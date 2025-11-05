# pages/02_issue_manage.py
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from menu_ui import render_sidebar

# ─────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="🧰 981Park 장애 처리", layout="wide")
render_sidebar(active="IssueManage")

# ─────────────────────────────────────────────
# Google 인증 (secrets.toml 기반)
# ─────────────────────────────────────────────
try:
    creds_info = st.secrets["google_service_account"]
except Exception:
    st.error("🔐 `st.secrets['google_service_account']` 항목이 없습니다.")
    st.stop()

creds = Credentials.from_service_account_info(
    creds_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]
)
gc = gspread.authorize(creds)

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_LOG = "접수내용"

# ─────────────────────────────────────────────
# 접수내용 시트 데이터 로드
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# 📋 데이터 로드
# ─────────────────────────────────────────────


@st.cache_data(ttl=30)
def load_issue_log() -> pd.DataFrame:
    """981파크 장애관리 > 접수내용 시트 전체 로드"""
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()

    if not data or len(data) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(data[1:], columns=data[0])
    if "날짜" in df.columns:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    return df


# ─────────────────────────────────────────────
# 📊 메인 UI
# ─────────────────────────────────────────────
st.title("🧰 981Park 장애 처리")

df = load_issue_log()
if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

# 필터 구성
col1, col2, col3 = st.columns([1.3, 1, 0.6])
with col1:
    positions = ["전체"] + sorted(df["포지션"].dropna().unique().tolist())
    selected_position = st.selectbox("📍 포지션", positions)
with col2:
    selected_status = st.selectbox("📋 상태", ["전체", "접수중", "점검중", "완료"])
with col3:
    refresh = st.button("🔄 새로고침")

# 필터 적용
filtered = df.copy()
if selected_position != "전체":
    filtered = filtered[filtered["포지션"] == selected_position]
if selected_status != "전체":
    filtered = filtered[filtered["접수처리"] == selected_status]

filtered = filtered.sort_values("날짜", ascending=False)

# 표시 컬럼
cols_to_show = ["날짜", "작성자", "포지션", "위치", "설비명", "세부기기", "장애내용", "접수처리", "점검자"]
filtered = filtered[[c for c in cols_to_show if c in filtered.columns]]

st.markdown("---")
st.subheader(f"📋 장애 목록 ({len(filtered)}건)")
st.caption("원하는 행을 클릭하면 상세 접수창이 팝업됩니다.")

# ─────────────────────────────────────────────
# 📋 인터랙티브 목록 (data_editor 기반)
# ─────────────────────────────────────────────
selected_issue = st.data_editor(
    filtered,
    hide_index=True,
    use_container_width=True,
    disabled=True,
    key="issue_table",
)

# ─────────────────────────────────────────────
# 🧾 팝업 — 장애 접수 처리
# ─────────────────────────────────────────────
if not filtered.empty:
    selected_index = st.session_state.get("issue_table", None)
    if selected_index:
        try:
            issue = filtered.iloc[selected_index["edited_rows"].keys()[
                0]]  # 첫 번째 클릭한 행

            with st.modal("🧾 장애 접수 처리"):
                st.markdown(f"### ⚙️ {issue['설비명']} 장애 접수")
                st.markdown(
                    f"""
                    **📅 날짜:** {issue.get('날짜', '')}  
                    **📍 포지션:** {issue.get('포지션', '')}  
                    **🏗️ 위치:** {issue.get('위치', '')}  
                    **🧩 세부기기:** {issue.get('세부기기', '')}  
                    **📝 장애내용:** {issue.get('장애내용', '')}
                    """
                )

                st.markdown("---")
                담당자 = st.text_input("👷 점검자 이름", issue.get("점검자", ""))
                if st.button("🚧 접수하기 (점검중으로 전환)", use_container_width=True):
                    try:
                        ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)

                        match = df[
                            (df["작성자"] == issue["작성자"]) &
                            (df["장애내용"] == issue["장애내용"]) &
                            (df["설비명"] == issue["설비명"])
                        ]
                        if match.empty:
                            st.error("⚠️ 해당 장애를 시트에서 찾을 수 없습니다.")
                        else:
                            row_index = match.index[0] + 2
                            ws.update_cell(row_index, 10, "점검중")  # J열: 접수처리
                            ws.update_cell(row_index, 12, 담당자)    # L열: 점검자
                            ws.update_cell(row_index, 15, "장애 등록")  # O열: 장애관리
                            st.success("✅ 장애가 점검중 상태로 변경되었습니다.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ 접수 처리 중 오류: {e}")

        except Exception:
            pass

st.caption("© 2025 981Park Technical Support Team — 장애 처리 시스템")
