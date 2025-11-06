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

    # 날짜 및 공백 처리
    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].apply(lambda x: x if str(x).strip() != "" else "—")

    # 중복 컬럼명 정리
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

    df.columns = [
        c if str(c).strip() != "" else f"Unnamed_{i}"
        for i, c in enumerate(df.columns)
    ]
    df.columns = make_unique_columns(df.columns)
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
if "상태" not in df.columns and "접수처리" in df.columns:
    df["상태"] = df["접수처리"].replace({
        "접수중": "미조치(접수중)",
        "점검중": "점검중",
        "완료": "완료"
    })

# 조치 필요 목록
pending = df[df["상태"].isin(["미조치(접수중)", "점검중"])].copy()
pending = pending.sort_values("날짜", ascending=False)

cols_show = [c for c in ["날짜", "포지션", "위치", "설비명",
                         "장애내용", "상태", "점검자"] if c in pending.columns]

if pending.empty:
    st.info("✅ 현재 조치가 필요한 장애가 없습니다.")
    st.stop()

# ─────────────────────────────────────────────
# AgGrid 표시 (체크박스 선택 시 자동 rerun)
# ─────────────────────────────────────────────
grid_data = pending[cols_show].copy()

gb = GridOptionsBuilder.from_dataframe(grid_data)
gb.configure_selection(selection_mode="single", use_checkbox=True)
gb.configure_pagination(paginationAutoPageSize=True)
grid_options = gb.build()

st.caption("☑️ 장애를 선택하면 아래에 상세 카드가 표시됩니다.")

# ✅ AgGrid 출력 (selection + manual rerun 유도)
grid_response = AgGrid(
    grid_data,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    enable_enterprise_modules=False,
    theme="balham",
    height=340,
    fit_columns_on_grid_load=True,
    key="issue_grid"
)

# ✅ 선택된 행 감지
selected_rows = grid_response["selected_rows"]

# ✅ 선택된 행이 있을 때 바로 rerun (명시적 트리거)
if selected_rows:
    st.session_state["selected_issue"] = selected_rows[0]
else:
    st.session_state["selected_issue"] = None

# ─────────────────────────────────────────────
# 선택된 장애 상세 카드 표시
# ─────────────────────────────────────────────
if st.session_state["selected_issue"] is not None:
    issue = st.session_state["selected_issue"]

    st.markdown("---")
    st.markdown(f"### 🧩 선택된 장애 — `{issue.get('설비명', '-')}`")

    # 카드 스타일
    st.markdown("""
    <style>
    .card {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        padding: 20px;
        margin-top: 10px;
        border-left: 6px solid #2E86DE;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <b>📅 날짜:</b> {issue.get('날짜', '—')}<br>
        <b>📍 포지션:</b> {issue.get('포지션', '—')}<br>
        <b>🏗️ 위치:</b> {issue.get('위치', '—')}<br>
        <b>⚙️ 설비명:</b> {issue.get('설비명', '—')}<br>
        <b>🧩 장애내용:</b> {issue.get('장애내용', '—')}<br>
        <b>📋 현재상태:</b> {issue.get('상태', '—')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👷 조치 내용 입력")
    담당자 = st.text_input("👷 점검자 이름", issue.get("점검자", ""))
    포지션_이동 = st.selectbox(
        "📍 포지션 시트 이동 (선택 안 함 가능)",
        ["선택 안 함", "Audio/Video", "RACE",
         "LAB", "운영설비", "충전설비", "정비고", "기타"]
    )

    # 상태별 버튼
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
                    ws.update_cell(row_index, 11, 포지션_이동 if 포지션_이동 != "선택 안 함" else "")
                    ws.update_cell(row_index, 15, "장애 등록")

                    st.success(f"✅ '{issue['설비명']}' 장애가 점검중으로 변경되었습니다.")
                    st.session_state["selected_issue"] = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 점검 시작 중 오류 발생: {e}")

    elif issue.get("상태") == "점검중":
        점검내용 = st.text_area("🧰 점검내용", height=100)
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
                    st.session_state["selected_issue"] = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 완료 처리 중 오류: {e}")
else:
    st.info("📋 왼쪽 체크박스를 클릭하여 장애를 선택하세요.")
