import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from menu_ui import render_sidebar
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ─────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="🧰 981Park 장애 처리", layout="wide")
render_sidebar(active="IssueManage")

# ─────────────────────────────────────────────
# Google 인증
# ─────────────────────────────────────────────
try:
    creds_info = st.secrets["google_service_account"]
except Exception:
    st.error("🔐 `st.secrets['google_service_account']` 항목이 없습니다.")
    st.stop()

creds = Credentials.from_service_account_info(
    creds_info,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)
gc = gspread.authorize(creds)

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_LOG = "접수내용"

# ─────────────────────────────────────────────
# 데이터 로드
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
        df["날짜"] = df["날짜"].apply(lambda x: x if x not in [
                                  None, "", " "] else "—")

    return df


# ─────────────────────────────────────────────
# 메인 UI
# ─────────────────────────────────────────────
st.title("🧰 981Park 장애 처리")
st.subheader("🧾 조치 필요 목록 (미조치/점검중)")

df = load_issue_log()
if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

# 상태 컬럼 표준화
if "접수처리" in df.columns:
    df["상태"] = df["접수처리"].replace({
        "접수중": "미조치(접수중)",
        "점검중": "점검중",
        "완료": "완료"
    })

pending = df[df["상태"].isin(["미조치(접수중)", "점검중"])].copy()
pending = pending.sort_values("날짜", ascending=False)

cols_show = [c for c in ["날짜", "포지션", "위치", "설비명",
                         "장애내용", "상태", "점검자"] if c in pending.columns]

if pending.empty:
    st.info("✅ 현재 조치가 필요한 장애가 없습니다.")
    st.stop()

# ─────────────────────────────────────────────
# AgGrid 테이블 표시 (행 클릭 가능)
# ─────────────────────────────────────────────
gb = GridOptionsBuilder.from_dataframe(pending[cols_show])
gb.configure_selection("single", use_checkbox=False)
gb.configure_grid_options(domLayout="normal")
gb.configure_default_column(resizable=True, wrapText=True, autoHeight=True)

# ✅ 더블클릭 이벤트 핸들러 추가
gb.configure_grid_options(onCellDoubleClicked={
    "function": """
        function(e) {
            window.dispatchEvent(new CustomEvent("aggrid_doubleclick", {detail: e.data}));
        }
    """
})

grid_options = gb.build()

st.caption("🔍 행을 더블클릭하면 상세 접수/처리 팝업이 열립니다.")

grid_response = AgGrid(
    pending[cols_show],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    fit_columns_on_grid_load=True,
    height=340,
    allow_unsafe_jscode=True  # ✅ JS 이벤트 허용
)

# ✅ JS → Streamlit 통신 (더블클릭 감지)
clicked_data = st.session_state.get("doubleclicked_row", None)

# ✅ 더블클릭 감지용 JS 이벤트 리스너 등록
st.components.v1.html(
    """
    <script>
    window.addEventListener("aggrid_doubleclick", (event) => {
        const data = JSON.stringify(event.detail);
        fetch("/_stcore/custom-component", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"type": "doubleclick", "data": data})
        });
    });
    </script>
    """,
    height=0,
)


# ─────────────────────────────────────────────
# 팝업용 스타일 정의
# ─────────────────────────────────────────────
st.markdown("""
<style>
.popup-overlay {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-color: rgba(0,0,0,0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999;
}
.popup-card {
    background-color: white;
    padding: 28px;
    border-radius: 12px;
    box-shadow: 0 6px 25px rgba(0,0,0,0.25);
    width: 480px;
    animation: fadeIn 0.25s ease-in-out;
    position: relative;
}
.popup-close {
    position: absolute;
    top: 10px; right: 15px;
    font-size: 20px;
    cursor: pointer;
    color: #444;
}
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(-10px);}
    to {opacity: 1; transform: translateY(0);}
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 팝업 표시 로직
# ─────────────────────────────────────────────
if "popup_issue" not in st.session_state:
    st.session_state.popup_issue = None

# ✅ selected 기본값 안전하게 초기화
selected = grid_response.get("selected_rows", [])

# ✅ 선택된 행 있을 경우 팝업 오픈
if isinstance(selected, list) and len(selected) > 0:
    st.session_state.popup_issue = selected[0]


if st.session_state.popup_issue:
    issue = st.session_state.popup_issue
    st.markdown(f"""
    <div class="popup-overlay" id="popup">
        <div class="popup-card">
            <div class="popup-close" onclick="document.getElementById('popup').style.display='none'">×</div>
            <h3>⚙️ 장애 처리 ({issue.get('상태', '-')})</h3>
            <hr>
            <p><b>📅 날짜:</b> {issue.get('날짜', '—')}</p>
            <p><b>📍 포지션:</b> {issue.get('포지션', '—')}</p>
            <p><b>🏗️ 위치:</b> {issue.get('위치', '—')}</p>
            <p><b>⚙️ 설비명:</b> {issue.get('설비명', '—')}</p>
            <p><b>🧩 장애내용:</b> {issue.get('장애내용', '—')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 👷 조치 내용 입력")

    담당자 = st.text_input("점검자 이름", issue.get("점검자", ""))
    포지션_이동 = st.selectbox(
        "포지션 시트로 이동 (선택 안 함 가능)",
        ["선택 안 함", "Audio/Video", "RACE",
         "LAB", "운영설비", "충전설비", "정비고", "기타"]
    )

    # 접수중 → 점검중
    if issue.get("상태") == "미조치(접수중)":
        if st.button("🚧 점검 시작 (접수중 → 점검중)", use_container_width=True):
            try:
                ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
                match = df[
                    (df["작성자"] == issue["작성자"]) &
                    (df["장애내용"] == issue["장애내용"]) &
                    (df["설비명"] == issue["설비명"])
                ]
                if match.empty:
                    st.error("⚠️ 시트에서 해당 장애를 찾을 수 없습니다.")
                else:
                    row_index = match.index[0] + 2
                    ws.update_cell(row_index, 10, "점검중")  # 접수처리
                    ws.update_cell(row_index, 12, 담당자)    # 점검자
                    ws.update_cell(
                        row_index, 11, 포지션_이동 if 포지션_이동 != "선택 안 함" else "")
                    ws.update_cell(row_index, 15, "장애 등록")
                    st.success(f"✅ '{issue['설비명']}' 장애가 점검중으로 변경되었습니다.")
                    st.session_state.popup_issue = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 점검 시작 중 오류: {e}")

    # 점검중 → 완료
    elif issue.get("상태") == "점검중":
        점검내용 = st.text_area("🧰 점검내용", "")
        if st.button("✅ 완료 처리 (점검중 → 완료)", use_container_width=True):
            try:
                ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
                match = df[
                    (df["작성자"] == issue["작성자"]) &
                    (df["장애내용"] == issue["장애내용"]) &
                    (df["설비명"] == issue["설비명"])
                ]
                if match.empty:
                    st.error("⚠️ 시트에서 해당 장애를 찾을 수 없습니다.")
                else:
                    row_index = match.index[0] + 2
                    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    ws.update_cell(row_index, 10, "완료")  # 접수처리
                    ws.update_cell(row_index, 13, now)     # 완료일자
                    ws.update_cell(row_index, 14, 점검내용)  # 점검내용
                    ws.update_cell(row_index, 15, "장애 처리")
                    ws.update_cell(row_index, 17, "종결")
                    st.success(f"✅ '{issue['설비명']}' 장애가 완료 처리되었습니다.")
                    st.session_state.popup_issue = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 완료 처리 중 오류: {e}")

st.caption("© 2025 981Park Technical Support Team — 장애 처리 시스템")
