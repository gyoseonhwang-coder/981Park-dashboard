import streamlit as st
from streamlit_js_eval import streamlit_js_eval

AUTHORIZED_USERS = {
    "gyoseon.hwang@monolith.co.kr": "황교선",
    "hyunjong.cho@monolith.co.kr": "조현종",
    "seonghoon.kang@monolith.co.kr": "강성훈",
}
AUTHORIZED_EMAILS = list(AUTHORIZED_USERS.keys())
ALLOWED_DOMAIN = "@monolith.co.kr"

def get_current_user():
    """
    사용자 이메일을 localStorage / session_state에서 불러와 인증 처리.
    - @monolith.co.kr 도메인만 로그인 허용
    - 기술지원 여부는 AUTHORIZED_USERS로 구분
    """
    if "user_email" in st.session_state:
        email = st.session_state.user_email.strip().lower()
        return email, AUTHORIZED_USERS.get(email, "일반 사용자")

    saved_email = streamlit_js_eval(
        js_expressions="localStorage.getItem('981_user_email')",
        key="get_user_email",
    )
    if saved_email:
        email = saved_email.strip().lower()
        st.session_state.user_email = email
        return email, AUTHORIZED_USERS.get(email, "일반 사용자")

    with st.sidebar:
        st.markdown("### 👋 환영합니다.")
        st.write("회사 이메일(@monolith.co.kr)로 로그인해주세요.")
        email_input = st.text_input("📧 회사 이메일 입력", key="email_input").strip().lower()

        if st.button("확인", key="email_confirm_btn"):
            if not email_input.endswith(ALLOWED_DOMAIN):
                st.warning("회사 이메일(@monolith.co.kr)만 사용할 수 있습니다.")
            else:
                st.session_state.user_email = email_input
                streamlit_js_eval(
                    js_expressions=f"localStorage.setItem('981_user_email', '{email_input}')",
                    key="set_user_email",
                )
                st.success(f"✅ {email_input} 으로 로그인되었습니다!")
                st.rerun()

    return None, None

def is_monolith_user(email: str) -> bool:
    """@monolith.co.kr 이메일이면 True"""
    return bool(email and email.strip().lower().endswith("@monolith.co.kr"))

def is_tech_support(email: str) -> bool:
    """기술지원 계정이면 True"""
    return bool(email and email.strip().lower() in AUTHORIZED_USERS)

def render_sidebar(active=None):
    """공용 사이드바 렌더링"""
    email, name = get_current_user()

    if not email:
        return 

    st.sidebar.markdown(f"**👋 환영합니다, {name}님!**")
    st.sidebar.caption(f"현재 계정: `{email}`")

    with st.sidebar.expander("🧑‍✈️ @monolith", expanded=True):
        st.page_link("pages/01_issueform.py", label="📝 장애 접수")

    if email in AUTHORIZED_EMAILS:
        st.sidebar.divider()
        with st.sidebar.expander("🧑‍✈️ 기술지원", expanded=True):
            st.page_link("pages/daily_report.py", label="📅 Daily")
            st.page_link("app.py", label="📊 Dashboard")
            st.page_link("pages/02_issue_manage.py", label="🧾 장애 처리")
            st.page_link("pages/03_issue_history.py", label="🧾 장애 이력")
         
    else:
        st.sidebar.divider()
        st.sidebar.info("🔒 기술지원 전용 메뉴는 접근 권한이 없습니다.")
