import streamlit as st
import sys
import os

import streamlit as st
import sys
import os

# ✅ Cloud/로컬 페이지 리스트 확인 (rerun 없이)
try:
    from streamlit.source_util import get_pages
    pages = get_pages("")
    st.sidebar.write("🔍 Available pages:", list(pages.keys()))
except Exception as e:
    st.sidebar.write("⚠️ 페이지 목록 확인 실패:", str(e))


def render_sidebar(active: str = "Dashboard"):
    """981Park Streamlit 사이드바 - Cloud/로컬 자동 감지 + 완전 안전 전환"""

    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # Streamlit Cloud 환경 감지
        IS_CLOUD = "mount/src" in sys.path[0] or os.environ.get(
            "STREAMLIT_RUNTIME") == "true"

        # ✅ Dashboard 이동
        if st.button("📊 Dashboard", use_container_width=True):
            try:
                if IS_CLOUD:
                    st.switch_page("Home")  # Cloud에서는 app.py가 "Home"으로 등록됨
                else:
                    st.switch_page("app.py")
            except Exception:
                # fallback (Cloud에서 경로 불일치 시)
                try:
                    st.page_link("Home", label="📊 Dashboard")
                except Exception:
                    st.experimental_rerun()

        # ✅ 장애 접수 이동
        if st.button("🧾 장애 접수", use_container_width=True):
            try:
                if IS_CLOUD:
                    # Cloud에서는 pages/01_issueform.py → "pages/01_issueform"
                    st.switch_page("pages/01_issueform")
                else:
                    st.switch_page("pages/01_issueform.py")
            except Exception:
                # fallback: 경로를 찾지 못할 경우 페이지 링크 시도
                try:
                    st.page_link("pages/01_issueform", label="🧾 장애 접수")
                except Exception:
                    st.experimental_rerun()

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")
