import streamlit as st
import sys
import os


def render_sidebar(active: str = "Dashboard"):
    """981Park Streamlit 사이드바 (공통 메뉴 + 헤더 자동 제거 포함)"""

    # ✅ 헤더/파일명 완전 제거 (pages 포함)
    st.markdown("""
        <style>
        /* 모든 상단 헤더 및 파일명 제거 */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        div[data-testid="stMarkdownContainer"] h1,
        div.block-container > div:first-child h1,
        div[data-testid="stAppViewBlockContainer"] h1,
        div[data-testid="stVerticalBlock"] h1,
        div[data-testid="stHorizontalBlock"] h1,
        section.main > div:first-child h1 {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # ✅ 사이드바 메뉴
    # ─────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # 현재 환경 감지
        is_cloud = "mount/src" in sys.path[0] or os.environ.get("STREAMLIT_RUNTIME")

        # ✅ Dashboard 버튼
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                if is_cloud:
                    st.switch_page("Home")
                else:
                    st.switch_page("app.py")
            except Exception:
                st.page_link("Home", label="📊 Dashboard")

        # ✅ Daily 버튼
        if st.button("📅 Daily", use_container_width=True):
            try:
                if is_cloud:
                    st.switch_page("pages/daily_report")
                else:
                    st.switch_page("pages/daily_report.py")
            except Exception:
                st.page_link("pages/daily_report.py", label="📅 Daily")

        # ✅ 장애 접수 버튼
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                if is_cloud:
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
