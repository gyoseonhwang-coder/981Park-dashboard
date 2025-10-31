import streamlit as st


def render_sidebar(active: str = "Dashboard"):
    """
    항상 열려있는 왼쪽 사이드바
    """
    # 기본 내비게이션 숨김
    st.markdown("""
    <style>
      [data-testid="stSidebarNav"] { display: none !important; }
      section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
        padding-top: 18px;
      }
    </style>
    """, unsafe_allow_html=True)

    # 사이드 메뉴 표시
    st.sidebar.markdown("### 🧭 Navigation")

    # ✅ 여기서 이모지는 실제 문자로! (콜론(:) 금지)
    st.sidebar.page_link("app.py", label="📊 Dashboard", icon="📊")
    st.sidebar.page_link("pages/01_issueform.py", label="🧾 장애 접수", icon="🧾")

    # 현재 페이지 표시
    if active == "Dashboard":
        st.sidebar.success("현재 페이지: Dashboard")
    elif active == "IssueForm":
        st.sidebar.success("현재 페이지: 장애 접수")
