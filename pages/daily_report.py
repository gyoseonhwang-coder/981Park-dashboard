import streamlit as st
import pandas as pd
import requests
import io
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from menu_ui import render_sidebar, get_current_user, AUTHORIZED_USERS

# ─────────────────────────────────────────────
# 🔐 접근 권한 확인
# ─────────────────────────────────────────────
email, name = get_current_user()
if email not in AUTHORIZED_USERS:
    st.error("🚫 접근 권한이 없습니다. (기술지원 전용 페이지)")
    st.stop()

# ─────────────────────────────────────────────
# 📄 페이지 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="📅 Daily 현황", layout="wide")
render_sidebar(active="Daily")

KST = ZoneInfo("Asia/Seoul")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI/export?format=csv&gid=389240943"


# ─────────────────────────────────────────────
# 📦 데이터 로드 함수
# ─────────────────────────────────────────────
def fetch_csv(url: str) -> pd.DataFrame:
    """Google Sheets CSV 안전 로드"""
    resp = requests.get(url, timeout=15)
    head = resp.text.strip()[:200].lower()
    if head.startswith("<"):
        raise RuntimeError("CSV 대신 HTML 응답 수신 — 공유 설정을 확인하세요.")
    resp.encoding = "utf-8"
    raw = resp.text
    first = raw.splitlines()[0] if raw else ""
    sep = ";" if first.count(";") > first.count(",") else ","
    df = pd.read_csv(io.StringIO(raw), sep=sep, engine="python")
    df.columns = df.columns.str.replace("\n", "", regex=False).str.strip()
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed", na=False)]
    return df


# ─────────────────────────────────────────────
# 🕓 날짜 파싱 함수
# ─────────────────────────────────────────────
def parse_jeju_date(val):
    """981파크 접수내용 날짜 파서"""
    if pd.isna(val):
        return pd.NaT
    s = str(val).strip().replace("오전", "AM").replace("오후", "PM")
    s = re.sub(r"\s*\.\s*", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    patterns = [
        "%Y-%m-%d %p %I:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%y-%m-%d",
        "%Y-%m-%d %I:%M:%S %p",
    ]
    for fmt in patterns:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    if re.fullmatch(r"\d+(\.\d+)?", s):
        try:
            return pd.to_datetime(float(s), unit="D", origin="1899-12-30")
        except Exception:
            pass
    return pd.to_datetime(s, errors="coerce")


# ─────────────────────────────────────────────
# 📊 상태 표준화
# ─────────────────────────────────────────────
def normalize_status(s):
    if pd.isna(s):
        return "미정의"
    sv = str(s).strip()
    if sv in ["점검중", "진행중", "처리중"]:
        return "점검중"
    if sv in ["접수중", "대기", "미조치"]:
        return "미조치(접수중)"
    if sv in ["완료", "운영중", "사용중지"]:
        return "완료"
    return sv


# ─────────────────────────────────────────────
# 📈 KPI 계산 함수
# ─────────────────────────────────────────────
def status_counts(frame: pd.DataFrame):
    total = len(frame)
    vc = frame["상태"].value_counts()
    prog = int(vc.get("점검중", 0))
    pend = int(vc.get("미조치(접수중)", 0))
    done = int(vc.get("완료", 0))
    rate = (done / total * 100) if total else 0.0
    return total, prog, pend, done, rate


# ─────────────────────────────────────────────
# 🎨 KPI 카드 렌더링
# ─────────────────────────────────────────────
def render_kpi(cards, columns=5):
    st.markdown(
        """
        <style>
        .kpi-card {
            padding:18px;
            border-radius:12px;
            border:1px solid rgba(255,255,255,0.08);
            background:rgba(0,0,0,0.03);
        }
        .kpi-title{font-size:14px;color:#7e8b9c;margin-bottom:6px;}
        .kpi-value{font-size:28px;font-weight:700;}
        .c-blue{color:#2c7be5;}
        .c-orange{color:#f59f00;}
        .c-red{color:#e03131;}
        .c-green{color:#2b8a3e;}
        .c-navy{color:#233142;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(columns)
    for (title, value, cls), col in zip(cards, cols):
        col.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">{title}</div>
              <div class="kpi-value {cls}">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────
# 📥 데이터 로드
# ─────────────────────────────────────────────
try:
    df = fetch_csv(SHEET_URL)
except Exception as e:
    st.error(f"❌ 접수내용 로드 실패: {e}")
    st.stop()

if "날짜" not in df.columns or "접수처리" not in df.columns:
    st.error("❌ 필수 컬럼(날짜, 접수처리)이 없습니다.")
    st.stop()

df["날짜"] = df["날짜"].apply(parse_jeju_date)
df["상태"] = df["접수처리"].apply(normalize_status)
df = df.dropna(subset=["날짜"]).copy()

# ─────────────────────────────────────────────
# 📅 금일 접수 현황
# ─────────────────────────────────────────────
st.title("📅 Daily 장애 접수 현황")

today_kst = datetime.now(tz=KST).date()
df_today = df[df["날짜"].dt.date == today_kst]
t_total, t_prog, t_pend, t_done, t_rate = status_counts(df_today)

render_kpi([
    ("금일 접수", f"{t_total}", "c-blue"),
    ("금일 점검중", f"{t_prog}", "c-orange"),
    ("금일 미조치(접수중)", f"{t_pend}", "c-red"),
    ("금일 완료", f"{t_done}", "c-green"),
    ("금일 완료율", f"{t_rate:0.1f}%", "c-navy"),
])

st.divider()

# ─────────────────────────────────────────────
# 🧾 금일 장애 목록
# ─────────────────────────────────────────────
st.subheader("🧾 금일 장애 접수 목록")
pending = df_today[df_today["상태"].isin(["미조치(접수중)", "점검중"])]
cols_show = [c for c in ["날짜", "포지션", "위치", "설비명", "장애내용", "상태", "점검자"] if c in pending.columns]

if not pending.empty:
    st.dataframe(
        pending.sort_values("날짜", ascending=False)[cols_show],
        use_container_width=True, height=320
    )
else:
    st.info("✅ 현재 미조치 또는 점검중 장애가 없습니다.")

st.caption("© 2025 981Park Technical Support Team — Daily Report (금일 현황)")
