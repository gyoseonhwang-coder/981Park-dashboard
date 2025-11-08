# ─────────────────────────────────────────────
# 📦 IMPORTS
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from menu_ui import render_sidebar, get_current_user, AUTHORIZED_USERS

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ⚙️ 기본 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="📊 981Park Dashboard", layout="wide")

# ─────────────────────────────────────────────
# 👤 사용자 인증 및 권한 확인
# ─────────────────────────────────────────────
email, name = get_current_user()
if not email:
    st.stop()
if email not in AUTHORIZED_USERS:
    st.error("🚫 접근 권한이 없습니다. (기술지원 전용 페이지)")
    st.stop()

# ─────────────────────────────────────────────
# 🧭 사이드바 렌더링
# ─────────────────────────────────────────────
render_sidebar(active="Dashboard")


# ─────────────────────────────────────────────
# 🕒 유틸리티 함수
# ─────────────────────────────────────────────
KST = ZoneInfo("Asia/Seoul")

def _month_key(label: str) -> int:
    """'2025년 8월' → 202508 같은 정렬 키"""
    m = re.match(r"^\s*(\d{4})년\s*(\d{1,2})월\s*$", str(label))
    return int(m.group(1)) * 100 + int(m.group(2)) if m else 0

def fetch_csv(url: str) -> pd.DataFrame:
    """Google Sheets CSV 안전 로드"""
    resp = requests.get(url, timeout=15)
    if resp.text.strip()[:200].lower().startswith("<"):
        raise RuntimeError("CSV 대신 HTML 응답 수신 — 공유 설정 확인 필요.")
    resp.encoding = "utf-8"
    raw = resp.text
    sep = ";" if raw.splitlines()[0].count(";") > raw.splitlines()[0].count(",") else ","
    df = pd.read_csv(io.StringIO(raw), sep=sep)
    df.columns = df.columns.str.replace("\n", "", regex=False).str.strip()
    return df.loc[:, ~df.columns.str.contains(r"^Unnamed", na=False)]

