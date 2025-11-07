import streamlit as st
import sys
import os

# ─────────────────────────────────────────────
# ✅ 1. 기술지원팀 권한 계정 정의
# ─────────────────────────────────────────────
AUTHORIZED_USERS = {
    "gyoseon.hwang@monolith.co.kr": "황교선",
    "hyunjong.cho@monolith.co.kr": "조현종",
    "seonghoon.kang@monolith.co.kr": "강성훈"
}


def get_user_info():
    """현재 로그인한 사용자 정보 안전하게 반환"""
    user = getattr(st, "user", None)
    email = getattr(user, "email", "guest")
    name = getattr(user, "name", "게스트")
    return name, email
def get_current_user():
    """현재 사용자 이메일/이름 반환 (st.user 기반 최신 버전)"""
    try:
        # ✅ 최신 Streamlit API (2025 이후)
        email = getattr(st.user, "email", None)
    except Exception:
        email = None

    # 로컬 실행 시에는 환경변수 기반 대체
    if not email:
        email = os.getenv("USER_EMAIL", os.getenv("USERNAME", "guest"))

    email = email.lower()
    name = AUTHORIZED_USERS.get(email)
    return email, name

# ─────────────────────────────────────────────
# ✅ 2. 사이드바 렌더링
# ─────────────────────────────────────────────
def render_sidebar(active=None):
    name, email = get_user_info()

    st.sidebar.markdown("### 📍 메뉴")
    st.sidebar.markdown(f"👋 환영합니다, **{name}**님.")
    st.sidebar.caption(f"현재 계정: `{email}`")

    st.sidebar.divider()

    # ──────────────────────────────
    # Crew 메뉴
    # ──────────────────────────────
    with st.sidebar.expander("🧑‍✈️ Crew", expanded=True):
        st.page_link("pages/01_issueform.py", label="📋 장애 접수")

    # ──────────────────────────────
    # 기술지원 메뉴 접근 제한
    # ──────────────────────────────
    allowed_users = [
        "gyoseon.hwang@monolith.co.kr",
        "hyunjong.cho@monolith.co.kr",
        "seonghoon.kang@monolith.co.kr"
    ]

    if email in allowed_users:
        st.sidebar.divider()
        with st.sidebar.expander("🧰 기술지원", expanded=True):
            st.page_link("pages/02_issue_manage.py", label="🧾 장애 처리")
            st.page_link("pages/daily_report.py", label="📅 Daily")
            st.page_link("pages/dashboard.py", label="📊 Dashboard")
    else:
        st.sidebar.divider()
        st.sidebar.info("🔒 기술지원 전용 메뉴는 접근 권한이 없습니다.", icon="🔒")

    st.sidebar.divider()
    st.sidebar.caption("© 2025 981Park Technical Support Team")