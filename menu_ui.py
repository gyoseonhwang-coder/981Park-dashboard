import streamlit as st

def render_sidebar(active: str = "Dashboard"):
    """Cloud 완전 호환 사이드 메뉴"""

    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # 대시보드 이동
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("Home")  # ✅ Cloud에서는 "app.py"가 "Home"으로 등록됨

        # 장애 접수 이동
        if st.button("🧾 장애 접수", use_container_width=True):
            st.switch_page("01_issueform")  # ✅ "pages/01_issueform.py" → "01_issueform" 으로 등록됨

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")