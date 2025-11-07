# ─────────────────────────────────────────────
# 📦 Imports
# ─────────────────────────────────────────────
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
from menu_ui import render_sidebar, get_current_user, AUTHORIZED_USERS

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ⚙️ Page Setup & Auth
# ─────────────────────────────────────────────
st.set_page_config(page_title="🧰 장애 처리", layout="wide")
render_sidebar(active="IssueManage")

email, name = get_current_user()
if email not in AUTHORIZED_USERS:
    st.error("🚫 접근 권한이 없습니다. (기술지원 전용 페이지)")
    st.stop()


# ─────────────────────────────────────────────
# 🔐 Google 인증
# ─────────────────────────────────────────────
try:
    creds_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    gc = gspread.authorize(creds)
except Exception:
    st.error("🔐 Google 서비스 계정 정보가 누락되었습니다. `.streamlit/secrets.toml`을 확인하세요.")
    st.stop()

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_LOG = "접수내용"


# ─────────────────────────────────────────────
# 📘 데이터 로드
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_issue_log() -> pd.DataFrame:
    """981파크 장애관리 > 접수내용 시트 전체 로드"""
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(data[1:], columns=data[0])

    # 날짜 정리
    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].replace("", "—")

    # 상태 표준화
    if "상태" not in df.columns and "접수처리" in df.columns:
        df["상태"] = df["접수처리"]
    df["상태"] = df["상태"].replace({
        "접수중": "미조치(접수중)",
        "점검중": "점검중",
        "완료": "완료"
    })
    return df


# ─────────────────────────────────────────────
# 🧾 메인 UI
# ─────────────────────────────────────────────
st.title("🧰 981Park 장애 처리")
st.caption(f"접속 계정: {email}")
st.divider()

df = load_issue_log()
if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

pending = df[df["상태"].isin(["미조치(접수중)", "점검중"])].copy()
pending = pending.sort_values("날짜", ascending=False)

cols_show = [c for c in ["날짜", "포지션", "위치", "설비명", "장애내용", "상태", "점검자"] if c in pending.columns]
st.dataframe(pending[cols_show], use_container_width=True, height=320)

st.divider()

# ─────────────────────────────────────────────
# 🎯 처리할 장애 선택
# ─────────────────────────────────────────────
st.markdown("""
<style>
div[data-baseweb="select"] span {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    line-height: 1.5em !important;
}
div.stSelectbox > label > div {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #222 !important;
    margin-bottom: 6px !important;
}
</style>
""", unsafe_allow_html=True)

row_labels = [f"[{r['상태']}] {r['설비명']} — {r['장애내용']}" for _, r in pending.iterrows()]
selected_label = st.selectbox("📋 처리할 장애 선택", ["선택 안 함"] + row_labels, index=0)

if selected_label == "선택 안 함":
    st.info("📋 위 목록에서 처리할 장애를 선택하세요.")
    st.stop()

selected_index = row_labels.index(selected_label)
issue = pending.iloc[selected_index]

st.markdown("---")
st.markdown(
    f"### 🧩 선택된 장애 — <span style='color:#16a34a;font-weight:600'>{issue.get('포지션', '-')} {issue.get('설비명', '-')}</span>",
    unsafe_allow_html=True
)

# 카드형 UI
st.markdown("""
<style>
.issue-card {
    background-color: #ffffff;
    border-radius: 10px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    padding: 20px;
    margin-top: 10px;
    border-left: 6px solid #2E86DE;
}
.issue-card b { color: #111; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="issue-card">
    <b>📅 날짜:</b> {issue.get('날짜', '—')}<br>
    <b>📍 포지션:</b> {issue.get('포지션', '—')}<br>
    <b>🏗️ 위치:</b> {issue.get('위치', '—')}<br>
    <b>⚙️ 설비명:</b> {issue.get('설비명', '—')}<br>
    <b>🧩 장애내용:</b> {issue.get('장애내용', '—')}<br>
    <b>📋 현재상태:</b> {issue.get('상태', '—')}
</div>
""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────
# 👷 조치 입력 & 상태 변경
# ─────────────────────────────────────────────
st.markdown("### 👷 조치 내용 입력")

담당자 = st.text_input("👷 점검자 이름", issue.get("점검자", ""))
포지션_이동 = st.selectbox(
    "📍 포지션 시트로 이동 (선택 안 함 가능)",
    ["선택 안 함", "Audio/Video", "RACE", "LAB", "운영설비", "충전설비", "정비고", "기타"]
)

# 시트 참조 준비
ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
match = df[
    (df["작성자"] == issue.get("작성자")) &
    (df["장애내용"] == issue.get("장애내용")) &
    (df["설비명"] == issue.get("설비명"))
]

if match.empty:
    st.error("⚠️ 해당 장애를 시트에서 찾을 수 없습니다.")
    st.stop()

row_index = match.index[0] + 2  # 헤더 포함 offset

# ─────────────────────────────────────────────
# 🚧 접수중 → 점검중
# ─────────────────────────────────────────────
if issue.get("상태") == "미조치(접수중)":
    st.info("📩 아직 조치되지 않은 장애입니다. 점검 시작 시 아래 버튼을 클릭하세요.")
    if st.button("🚧 장애 접수 (→ 점검중)", use_container_width=True):
        try:
            ws.update_cell(row_index, 10, "점검중")  # 접수처리
            ws.update_cell(row_index, 12, 담당자)    # 점검자
            ws.update_cell(row_index, 11, 포지션_이동 if 포지션_이동 != "선택 안 함" else "")
            ws.update_cell(row_index, 15, "장애 등록")

            st.toast(f"✅ '{issue['설비명']}' 장애가 점검중으로 변경되었습니다.", icon="⚙️")
            with st.spinner("🔄 시트 업데이트 중..."):
                import time
                time.sleep(1.5)
            st.rerun()
        except Exception as e:
            st.error(f"❌ 장애 접수 중 오류 발생: {e}")

# ─────────────────────────────────────────────
# 🧰 점검중 → 완료
# ─────────────────────────────────────────────
elif issue.get("상태") == "점검중":
    st.info("🧰 점검이 완료되면 아래 내용을 입력 후 완료 처리하세요.")
    점검내용 = st.text_area("🔧 점검내용", height=120, placeholder="점검 결과나 조치 내용을 입력하세요.")
    if st.button("✅ 완료 처리 (→ 완료)", use_container_width=True):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.update_cell(row_index, 10, "완료")
            ws.update_cell(row_index, 13, now)
            ws.update_cell(row_index, 14, 점검내용)
            ws.update_cell(row_index, 15, "장애 처리")
            ws.update_cell(row_index, 17, "종결")

            st.toast(f"🎉 '{issue['설비명']}' 장애가 완료 처리되었습니다.", icon="✅")
            with st.spinner("💾 변경 내용 저장 중..."):
                import time
                time.sleep(1.5)
            st.rerun()
        except Exception as e:
            st.error(f"❌ 완료 처리 중 오류: {e}")

else:
    st.info("✅ 이 장애는 이미 완료 상태입니다.")

st.caption("© 2025 981Park Technical Support Team — 기술지원 전용 장애 처리 시스템")
