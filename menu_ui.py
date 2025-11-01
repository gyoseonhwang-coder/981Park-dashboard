import streamlit as st
import os


def render_sidebar(active: str = "Dashboard"):
    """왼쪽 고정 사이드 메뉴 (로컬 + Streamlit Cloud 완전 호환형)"""
    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # 현재 실행 환경 확인
        is_cloud = os.environ.get("STREAMLIT_RUNTIME") is not None

        # Dashboard 이동 버튼
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                if is_cloud:
                    st.switch_page("/")  # Cloud root page
                else:
                    st.switch_page("app.py")  # Local
            except Exception as e:
                st.error(f"⚠️ 이동 실패: {e}")

        # 장애 접수 이동 버튼
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                if is_cloud:
                    st.switch_page("/01_issueform")  # Cloud page route
                else:
                    st.switch_page("pages/01_issueform.py")  # Local dev
            except Exception as e:
                st.error(f"⚠️ 이동 실패: {e}")

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")
