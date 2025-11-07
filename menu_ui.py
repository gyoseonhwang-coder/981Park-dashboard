import streamlit as st
import sys
import os
import base64
import json
import time

# ─────────────────────────────────────────────
# ✅ 허용된 이메일 목록 (기술지원 전용)
# ─────────────────────────────────────────────
ALLOWED_EMAILS = [
    "gyoseon.hwang@monolith.co.kr",
    "hyunjong.cho@monolith.co.kr",
    "seonghoon.kang@monolith.co.kr",
]


# ─────────────────────────────────────────────
# ✅ localStorage 연동 (Streamlit JS <-> Python)
# ─────────────────────────────────────────────
def sync_user_from_localstorage():
    """JS localStorage에 저장된 이메일을 Streamlit 세션으로 복원"""
    js = """
    <script>
    const email = localStorage.getItem("981_user_email");
    if (email) {
        const data = {email: email};
        window.parent.postMessage({isStreamlitMessage: true, type: "userEmailSync", data: data}, "*");
    }
    </script>
    """
    st.components.v1.html(js, height=0)

    # Streamlit의 Custom Message Handler 수신
    msg = st.session_state.get("_js_msg")
    if msg and "email" in msg:
        st.session_state.user_email = msg["email"]


def save_user_to_localstorage(email):
    """이메일을 localStorage에 저장"""
    js = f"""
    <script>
    localStorage.setItem("981_user_email", "{email}");
    </script>
    """
    st.components.v1.html(js, height=0)


def clear_localstorage():
    """로그아웃 시 localStorage 삭제"""
    js = """
    <script>
    localStorage.removeItem("981_user_email");
    </script>
    """
    st.components.v1.html(js, height=0)


# ─────────────────────────────────────────────
# ✅ 사용자 인증
# ─────────────────────────────────────────────
def get_current_user():
    """localStorage + 세션 기반 로그인"""
    # localStorage에 저장된 이메일을 복원
    sync_user_from_localstorage()

    # 세션에 이미 있으면 바로 리턴
    if "user_email" in st.session_state:
        return st.session_state.user_email

    # 입력창 표시
    with st.sidebar:
        st.markdown("### 👋 환영합니다.")
        st.write("최초 1회만 이메일을 입력해주세요.")
        email = st.text_input("회사 이메일 입력", key="manual_email_input").strip().lower()
        if st.button("확인", key="manual_email_submit"):
            if "@monolith.co.kr" not in email:
                st.warning("회사 이메일(@monolith.co.kr)만 사용 가능합니다.")
            else:
                st.session_state.user_email = email
                save_user_to_localstorage(email)
                st.success("✅ 로그인 정보가 저장되었습니다. 페이지를 새로고침해주세요.")
                st.stop()
        st.stop()

    return None


# ─────────────────────────────────────────────
# ✅ 사이드바 렌더링
# ─────────────────────────────────────────────
def render_sidebar(active=None):
    email = get_current_user()
    if not email:
        return

    st.sidebar.markdown("### 📍 메뉴")
    st.sidebar.markdown(f"현재 계정: `{email}`")

    # ───── Crew 메뉴 ─────
    with st.sidebar.expander("🧑‍✈️ Crew", expanded=True):
        st.page_link("pages/01_issueform.py", label="📝 장애 접수")

    # ───── 기술지원 전용 메뉴 ─────
    if email in ALLOWED_EMAILS:
        st.sidebar.divider()
        st.sidebar.markdown("### 🧰 기술지원")
        st.page_link("app.py", label="📊 Dashboard")
        st.page_link("pages/02_issue_manage.py", label="🧾 장애 처리")
        st.page_link("pages/daily_report.py", label="📅 Daily")

        # 로그아웃 버튼
        if st.sidebar.button("🚪 로그아웃"):
            clear_localstorage()
            st.session_state.pop("user_email", None)
            st.success("로그아웃 완료. 페이지를 새로고침해주세요.")
    else:
        st.sidebar.divider()
        st.sidebar.info("🔒 기술지원 전용 메뉴는 접근 권한이 없습니다.")
