import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# ─────────────────────────────
# ✅ 허용된 이메일 목록 및 이름 매핑
# ─────────────────────────────
AUTHORIZED_USERS = {
    "gyoseon.hwang@monolith.co.kr": "황교선",
    "hyunjong.cho@monolith.co.kr": "조현종",
    "seonghoon.kang@monolith.co.kr": "강성훈",
}
ALLOWED_EMAILS = list(AUTHORIZED_USERS.keys())


# ─────────────────────────────
# ✅ 사용자 인증 (새로고침 없는 즉시 로그인)
# ─────────────────────────────
def get_current_user():
    """
    로그인 정보 확인 및 반환 (email, name)
    - localStorage → session_state → 입력 순서
    - rerun/st.stop() 없이 즉시 반영
    """
    # 1️⃣ 이미 로그인된 사용자
    if "user_email" in st.session_state:
        email = st.session_state.user_email.strip().lower()
        return email, AUTHORIZED_USERS.get(email, "게스트")

    # 2️⃣ localStorage 확인
    saved_email = streamlit_js_eval(
        js_expressions="localStorage.getItem('981_user_email')",
        key="get_user_email",
    )
    if saved_email:
        email = saved_email.strip().lower()
        st.session_state.user_email = email
        return email, AUTHORIZED_USERS.get(email, "게스트")

    # 3️⃣ 이메일 입력 UI 표시 (처음 로그인 시)
    with st.sidebar:
        st.markdown("### 👋 환영합니다.")
        st.write("최초 1회만 회사 이메일을 입력해주세요.")
        email_input = st.text_input("📧 회사 이메일 입력", key="email_input").strip().lower()

        if st.button("확인", key="email_confirm_btn"):
            if "@monolith.co.kr" not in email_input:
                st.warning("회사 이메일(@monolith.co.kr)만 사용 가능합니다.")
            else:
                st.session_state.user_email = email_input
                streamlit_js_eval(
                    js_expressions=f"localStorage.setItem('981_user_email', '{email_input}')",
                    key="set_user_email",
                )
                st.success(f"✅ {email_input} 으로 로그인되었습니다!")
                st.experimental_rerun()

    return None, None


# ─────────────────────────────
# ✅ 사이드바 렌더링
# ─────────────────────────────
def render_sidebar(active=None):
    """공용 사이드바 렌더링"""
    email, name = get_current_user()

    # 로그인되지 않은 경우 → 로그인 UI만 표시
    if not email:
        return

    # ─ 메뉴 헤더 ─
    st.sidebar.markdown("### 📍 메뉴")
    st.sidebar.markdown(f"**👋 환영합니다, {name}님!**")
    st.sidebar.caption(f"현재 계정: `{email}`")

    # ─ Crew 메뉴 (모두 접근 가능) ─
    with st.sidebar.expander("🧑‍✈️ Crew", expanded=True):
        st.page_link("pages/01_issueform.py", label="📝 장애 접수")

    # ─ 기술지원 전용 메뉴 (권한자만 접근 가능) ─
    if email in ALLOWED_EMAILS:
        st.sidebar.divider()
        st.sidebar.markdown("### 💼 기술지원")
        st.page_link("app.py", label="📊 Dashboard")
        st.page_link("pages/02_issue_manage.py", label="🧾 장애 처리")
        st.page_link("pages/daily_report.py", label="📅 Daily")
    else:
        st.sidebar.divider()
        st.sidebar.info("🔒 기술지원 전용 메뉴는 접근 권한이 없습니다.")
