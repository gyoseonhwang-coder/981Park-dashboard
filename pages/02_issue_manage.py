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

    # ✅ 날짜 변환 (문자열 그대로 표시)
    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].replace("", "—").fillna("—")

    return df


# ─────────────────────────────────────────────
# 📊 메인 UI
# ─────────────────────────────────────────────
st.title("🧰 981Park 장애 처리")

df = load_issue_log()
if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

# ✅ 필터 구성
col1, col2, col3 = st.columns([1.3, 1, 0.6])
with col1:
    positions = ["전체"] + sorted(df["포지션"].dropna().unique().tolist())
    selected_position = st.selectbox("📍 포지션", positions)
with col2:
    selected_status = st.selectbox("📋 상태", ["전체", "접수중", "점검중", "완료"])
with col3:
    refresh = st.button("🔄 새로고침")

# ✅ 필터 적용
filtered = df.copy()
if selected_position != "전체":
    filtered = filtered[filtered["포지션"] == selected_position]
if selected_status != "전체":
    filtered = filtered[filtered["접수처리"] == selected_status]

filtered = filtered.sort_values(
    by=df.columns[1], ascending=False, ignore_index=True)

# ✅ 표시 컬럼
cols_to_show = [
    "날짜", "작성자", "포지션", "위치",
    "설비명", "세부기기", "장애내용", "접수처리", "점검자"
]
filtered = filtered[[c for c in cols_to_show if c in filtered.columns]]

# ─────────────────────────────────────────────
# 📋 장애 목록 표시
# ─────────────────────────────────────────────
st.markdown("---")
st.subheader(f"📋 장애 목록 ({len(filtered)}건)")
st.caption("행을 선택한 후 아래의 [장애 접수] 버튼을 누르세요.")

# ✅ 선택 UI
selected_idx = st.number_input(
    "🔢 선택할 행 번호 입력 (0부터 시작)",
    min_value=0,
    max_value=len(filtered)-1 if len(filtered) > 0 else 0,
    step=1,
    value=0
)

# ✅ 표 표시 (클릭만, 선택은 입력으로)
st.dataframe(filtered, use_container_width=True, height=420)

# ─────────────────────────────────────────────
# 🧾 장애 접수 버튼 + 팝업 처리
# ─────────────────────────────────────────────
if st.button("🚧 장애 접수", use_container_width=True):
    if filtered.empty:
        st.warning("⚠️ 선택할 데이터가 없습니다.")
    else:
        issue = filtered.iloc[int(selected_idx)]

        with st.expander("⚙️ 장애 접수 처리", expanded=True):
            st.markdown(f"### ⚙️ {issue['설비명']} 장애 접수")
            st.markdown(
                f"""
                **📅 날짜:** {issue.get('날짜', '—')}  
                **📍 포지션:** {issue.get('포지션', '—')}  
                **🏗️ 위치:** {issue.get('위치', '—')}  
                **🧩 세부기기:** {issue.get('세부기기', '—')}  
                **📝 장애내용:** {issue.get('장애내용', '—')}  
                **📋 현재상태:** {issue.get('접수처리', '—')}
                """
            )

            st.markdown("---")

            # 입력 필드
            담당자 = st.text_input("👷 접수자 이름", "")
            포지션_이동 = st.selectbox(
                "📍 포지션 시트로 이동 (선택 안 함 가능)",
                ["선택 안 함", "Audio/Video", "RACE",
                    "LAB", "운영설비", "충전설비", "정비고", "기타"]
            )

            if st.button("✅ 접수 완료", use_container_width=True):
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
                        row_index = match.index[0] + 2  # header offset
                        ws.update_cell(row_index, 10, "점검중")     # J열: 접수처리
                        ws.update_cell(row_index, 12, 담당자)       # L열: 점검자
                        ws.update_cell(
                            row_index, 11, 포지션_이동 if 포지션_이동 != "선택 안 함" else "")
                        ws.update_cell(row_index, 15, "장애 등록")  # O열: 장애관리

                        st.success(f"✅ '{issue['설비명']}' 장애가 점검중으로 변경되었습니다.")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 접수 처리 중 오류 발생: {e}")

st.caption("© 2025 981Park Technical Support Team — 장애 처리 시스템")
