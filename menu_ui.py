import streamlit as st


def render_sidebar(active: str = "Dashboard"):
    """왼쪽 고정 사이드 메뉴 (Cloud 호환형)"""

    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # Dashboard 이동 버튼
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                st.switch_page("app.py")  # 로컬 환경
            except Exception:
                st.switch_page("Home")     # Streamlit Cloud 경로 fallback

        # 장애 접수 이동 버튼
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                st.switch_page("pages/01_issueform.py")  # 로컬 환경
            except Exception:
                # Streamlit Cloud fallback
                st.switch_page("IssueForm")

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")


def read_nav_target(default: str = "Dashboard") -> str:
    """URL query string에서 nav 파라미터 읽기"""
    nav = st.query_params.get("nav") if hasattr(st, "query_params") else None
    if isinstance(nav, list):
        nav = nav[0]
    if nav in ("Dashboard", "IssueForm"):
        return nav
    return default
