import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
from menu_ui import render_sidebar, get_current_user, AUTHORIZED_USERS

# 페이지 설정
st.set_page_config(page_title="🧰 장애 처리", layout="wide")

# 공통 스타일 (타이틀 상단 여백 제거 + 전체 테마 포함)
st.markdown("""
<style>
/* ────────────────────────────────
 📦 전체 UI 공통 스타일
──────────────────────────────── */

/* 사이드바 제거 */
[data-testid="stSidebarNav"] { display:none !important; }
section[data-testid="stSidebar"] div[role="listbox"] { display:none !important; }

/* 폰트 / 헤딩 */
html, body { font-family: 'Noto Sans KR', sans-serif !important; }
h1, h2, h3 { font-weight: 700 !important; }

/* ────────────────────────────────
 🎨 콘텐츠 영역 (block-container) 상단 여백 보정
──────────────────────────────── */

/* 기본 여백 변수 (데스크탑 기준) */
:root { --top-gap: 48px; } /* 필요시 px값 조절: 40~80 권장 */

div[data-testid="stAppViewContainer"] > .main > div.block-container,
div[data-testid="stAppViewContainer"] .main .block-container,
main .block-container,
div.block-container {
    padding-top: var(--top-gap) !important;
    margin-top: 0 !important;
}

/* 헤더의 line-height 및 마진 보정 */
div.block-container h1, div.block-container h2 {
    margin-top: 0 !important;
    padding-top: 0 !important;
    line-height: 1.05 !important;
}

/* 상단 툴바 겹침 방지 */
header, [data-testid="stToolbar"] {
    position: relative;
    z-index: 1000;
}

/* 작은 화면(모바일/태블릿) 대응 */
@media (max-width: 900px) {
  :root { --top-gap: 20px; }
  div.block-container h1 { font-size: 1.35rem !important; }
}

/* ────────────────────────────────
 🧩 상세 패널 / 박스 애니메이션
──────────────────────────────── */
.detail-box {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    padding: 24px;
    animation: fadeIn 0.3s ease-in;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateX(10px); }
    to { opacity: 1; transform: translateX(0); }
}

/* ────────────────────────────────
 🔧 오른쪽 안내 박스 높이 보정
──────────────────────────────── */
div[data-testid="column"]:has(div[data-testid="stVerticalBlock"]) > div:has(.stAlert) {
    margin-top: 18px !important; /* 15~20px 정도로 조정해보며 맞추면 됨 */
}
</style>

<script>
(function(){
  // 상단 여백 강제 유지 (DOM 재렌더링 방지용)
  function ensureTopGap(){
    try {
      const gap = getComputedStyle(document.documentElement).getPropertyValue('--top-gap') || '48px';
      const selectors = [
        'div[data-testid="stAppViewContainer"] > .main > div.block-container',
        'div[data-testid="stAppViewContainer"] .main .block-container',
        'main .block-container',
        'div.block-container'
      ];
      selectors.forEach(sel => {
        const el = document.querySelector(sel);
        if (el) {
          el.style.paddingTop = gap;
        }
      });
    } catch(e){ console && console.warn && console.warn("ensureTopGap error", e); }
  }

  // 즉시/지연 적용 (Streamlit의 rerun에 대응)
  ensureTopGap();
  setTimeout(ensureTopGap, 150);
  setTimeout(ensureTopGap, 600);
})();
</script>
""", unsafe_allow_html=True)




# 인증
email, name = get_current_user()
if not email or email.strip().lower() not in [e.lower() for e in AUTHORIZED_USERS]:
    st.error("🚫 이 메뉴는 기술지원 전용입니다.")
    st.stop()

render_sidebar(active="IssueManage")

@st.cache_resource
def get_gspread_client():
    creds_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds)

gc = get_gspread_client()

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_LOG = "접수내용"

