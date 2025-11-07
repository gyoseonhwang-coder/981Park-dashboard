import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# ─────────────────────────────
# ✅ 허용된 이메일 목록
# ─────────────────────────────
ALLOWED_EMAILS = [
    "gyoseon.hwang@monolith.co.kr",
    "hyunjong.cho@monolith.co.kr",
    "seonghoon.kang@monolith.co.kr",
]

# ─────────────────────────────
# ✅ 사용자 인증 (localStorage 기반)
# ─────────────────────────────
def get_current_user():
    # 1️⃣ localStorage에서 복원 시도
    saved_email = streamlit_js_eval(js_expressions="localStorage.getItem('981_user_email')", key="get_user_email")
    if saved_email:
        st.session_state.user_email = saved_email
        return saved_email

    # 2️⃣ 세션에 이미 있으면 그대로 유지
    if "user_email" in st.session_state:
        return st.session_state.user_email

    # 3️⃣ 로그인 폼 표시
    with st.sidebar:
        st.markdown("### 👋 환영합니다.")
        st.write("최초 1회만 이메일을 입력해주세요.")
        email = st.text_input("회사 이메일 입력", key="email_input").strip().lower()
        if st.button("확인"):
            if "@monolith.co.kr" not in email:
                st.warning("회사 이메일(@monolith.co.kr)만 사용 가능합니다.")
            else:
                st.session_state.user_email = email
                # localStorage에 저장
                streamlit_js_eval(js_expressions=f"localStorage.setItem('981_user_email', '{email}')", key="set_user_email")
                st.success("✅ 로그인 정보가 저장되었습니다. 페이지를 새로고침해주세요.")
                st.stop()
        st.stop()

    return None


# ─────────────────────────────
# ✅ 로그아웃 함수
# ─────────────────────────────
def logout():
    streamlit_js_eval(js_expressions="localStorage.removeItem('981_user_email')", key="logout_user")
    if "user_email" in st.session_state:
        del st.session_state.user_email
    st.success("🚪 로그아웃 완료! 새로고침하면 로그인 창이 표시됩니다.")


# ─────────────────────────────
# ✅ 사이드바 렌더링
# ─────────────────────────────
def render_sidebar(active=None):
    email = get_current_user()
    if not email:
        return

    st.sidebar.markdown("### 📍 메뉴")
    st.sidebar.markdown(f"현재 계정: `{email}`")

    # Crew 메뉴
    with st.sidebar.expander("🧑‍✈️ Crew", expanded=True):
        st.page_link("pages/01_issueform.py", label="📝 장애 접수")

    # 기술지원 메뉴
    if email in ALLOWED_EMAILS:
        st.sidebar.divider()
        st.sidebar.markdown("### 🧰 기술지원")
        st.page_link("app.py", label="📊 Dashboard")
        st.page_link("pages/02_issue_manage.py", label="🧾 장애 처리")
        st.page_link("pages/daily_report.py", label="📅 Daily")

        if st.sidebar.button("🚪 로그아웃"):
            logout()
    else:
        st.sidebar.divider()
        st.sidebar.info("🔒 기술지원 전용 메뉴는 접근 권한이 없습니다.")
