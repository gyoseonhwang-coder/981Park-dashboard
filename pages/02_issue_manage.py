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

#🔒 사이드바 네비게이션 숨김 처리 (app / issueform / issue manage)
st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none !important;}
section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

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

    # 날짜 정리
    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].apply(lambda x: x if x.strip() != "" else "—")

    # 상태 표준화
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

    return df


# ─────────────────────────────────────────────
# 메인 UI
# ─────────────────────────────────────────────
st.title("🧰 981Park 장애 처리")
st.subheader("🧾 조치 필요 목록 (미조치/점검중)")

st.divider()

df = load_issue_log()

if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

pending = df[df["상태"].isin(["미조치(접수중)", "점검중"])].copy()
pending = pending.sort_values("날짜", ascending=False)

cols_show = [c for c in ["날짜", "포지션", "위치", "설비명",
                         "장애내용", "상태", "점검자"] if c in pending.columns]
st.dataframe(pending[cols_show], use_container_width=True, height=320)

st.divider()

# ─────────────────────────────────────────────
# 🔹 처리할 장애 선택 (단일 텍스트 + 스타일 개선)
# ─────────────────────────────────────────────

# Selectbox 내부 텍스트 줄바꿈 허용 (장애 내용이 짤리지 않도록)
st.markdown("""
<style>
/* selectbox 내부 줄바꿈 및 스타일 개선 */
div[data-baseweb="select"] span {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    line-height: 1.5em !important;
}
/* 라벨 텍스트 (📋 처리할 장애 선택) 크기 확대 */
div.stSelectbox > label > div {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #222 !important;
    margin-bottom: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# 장애 목록 표시
row_labels = [
    f"[{r['상태']}] {r['설비명']} — {r['장애내용']}"
    for _, r in pending.iterrows()
]

# 선택 박스 표시 (라벨 1개만 사용)
selected_label = st.selectbox(
    "📋 처리할 장애 선택",
    ["선택 안 함"] + row_labels,
    index=0,
)

# 선택된 장애 표시
if selected_label != "선택 안 함":
    selected_index = row_labels.index(selected_label)
    issue = pending.iloc[selected_index]

    # 카드형 UI
    st.markdown("---")
    st.markdown(
        f"### 🧩 선택된 장애 — <span style='color:#16a34a;font-weight:600'>{issue.get('포지션', '-')} {issue.get('설비명', '-')}</span>",
        unsafe_allow_html=True
    )

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
    .issue-card b {
        color: #111;
    }
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

    st.markdown("### 👷 조치 내용 입력")

    담당자 = st.text_input("👷 점검자 이름", issue.get("점검자", ""))
    포지션_이동 = st.selectbox(
        "📍 포지션 시트로 이동 (선택 안 함 가능)",
        ["선택 안 함", "Audio/Video", "RACE", "LAB", "운영설비", "충전설비", "정비고", "기타"]
    )

    # 상태별 처리 버튼
    # 🚧 접수중 → 점검중
    if issue.get("상태") == "미조치(접수중)":
        st.info("📩 이 장애는 아직 접수되지 않았습니다. 아래 정보를 입력하고 장애를 접수하세요.")
        if st.button("🚧 장애 접수 (접수중 → 점검중)", use_container_width=True):
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
                        row_index, 11, 포지션_이동 if 포지션_이동 != "선택 안 함" else ""
                    )
                    ws.update_cell(row_index, 15, "장애 등록")

                    # ✅ UX 개선 포인트: 토스트 + 스피너 + 자연스러운 새로고침
                    st.toast(f"✅ '{issue['설비명']}' 장애가 접수되었습니다.", icon="📨")
                    st.success("⚙️ 장애 상태가 '점검중'으로 변경되었습니다.")
                    with st.spinner("🔄 변경 사항을 반영 중입니다..."):
                        import time
                        time.sleep(2.0)
                    st.session_state.popup_issue = None
                    st.experimental_rerun()

            except Exception as e:
                st.error(f"❌ 장애 접수 중 오류 발생: {e}")

    # 🧰 점검중 → 완료
    elif issue.get("상태") == "점검중":
        st.info("🧰 점검이 완료되면 아래 내용을 입력 후 완료 처리하세요.")
        점검내용 = st.text_area("🔧 점검내용", height=120,
                            placeholder="점검 결과나 조치 내용을 입력하세요.")
        if st.button("✅ 완료 처리 (점검중 → 완료)", use_container_width=True):
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
                    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    ws.update_cell(row_index, 10, "완료")      # 상태 변경
                    ws.update_cell(row_index, 13, now)          # 완료일자
                    ws.update_cell(row_index, 14, 점검내용)      # 점검내용
                    ws.update_cell(row_index, 15, "장애 처리")   # 관리 플래그
                    ws.update_cell(row_index, 17, "종결")       # 종결 상태

                    # ✅ UX 개선 포인트: 동일한 시각 피드백 로직
                    st.toast(f"🎉 '{issue['설비명']}' 장애가 완료 처리되었습니다.", icon="✅")
                    st.success("🟢 장애 상태가 '완료'로 변경되었습니다.")
                    with st.spinner("💾 변경 내용을 저장하고 있습니다..."):
                        import time
                        time.sleep(2.0)
                    st.session_state.popup_issue = None
                    st.rerun()

            except Exception as e:
                st.error(f"❌ 완료 처리 중 오류: {e}")

    else:
        st.info("📋 위 목록에서 처리할 장애를 선택하세요.")

    st.caption("© 2025 981Park Technical Support Team — 장애 처리 시스템")