@st.cache_data(ttl=30)
def load_issue_log():
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(data[1:], columns=data[0])
    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].replace("", "—")
    if "상태" not in df.columns and "접수처리" in df.columns:
        df["상태"] = df["접수처리"]
    df["상태"] = df["상태"].replace({
        "접수중": "접수중",
        "미조치(접수중)": "접수중",
        "점검중": "점검중",
        "운영중": "운영중",
        "운영중단": "운영중단",
        "완료": "완료"
    })
    return df

def move_issue_to_position(payload):
    """981파크 장애관리 - 접수내용 -> 포지션 시트 이동"""
    try:
        sh = gc.open(SPREADSHEET_NAME)
        position = payload.get("포지션", "").strip()
        if not position:
            st.warning("⚠️ 포지션 정보가 없어 포지션 시트로 이동하지 못했습니다.")
            return

        # 포지션 시트 없으면 생성
        try:
            target_ws = sh.worksheet(position)
        except Exception:
            target_ws = sh.add_worksheet(title=position, rows="500", cols="20")
            headers = [
                "위치", "설비명", "세부장치", "장애유형", "장애내용",
                "접수처리", "장애등록", "점검자", "완료일자"
            ]
            target_ws.append_row(headers)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ✅ 실제 시트 순서에 맞게 정렬
        new_row = [
            payload.get("위치", ""),
            payload.get("설비명", ""),
            payload.get("세부장치", ""),
            payload.get("장애유형", ""),
            payload.get("장애내용", ""),
            "점검중",                      # 접수처리
            payload.get("포지션", ""),      # 장애등록
            payload.get("점검자", ""),      # 점검자
            "",                            # 완료일자 (미기입)
        ]

        target_ws.append_row(new_row, value_input_option="USER_ENTERED")
        st.toast(f"📤 '{position}' 시트로 정확히 이동 완료", icon="✅")

    except Exception as e:
        st.error(f"❌ 포지션 시트 이동 중 오류 발생: {e}")

def update_issue_status(ws, row_index, 상태선택, 담당자, 점검내용):
    """
    장애 상태를 업데이트하고, 완료 시 Q열(종결 컬럼)에 '종결'을 기록한다.
    ws : gspread Worksheet 객체
    row_index : 수정할 행 번호 (2부터 시작)
    상태선택 : 새 상태 (점검중, 운영중, 운영중단, 완료)
    담당자 : 점검자 이름
    점검내용 : 점검 상세 내용
    """
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ✅ 상태 업데이트 (접수처리)
        ws.update_cell(row_index, 10, 상태선택)

        # ✅ 점검자 / 점검내용 / 완료일자 갱신
        ws.update_cell(row_index, 12, 담당자)
        ws.update_cell(row_index, 14, 점검내용)

        if 상태선택 == "완료":
            # ✅ 완료일자 입력 (M열, 13번째)
            ws.update_cell(row_index, 13, now)

            # ✅ Q열(17번째 컬럼)에 '종결' 입력
            ws.update_cell(row_index, 17, "종결")

        else:
            # 완료 아닐 경우, 완료일자 및 종결 표시 초기화
            ws.update_cell(row_index, 13, "")
            ws.update_cell(row_index, 17, "")

        st.toast("✅ 장애 상태 업데이트 완료 (시트 반영됨)", icon="✅")

    except Exception as e:
        st.error(f"❌ 시트 업데이트 중 오류 발생: {e}")