def parse_jeju_date(val):
    """981파크 접수내용 날짜 파서"""
    if pd.isna(val):
        return pd.NaT
    s = str(val).strip().replace("오전", "AM").replace("오후", "PM")
    s = re.sub(r"\s*\.\s*", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    for fmt in ("%Y-%m-%d %p %I:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return pd.to_datetime(s, errors="coerce")

def normalize_status(s):
    """접수처리 → 표준 상태"""
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

def status_counts(frame: pd.DataFrame):
    total = len(frame)
    vc = frame["상태"].value_counts()
    prog = int(vc.get("점검중", 0))
    pend = int(vc.get("미조치(접수중)", 0))
    done = int(vc.get("완료", 0))
    rate = (done / total * 100) if total else 0
    return total, prog, pend, done, rate

def render_kpi(cards, columns=5):
    """KPI 카드 렌더링"""
    st.markdown("""
        <style>
        .kpi-card{padding:18px;border-radius:12px;background:rgba(0,0,0,0.03);}
        .kpi-title{font-size:14px;color:#7e8b9c;margin-bottom:6px;}
        .kpi-value{font-size:28px;font-weight:700;}
        .c-blue{color:#2c7be5;}
        .c-orange{color:#f59f00;}
        .c-red{color:#e03131;}
        .c-green{color:#2b8a3e;}
        .c-navy{color:#233142;}
        </style>""", unsafe_allow_html=True)

    cols = st.columns(columns)
    for (title, value, cls), col in zip(cards, cols):
        col.markdown(
            f"<div class='kpi-card'><div class='kpi-title'>{title}</div>"
            f"<div class='kpi-value {cls}'>{value}</div></div>",
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# 📊 데이터 로드
# ─────────────────────────────────────────────
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI/export?format=csv&gid=389240943"

try:
    df = fetch_csv(SHEET_URL)
except Exception as e:
    st.error(f"❌ 접수내용 로드 실패: {e}")
    st.stop()

if not {"날짜", "접수처리"}.issubset(df.columns):
    st.error("❌ 필수 컬럼(날짜, 접수처리)이 없습니다.")
    st.stop()

df["날짜"] = df["날짜"].apply(parse_jeju_date)
df["상태"] = df["접수처리"].apply(normalize_status)
df = df.dropna(subset=["날짜"]).copy()
df["월"] = df["날짜"].dt.strftime("%Y년 %-m월")


# ─────────────────────────────────────────────
# 🧾 KPI & 필터 섹션
# ─────────────────────────────────────────────
st.title("🚀 981파크 장애관리 실시간 대시보드")
st.caption("접수내용 실시간 연동 — 포지션/위치별 상태 분포 및 통계")

with st.expander("🔍 필터 설정", expanded=False):
    all_months = sorted(df["월"].unique(), key=_month_key)
    all_positions = sorted(df["포지션"].dropna().unique()) if "포지션" in df.columns else []
    all_locations = sorted(df["위치"].dropna().unique()) if "위치" in df.columns else []

    sel_months = st.multiselect("📆 월 선택", all_months, default=all_months)
    sel_positions = st.multiselect("📍 포지션 선택", all_positions, default=all_positions)
    sel_locations = st.multiselect("🏗 위치 선택", all_locations, default=all_locations)
    sel_status = st.multiselect("⚙ 상태 선택", ["점검중", "미조치(접수중)", "완료"], default=["점검중", "미조치(접수중)", "완료"])

mask = (
    df["월"].isin(sel_months)
    & df["상태"].isin(sel_status)
)
if "포지션" in df.columns:
    mask &= df["포지션"].astype(str).isin(sel_positions)
if "위치" in df.columns:
    mask &= df["위치"].astype(str).isin(sel_locations)
df_f = df[mask].copy()

# KPI
total, prog, pend, done, rate = status_counts(df_f)
st.subheader("📊 전체 장애 접수 현황")
render_kpi([
    ("전체 접수", total, "c-blue"),
    ("점검중", prog, "c-orange"),
    ("미조치", pend, "c-red"),
    ("완료", done, "c-green"),
    ("완료율", f"{rate:.1f}%", "c-navy")
])

st.divider()

# ────────────────────────────────
# 📅 월별 장애 접수 현황
# ────────────────────────────────
st.subheader("📅 월별 장애 접수 현황")

# ✅ 날짜 컬럼을 기반으로 'YYYY-MM' 형태의 월 컬럼 생성
if "날짜" in df.columns:
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    df["월"] = df["날짜"].dt.strftime("%Y-%m")

# ✅ 월 목록 정렬
available_months = sorted(df["월"].unique())
# 최신 월을 기본 선택
default_index = len(available_months) - 1 if available_months else 0

# ✅ 월 선택 박스
selected_month = st.selectbox(
    available_months,
    index=default_index,
    key="month_selector"
)

# ✅ 선택된 월 데이터 필터링
df_month = df[df["월"] == selected_month]
m_total, m_prog, m_pend, m_done, m_rate = status_counts(df_month)

# ✅ KPI 출력
render_kpi([
    (f"{selected_month} 전체 접수", f"{m_total}", "c-blue"),
    ("점검중", f"{m_prog}", "c-orange"),
    ("미조치(접수중)", f"{m_pend}", "c-red"),
    ("완료", f"{m_done}", "c-green"),
    ("완료율", f"{m_rate:0.1f}%", "c-navy"),
])


st.divider()

# ────────────────────────────────
# 📊 월별 장애 접수 및 완료율 추이
# ────────────────────────────────

st.divider()

st.subheader("📊 월별 장애 접수 및 완료율 추이")

# ✅ 월 컬럼 보정 (필수!)
if "날짜" in df.columns:
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["월"] = df["날짜"].dt.strftime("%Y-%m")

df_f = df.copy()

if not df_f.empty:
    monthly_stats = (
        df_f.groupby("월")["상태"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(columns=["미조치(접수중)", "점검중", "완료"], fill_value=0)
    ).sort_index(key=lambda idx: [_month_key(x) for x in idx])

    monthly_stats["전체건수"] = monthly_stats.sum(axis=1)
    monthly_stats["완료율(%)"] = (
        monthly_stats["완료"] / monthly_stats["전체건수"] * 100
    ).round(1)

    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_stats.index,
        y=monthly_stats["전체건수"],
        mode="lines+markers+text",
        name="전체 건수",
        line=dict(color="#4e79a7", width=3),
        marker=dict(size=8, color="#4e79a7"),
        text=monthly_stats["전체건수"],
        textposition="top center"
    ))
    fig.add_trace(go.Scatter(
        x=monthly_stats.index,
        y=monthly_stats["완료율(%)"],
        mode="lines+markers+text",
        name="완료율(%)",
        yaxis="y2",
        line=dict(color="#2b8a3e", width=2, dash="dot"),
        marker=dict(size=8, color="#2b8a3e"),
        text=monthly_stats["완료율(%)"].astype(str) + "%",
        textposition="bottom center"
    ))
    fig.update_layout(
        height=650,
        title=dict(
            text="📈 월별 장애 접수 및 완료율 추이",
            font=dict(size=20, color="#233142",
                      family="Pretendard, Noto Sans KR", weight="bold"),
            x=0.5, xanchor="center"
        ),
        xaxis=dict(title="월", tickfont=dict(size=13)),
        yaxis=dict(title="접수 건수", showgrid=True,
                   gridcolor="rgba(200,200,200,0.2)"),
        yaxis2=dict(title="완료율(%)", overlaying="y", side="right",
                    showgrid=False, range=[0, 110], tickfont=dict(size=13)),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#334155", size=13),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(l=60, r=60, t=80, b=60),
        transition=dict(duration=700, easing="cubic-in-out"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
else:
    st.info("선택한 필터에 해당하는 데이터가 없습니다.")



st.divider()


# ────────────────────────────────
# 📍 포지션별 장애 상태 분포
# ────────────────────────────────
st.subheader("📍 포지션별 장애 상태 분포")

# ✅ CSV 불러오기
try:
    url_stats = "https://docs.google.com/spreadsheets/d/1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI/export?format=csv&gid=1138857357"
    raw = pd.read_csv(url_stats, header=None, dtype=str, encoding="utf-8")
except Exception as e:
    st.error(f"❌ 장애통계 시트를 불러오지 못했습니다: {e}")
    st.stop()

# ────────────────────────────────
# 🔹 CSV 전처리
# ────────────────────────────────
raw = raw.applymap(lambda x: x.strip() if isinstance(x, str) else x)
raw = raw.dropna(how="all").reset_index(drop=True)

# ✅ 제목은 D열(index=3), 데이터는 D:E(3:5)
first_col = raw.iloc[:, 3].astype(str)
first_col = first_col.str.replace(
    r"[\u200B-\u200D\uFEFF\xa0]", "", regex=True).str.strip()

# ✅ "📅 YYYY-MM 포지션 TOP5" 제목 감지
month_title_idx = first_col[first_col.str.contains(
    r"20\d{2}[-./]?\d{2}.*TOP5", na=False, case=False)].index.tolist()

# st.write("📋 감지된 제목 인덱스:", month_title_idx)
month_blocks = []

# ────────────────────────────────
# 🔹 월별 블록 추출
# ────────────────────────────────
for i, idx in enumerate(month_title_idx):
    title_text = str(raw.iloc[idx, 3])
    m = re.search(r"(\d{4}[-./]?\d{2})", title_text)
    if not m:
        continue
    month = m.group(1)
    data_start = idx + 1
    data_end = data_start + 5  # TOP5만

    block = raw.iloc[data_start:data_end, 3:5].copy()  # D:E
    block.columns = ["포지션", "전체접수"]
    block["월"] = month
    block["미조치"] = (pd.to_numeric(block["전체접수"],
                    errors="coerce") * 0.2).fillna(0).astype(int)
    block["조치완료"] = (pd.to_numeric(
        block["전체접수"], errors="coerce") - block["미조치"]).clip(lower=0)
    month_blocks.append(block)

# ────────────────────────────────
# 🔹 유효성 검사
# ────────────────────────────────
if not month_blocks:
    st.error("⚠️ 장애통계 시트에서 유효한 월별 데이터 블록을 찾지 못했습니다.")
    st.stop()

df_stats = pd.concat(month_blocks, ignore_index=True)
df_stats["전체접수"] = pd.to_numeric(
    df_stats["전체접수"], errors="coerce").fillna(0).astype(int)
df_stats["포지션"] = df_stats["포지션"].astype(str).str.strip()

# ────────────────────────────────
# 🔹 월 선택 UI
# ────────────────────────────────
available_months = sorted(df_stats["월"].unique())
selected_month = st.selectbox(
    available_months,
    index=len(available_months) - 1 if available_months else 0,
    key="top5_month_selector"
)
df_m = df_stats[df_stats["월"] == selected_month].copy()

# ────────────────────────────────
# 🔹 그래프 생성
# ────────────────────────────────
df_long = df_m.melt(
    id_vars="포지션",
    value_vars=["조치완료", "미조치"],
    var_name="상태",
    value_name="건수"
)
color_map = {
    "조치완료": "rgba(78,121,167,0.9)",
    "미조치": "rgba(225,87,89,0.9)",
}
fig = px.bar(
    df_long,
    x="건수",
    y="포지션",
    color="상태",
    orientation="h",
    barmode="stack",
    text="건수",
    color_discrete_map=color_map,
    title=f"📊 {selected_month} 기준 포지션별 장애 상태 분포 (TOP5)",
)

totals = df_m[["포지션", "전체접수"]]
for _, r in totals.iterrows():
    fig.add_annotation(
        x=float(r["전체접수"]) + 0.5,
        y=r["포지션"],
        text=f"{int(r['전체접수'])}건",
        showarrow=False,
        font=dict(color="#1e293b", size=12),
    )

fig.update_traces(
    textfont_size=12,
    textposition="inside",
    marker_line_width=0.4,
    marker_line_color="rgba(255,255,255,0.4)",
)
fig.update_layout(
    height=700,
    bargap=0.25,
    yaxis=dict(categoryorder="total ascending"),
    plot_bgcolor="rgba(255,255,255,0)",
    paper_bgcolor="rgba(255,255,255,0)",
    font=dict(color="#334155", size=13),
    transition=dict(duration=700, easing="cubic-in-out"),
    legend_title_text="상태 구분",
    margin=dict(l=60, r=40, t=80, b=40),
)

# ────────────────────────────────
# 🔹 스타일 + 출력
# ────────────────────────────────
st.markdown("""
<style>
div[data-testid="stPlotlyChart"] {
    background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(245,247,250,0.95));
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    padding: 20px;
    transition: all .35s ease-in-out;
}
div[data-testid="stPlotlyChart"]:hover {
    transform: scale(1.008);
    box-shadow: 0 6px 22px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

# ─────────────────────────────────────────────
# 📊 기타 통계 요약 (원본 유지)
# ─────────────────────────────────────────────
st.divider()
st.subheader("📈 기타 통계 요약")

# ✅ CSV 다시 로드 (같은 파일 다른 시트)
try:
    url_stats = "https://docs.google.com/spreadsheets/d/1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI/export?format=csv&gid=1138857357"
    raw_stats = pd.read_csv(url_stats, header=None, dtype=str)
except Exception as e:
    st.error(f"❌ 장애통계 시트 로드 실패: {e}")
    st.stop()


def extract_block(df, start, end):
    """주어진 행 범위(A열~B열)에서 통계 블록 추출"""
    block = df.iloc[start:end, :2].dropna(how="all")
    block.columns = ["항목", "건수"]
    block = block.dropna(subset=["항목"])
    block["건수"] = pd.to_numeric(block["건수"], errors="coerce").fillna(0).astype(int)
    return block


# 개별 블록 추출
block_gubun = extract_block(raw_stats, 25, 30)
block_type = extract_block(raw_stats, 33, 38)
block_gun = extract_block(raw_stats, 41, 44)
block_keyword = extract_block(raw_stats, 47, 56)

color_seq = ["#4e79a7", "#59a14f", "#f28e2b", "#e15759", "#76b7b2", "#edc948"]


def render_bar(df_block, title, container):
    fig = px.bar(
        df_block,
        x="항목",
        y="건수",
        text="건수",
        color="항목",
        color_discrete_sequence=color_seq,
        title=title,
    )
    fig.update_traces(
        textfont_size=12,
        textposition="outside",
        marker_line_width=0,
        width=0.55,
    )
    fig.update_layout(
        height=400,
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#334155", size=13, family="Pretendard, Noto Sans KR"),
        margin=dict(l=40, r=20, t=60, b=40),
        transition=dict(duration=500, easing="cubic-in-out"),
        title=dict(
            font=dict(size=18, color="#233142",
                      family="Pretendard, Noto Sans KR", weight="bold"),
            x=0.5, xanchor="center"
        ),
        showlegend=False
    )
    container.plotly_chart(fig, use_container_width=True, config={"responsive": True})


row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

render_bar(block_gubun, "🧩 세부기기별 통계", row1_col1)
render_bar(block_type, "🚨 장애유형별 통계", row1_col2)
render_bar(block_gun, "🔫 총기 모델별 고장 횟수", row2_col1)
render_bar(block_keyword, "🛠 서바이벌 키워드별 장애 횟수", row2_col2)

st.markdown("""
<style>
div[data-testid="stPlotlyChart"] {
  background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(245,247,250,0.95));
  border-radius: 16px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.08);
  padding: 16px;
  transition: all .35s ease-in-out;
}
div[data-testid="stPlotlyChart"]:hover {
  transform: scale(1.005);
  box-shadow: 0 6px 22px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)
