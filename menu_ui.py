import streamlit as st


def render_sidebar(active: str = "Dashboard"):
    """
    항상 열려있는 왼쪽 사이드바에
    - 📊 Dashboard
    - 🧾 장애 접수
    두 버튼만 노출 (기본 Streamlit 자동 내비게이션 숨김)
    """
    # ✅ 기본 멀티페이지 내비게이션 영역 숨김
    st.markdown("""
    <style>
      /* Streamlit 기본 사이드바 네비 숨김 */
      [data-testid="stSidebarNav"] { display: none !important; }
      /* 사이드바 폭과 내부 여백 약간 정리 */
      section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
        padding-top: 18px;
      }
    </style>
    """, unsafe_allow_html=True)

    # ✅ 우리 메뉴 렌더링 (항상 보임)
    st.sidebar.markdown("### 🧭 Navigation")
    # Streamlit 1.50: page_link 지원
    st.sidebar.page_link("app.py", label="📊 Dashboard", icon=":bar_chart:")
    st.sidebar.page_link("pages/01_issueform.py",
                         label="🧾 장애 접수", icon=":memo:")

    # 선택 상태 표시(하이라이트 느낌)
    if active == "Dashboard":
        st.sidebar.success("현재: Dashboard")
    elif active == "IssueForm":
        st.sidebar.success("현재: 장애 접수")
