import streamlit as st


def render_sidebar(active: str = "Dashboard"):
    """왼쪽 고정 사이드 메뉴 (Cloud 호환형)"""

    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # Dashboard 이동
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                st.switch_page("app.py")  # 로컬
            except Exception:
                st.switch_page("/")  # Cloud 루트 페이지

        # 장애 접수 이동
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                st.switch_page("pages/01_issueform.py")  # 로컬
            except Exception:
                st.switch_page("/01_issueform")  # Cloud 페이지 경로 (앞에 / 필수)

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")
