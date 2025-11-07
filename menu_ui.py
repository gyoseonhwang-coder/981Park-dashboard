import streamlit as st
import sys
import os


def render_sidebar(active: str = "Dashboard"):
    """981Park Streamlit 사이드바 (공통 메뉴 + 헤더 자동 제거 포함)"""

    # ─────────────────────────────────────────────
    # ✅ 페이지 헤더 자동 제거 (파일명 표시 숨김)
    # ─────────────────────────────────────────────
    hide_header_script = """
    <script>
    function hideStreamlitHeader() {
        const titleSelectors = [
            'section.main h1',
            'div[data-testid="stMarkdownContainer"] h1',
            'div[data-testid="stAppViewBlockContainer"] h1'
        ];
        titleSelectors.forEach(sel => {
            const el = window.parent.document.querySelector(sel);
            if (el && /(01_issueform|02_issue_manage|03_daily|app)/i.test(el.innerText)) {
                el.style.display = 'none';
            }
        });
        const header = window.parent.document.querySelector('header[data-testid="stHeader"]');
        const toolbar = window.parent.document.querySelector('div[data-testid="stToolbar"]');
        const deco = window.parent.document.querySelector('[data-testid="stDecoration"]');
        if (header) header.style.display = 'none';
        if (toolbar) toolbar.style.display = 'none';
        if (deco) deco.style.display = 'none';
    }
    setTimeout(hideStreamlitHeader, 800);
    setInterval(hideStreamlitHeader, 1500);
    </script>
    """
    st.markdown(hide_header_script, unsafe_allow_html=True)

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
                    st.switch_page("pages/03_daily")
                else:
                    st.switch_page("pages/03_daily.py")
            except Exception:
                st.page_link("pages/03_daily.py", label="📅 Daily")

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
