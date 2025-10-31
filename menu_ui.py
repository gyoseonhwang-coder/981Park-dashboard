import streamlit as st

# ─────────────────────────────────────────────
# Streamlit 기본 사이드바 탐색 메뉴 비활성화
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* 기본 탐색 메뉴 숨기기 */
[data-testid="stSidebarNav"] {display:none !important;}
[data-testid="stSidebarNav"] + div {display:none !important;}
section[data-testid="stSidebar"] {width:0 !important; min-width:0 !important; overflow:hidden !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 커스텀 햄버거 메뉴 렌더러
# ─────────────────────────────────────────────
def render_menu(active: str = "Dashboard"):
    """좌측 상단 햄버거 + 메뉴창 렌더링"""
    if "menu_open" not in st.session_state:
        st.session_state.menu_open = False

    # ✅ CSS : 버튼과 패널을 Streamlit 상위 레이어에 고정
    st.markdown("""
    <style>
    #custom-menu-btn {
        position: fixed;
        top: 16px;
        left: 18px;
        z-index: 99999;
        background: none;
        border: none;
        color: #2c7be5;
        font-size: 26px;
        cursor: pointer;
    }
    .custom-sidebar {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: 240px;
        background: linear-gradient(180deg, #1e293b, #334155);
        color: #fff;
        padding: 70px 20px 20px 20px;
        box-shadow: 3px 0 10px rgba(0,0,0,0.3);
        border-right: 1px solid rgba(255,255,255,0.1);
        transform: translateX(-260px);
        transition: transform 0.35s ease;
        z-index: 99998;
    }
    .custom-sidebar.open {
        transform: translateX(0);
    }
    .menu-item {
        font-size: 17px;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.25s;
    }
    .menu-item:hover {
        background: rgba(255,255,255,0.15);
    }
    .menu-active {
        background: rgba(255,255,255,0.25);
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # ✅ JS : 메뉴 토글 및 페이지 이동
    st.markdown("""
    <script>
    function toggleMenu() {
        const panel = window.parent.document.querySelector('.custom-sidebar');
        if (panel) {
            panel.classList.toggle('open');
        }
    }
    function navSelect(target) {
        const url = new URL(window.location);
        url.searchParams.set('nav', target);
        window.history.replaceState({}, '', url);
        window.parent.postMessage({nav: target}, '*');
    }
    </script>
    """, unsafe_allow_html=True)

    # ✅ 버튼과 패널 삽입
    menu_html = f"""
    <button id="custom-menu-btn" onclick="toggleMenu()">☰</button>
    <div class="custom-sidebar {'open' if st.session_state.menu_open else ''}">
        <div class="menu-item {'menu-active' if active == 'Dashboard' else ''}" 
             onclick="navSelect('Dashboard')">📊 Dashboard</div>
        <div class="menu-item {'menu-active' if active == 'IssueForm' else ''}" 
             onclick="navSelect('IssueForm')">🧾 장애 접수</div>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 네비게이션 상태 관리
# ─────────────────────────────────────────────
def read_nav_target(default: str = "Dashboard") -> str:
    """현재 nav 파라미터 읽기"""
    try:
        nav = st.query_params.get("nav") if hasattr(st, "query_params") else None
        if isinstance(nav, list):
            nav = nav[0]
        if nav in ("Dashboard", "IssueForm"):
            return nav
        return default
    except Exception:
        return default
