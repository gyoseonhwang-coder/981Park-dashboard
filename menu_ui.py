import streamlit as st

# ─────────────────────────────────────────────
# ✅ 기본 Streamlit Navigation 패널 숨기기
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* 기본 Pages 탐색 메뉴 숨기기 */
[data-testid="stSidebarNav"] {display: none !important;}
section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
/* 상단 여백 최소화 */
[data-testid="stSidebar"] {padding-top: 0px !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ✅ 커스텀 사이드바 메뉴
# ─────────────────────────────────────────────
def render_sidebar(active: str = "Dashboard"):
    """981Park 전용 사이드바"""
    with st.sidebar:
        st.markdown("### 🚀 981Park")
        st.markdown("---")

        # 메뉴 항목
        st.page_link("app.py", label="📊 Dashboard")
        st.page_link("pages/01_issueform.py", label="🧾 장애 접수")

        st.markdown("---")
        st.caption("981Park Technical Support © 2025")