def render_detail_panel(issue, df):
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)

    st.markdown("### 🧩 장애 처리")
    st.markdown(f"""
    **설비명:** {issue.get('설비명', '-')}  
    **위치:** {issue.get('위치', '-')}  
    **장애내용:** {issue.get('장애내용', '-')}
    """)
    st.divider()

    current_status = issue.get("상태", "접수중")
    st.info(f"현재 상태: **{current_status}**")

    state_map = {
        "접수중": ["점검중", "운영중", "운영중단"],
        "점검중": ["운영중", "운영중단", "완료"],
        "운영중": ["점검중", "완료"],
        "운영중단": ["점검중", "완료"],
        "완료": []
    }

    options = state_map.get(current_status, [])
    if not options:
        st.success("✅ 완료된 장애입니다. 추가 변경 불가.")
        return

    상태선택 = st.selectbox("📊 상태 변경", options)
    포지션_이동 = st.selectbox(
        "📍 포지션 시트로 이동",
        ["선택 안 함", "Audio/Video", "RACE", "LAB", "운영설비", "충전설비", "정비고", "기타"]
    )
    담당자 = st.text_input("👷 점검자", issue.get("점검자", ""))
    점검내용 = st.text_area("🧾 점검내용", height=150, placeholder="조치 내용 또는 점검 결과를 입력하세요.")

    if st.button("💾 저장", use_container_width=True):
        row_index = df.index[df["장애내용"] == issue["장애내용"]][0] + 2
        update_issue_status(ws, row_index, 상태선택, 담당자, 점검내용)

        if 포지션_이동 != "선택 안 함":
            payload = issue.to_dict()
            payload.update({
                "점검자": 담당자,
                "점검내용": 점검내용,
                "포지션": 포지션_이동,
                "상태": 상태선택
            })
            move_issue_to_position(payload)

        st.rerun()

def main():
    st.title("💼 981Park 장애 처리")
    st.caption(f"접속 계정: {email}")

    df = load_issue_log()
    if df.empty:
        st.warning("⚠️ 데이터가 없습니다.")
        return

    # 보여줄 장애 목록
    pending = df[df["상태"].isin(["접수중", "점검중", "운영중", "운영중단"])].copy()

    # ✅ 체크박스 열 추가
    pending.insert(0, "선택", False)

    # ✅ 표시할 컬럼 목록 수정 (선택 컬럼 포함)
    cols_show = [c for c in ["선택", "포지션", "위치", "설비명", "장애내용", "상태", "점검자"] if c in pending.columns]

    # 세션 초기화
    if "selected_issue" not in st.session_state:
        st.session_state["selected_issue"] = None

    col_list, col_detail = st.columns([3, 1], gap="large")

    with col_list:
        st.subheader("📋 장애 목록")

        # ✅ '선택' 컬럼 포함한 데이터 편집기 표시
        edited = st.data_editor(
            pending[cols_show],
            use_container_width=True,
            height=500,
            hide_index=True,
            key="issue_table",
        )

        # ✅ 체크된 행 탐색
        if "선택" in edited.columns:
            selected_rows = edited[edited["선택"] == True]

            if len(selected_rows) == 0:
                st.warning("⚠️ 처리할 장애를 선택하세요.")
                st.session_state["selected_issue"] = None
            elif len(selected_rows) > 1:
                st.info("ℹ️ 여러 항목이 선택되었습니다. 가장 최근 선택된 장애만 표시됩니다.")
                last_selected = selected_rows.iloc[-1]
                st.session_state["selected_issue"] = last_selected
            else:
                st.session_state["selected_issue"] = selected_rows.iloc[0]
        else:
            st.error("⚠️ 데이터 편집기에서 '선택' 컬럼을 찾을 수 없습니다.")
            st.session_state["selected_issue"] = None

        # ✅ 선택된 장애 표시
        if st.session_state["selected_issue"] is not None:
            issue = st.session_state["selected_issue"]
            st.success(f"✅ 선택됨: {issue['설비명']} — {issue['장애내용']}")

    # ✅ 오른쪽 상세 패널 표시
    with col_detail:
        if st.session_state["selected_issue"] is not None:
            issue = st.session_state["selected_issue"]
            with st.container(border=True):
                render_detail_panel(issue, df)
        else:
            st.info("📋 왼쪽에서 장애를 체크하면 상세 정보가 표시됩니다.")





if __name__ == "__main__":
    main()
