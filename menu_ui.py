import streamlit as st


def render_sidebar(active: str = "Dashboard"):
    """왼쪽 사이드바 렌더링"""
    with st.sidebar:
        st.markdown(
            "<h2 style='color:#2c7be5; margin-bottom:20px;'>📋 981Park</h2>",
            unsafe_allow_html=True,
        )

        # Dashboard 버튼
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("app.py")

        # 장애 접수 버튼
        if st.button("🧾 장애 접수", use_container_width=True):
            st.switch_page("pages/01_issueform.py")

        st.markdown("---")
        st.caption("© 2025 981Park Dashboard")

        # 현재 활성 페이지 강조 (텍스트 표시)
        st.markdown(
            f"<p style='color:gray; font-size:14px;'>현재 페이지: <b>{active}</b></p>",
            unsafe_allow_html=True
        )
