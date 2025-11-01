import streamlit as st
import sys

def render_sidebar(active: str = "Dashboard"):
    """981Park Streamlit 사이드바 - Cloud/로컬 자동 감지"""

    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # Dashboard 이동
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                # ✅ Cloud에서는 app.py 대신 "Home"
                if "mount/src" in sys.path[0]:
                    st.switch_page("Home")
                else:
                    st.switch_page("app.py")
            except Exception:
                st.page_link("Home", label="📊 Dashboard")

        # 장애 접수 이동
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                # ✅ Cloud에서는 이렇게 등록됨
                if "mount/src" in sys.path[0]:
                    st.switch_page("pages/01_issueform")
                else:
                    st.switch_page("pages/01_issueform.py")
            except Exception:
                st.page_link("pages/01_issueform.py", label="🧾 장애 접수")

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")
