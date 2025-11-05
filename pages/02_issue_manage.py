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

    # ✅ 날짜 공백 보정
    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].apply(lambda x: x if str(x).strip() != "" else "—")

    # ✅ 중복 컬럼명 자동 정리 (빈 이름 포함)
    df.columns = [
        c if str(c).strip() != "" else f"Unnamed_{i}"
        for i, c in enumerate(df.columns)
    ]

    # ✅ 동일 이름 중복 고유화 (pandas 2.x 완전 호환)
    def make_unique_columns(columns):
        seen = {}
        new_cols = []
        for col in columns:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}.{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)
        return new_cols

    df.columns = make_unique_columns(df.columns)

    return df

# ─────────────────────────────────────────────
# 메인 UI
# ─────────────────────────────────────────────
st.title("🧰 981Park 장애 처리")

# ✅ Session State 초기화 (이게 꼭 필요)
if "popup_issue" not in st.session_state:
    st.session_state.popup_issue = None

if "selected_issue" not in st.session_state:
    st.session_state.selected_issue = None

st.subheader("🧾 조치 필요 목록 (미조치/점검중)")

df = load_issue_log()
if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

# ✅ 상태 컬럼 표준화 (더 안전하게)
if "상태" not in df.columns and "접수처리" in df.columns:
    df["상태"] = df["접수처리"].replace({
        "접수중": "미조치(접수중)",
        "점검중": "점검중",
        "완료": "완료"
    })
elif "상태" in df.columns:
    df["상태"] = df["상태"].replace({
        "접수중": "미조치(접수중)",
        "점검중": "점검중",
        "완료": "완료"
    })


pending = df[df["상태"].isin(["미조치(접수중)", "점검중"])].copy()
pending = pending.sort_values("날짜", ascending=False)

st.write("🧩 [DEBUG] df.shape:", df.shape)
st.write("🧩 [DEBUG] pending.shape:", pending.shape)
st.write("🧩 [DEBUG] df.columns:", df.columns.tolist())

cols_show = [c for c in ["날짜", "포지션", "위치", "설비명",
                         "장애내용", "상태", "점검자"] if c in pending.columns]

if pending.empty:
    st.warning("⚠️ pending이 비어 있습니다. ‘상태’ 컬럼 또는 ‘접수처리’ 컬럼 확인 필요.")
    st.stop()


# ─────────────────────────────────────────────
# AgGrid 테이블 표시 (행 클릭 + 더블클릭)
# ─────────────────────────────────────────────
gb = GridOptionsBuilder.from_dataframe(pending[cols_show])
gb.configure_selection("single", use_checkbox=True)
gb.configure_grid_options(
    onCellDoubleClicked={
        "function": """
            function(e) {
                window.dispatchEvent(
                    new CustomEvent("aggrid_doubleclick", {detail: e.data})
                );
            }
        """
    }
)
gb.configure_pagination(paginationAutoPageSize=True)
grid_options = gb.build()

grid_response = AgGrid(
    pending,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.MODEL_CHANGED,
    enable_enterprise_modules=False,
    theme="balham",
    height=340,
    fit_columns_on_grid_load=True,
)


st.caption("🔍 행을 더블클릭하면 상세 접수/처리 팝업이 열립니다.")

# ✅ 선택된 행 처리 (안전 버전)
selected_rows = grid_response.get("selected_rows", [])

if isinstance(selected_rows, list) and len(selected_rows) > 0:
    st.session_state.selected_issue = selected_rows[0]
    st.session_state.popup_issue = selected_rows[0]
else:
    st.session_state.selected_issue = None

# ─────────────────────────────────────────────
# 팝업 스타일 (오버레이 카드)
# ─────────────────────────────────────────────
st.markdown("""
<style>
.popup-overlay {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-color: rgba(0,0,0,0.55);
    display: flex; align-items: center; justify-content: center;
    z-index: 9999;
}
.popup-card {
    background-color: white;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 6px 25px rgba(0,0,0,0.3);
    width: 480px;
    animation: fadeIn 0.3s ease-in-out;
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
# 팝업 표시 및 처리 로직
# ─────────────────────────────────────────────
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
                    st.error("⚠️ 해당 장애를 시트에서 찾을 수 없습니다.")
                else:
                    row_index = match.index[0] + 2
                    ws.update_cell(row_index, 10, "점검중")
                    ws.update_cell(row_index, 12, 담당자)
                    ws.update_cell(
                        row_index, 11, 포지션_이동 if 포지션_이동 != "선택 안 함" else "")
                    ws.update_cell(row_index, 15, "장애 등록")

                    st.success(f"✅ '{issue['설비명']}' 장애가 점검중으로 변경되었습니다.")
                    st.session_state.popup_issue = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 접수 처리 중 오류 발생: {e}")

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
                    ws.update_cell(row_index, 10, "완료")
                    ws.update_cell(row_index, 13, now)
                    ws.update_cell(row_index, 14, 점검내용)
                    ws.update_cell(row_index, 15, "장애 처리")
                    ws.update_cell(row_index, 17, "종결")

                    st.success(f"✅ '{issue['설비명']}' 장애가 완료 처리되었습니다.")
                    st.session_state.popup_issue = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 완료 처리 중 오류: {e}")

st.caption("© 2025 981Park Technical Support Team — 장애 처리 시스템")
