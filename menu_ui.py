import streamlit as st
import sys
import os


def render_sidebar(active: str = "Dashboard"):
    """981Park Streamlit 사이드바 (로컬 & Cloud 완전 호환)"""

    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # 현재 환경 감지
        is_cloud = "mount/src" in sys.path[0] or os.environ.get(
            "STREAMLIT_RUNTIME")

        # ✅ Dashboard 버튼
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                if is_cloud:
                    # Cloud 환경에서는 Home 이 기본 페이지
                    st.switch_page("Home")
                else:
                    # 로컬 환경
                    st.switch_page("app.py")
            except Exception:
                # Fallback — Cloud에서 switch_page 실패 시 page_link 로 대체
                st.page_link("Home", label="📊 Dashboard")

        # ✅ 장애 접수 버튼
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                if is_cloud:
                    # Cloud에서는 확장자 없이 등록됨
                    st.switch_page("pages/01_issueform")
                else:
                    st.switch_page("pages/01_issueform.py")
            except Exception:
                st.page_link("pages/01_issueform.py", label="🧾 장애 접수")

        # ✅ 장애 처리 버튼
        if st.button("🧰 장애 처리", use_container_width=True):
            try:
                if is_cloud:
                    st.switch_page("pages/02_issue_manage")
                else:
                    st.switch_page("pages/02_issue_manage.py")
            except Exception:
                st.page_link("pages/02_issue_manage.py", label="🧰 장애 처리")

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")
