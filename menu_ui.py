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
def render_sidebar(active: str = "Dashboard"):
    """981Park Streamlit 사이드바 (Crew + 기술지원 + 권한 제어 포함)"""
    with st.sidebar:
        st.markdown("## 📍 메뉴")

        # 환경 감지
        is_cloud = "mount/src" in sys.path[0] or os.environ.get("STREAMLIT_RUNTIME")
        email, name = get_current_user()

        # ─────────────────────────────────────────────
        # 👋 상단 사용자 환영 메시지
        # ─────────────────────────────────────────────
        st.markdown("### 👋 " + (f"안녕하세요, **{name}** 님" if name else "환영합니다."))
        st.caption(f"현재 계정: `{email}`")
        st.markdown("---")

        # ─────────────────────────────────────────────
        # 🧑‍✈️ Crew 메뉴 (공통)
        # ─────────────────────────────────────────────
        with st.expander("🧑‍✈️ Crew", expanded=True):
            if st.button("🧾 장애 접수", use_container_width=True):
                try:
                    if is_cloud:
                        st.switch_page("pages/01_issueform")
                    else:
                        st.switch_page("pages/01_issueform.py")
                except Exception:
                    st.page_link("pages/01_issueform.py", label="🧾 장애 접수")

        # ─────────────────────────────────────────────
        # 🛠️ 기술지원 메뉴 (권한 사용자 전용)
        # ─────────────────────────────────────────────
        if email in AUTHORIZED_USERS:
            with st.expander("🛠️ 기술지원", expanded=True):
                if st.button("📊 Dashboard", use_container_width=True):
                    try:
                        if is_cloud:
                            st.switch_page("Home")
                        else:
                            st.switch_page("app.py")
                    except Exception:
                        st.page_link("Home", label="📊 Dashboard")

                if st.button("📅 Daily", use_container_width=True):
                    try:
                        if is_cloud:
                            st.switch_page("pages/daily_report")
                        else:
                            st.switch_page("pages/daily_report.py")
                    except Exception:
                        st.page_link("pages/daily_report.py", label="📅 Daily")

                if st.button("🧰 장애 처리", use_container_width=True):
                    try:
                        if is_cloud:
                            st.switch_page("pages/02_issue_manage")
                        else:
                            st.switch_page("pages/02_issue_manage.py")
                    except Exception:
                        st.page_link("pages/02_issue_manage.py", label="🧰 장애 처리")
        else:
            st.markdown("---")
            st.info("🔒 기술지원 전용 메뉴는 접근 권한이 없습니다.")

        st.markdown("---")
        st.caption("© 2025 981Park Technical Support Team")
