import streamlit as st
import os


def render_sidebar(active: str = "Dashboard"):
    """로컬 + Cloud 환경 자동 감지 사이드바"""
    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # 📊 Dashboard 이동
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                if os.environ.get("STREAMLIT_RUNTIME"):  # Cloud 환경
                    st.switch_page("Home")
                else:  # 로컬
                    st.switch_page("app.py")
            except Exception as e:
                st.error(f"⚠️ 이동 실패 (Dashboard): {e}")

        # 🧾 장애 접수 이동
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                if os.environ.get("STREAMLIT_RUNTIME"):  # Cloud 환경
                    # ✅ Cloud에서는 이렇게 등록되어 있음
                    st.switch_page("pages/01_issueform")
                else:  # 로컬 실행 시
                    st.switch_page("pages/01_issueform.py")
            except Exception as e:
                st.error(f"⚠️ 이동 실패 (IssueForm): {e}")

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")
