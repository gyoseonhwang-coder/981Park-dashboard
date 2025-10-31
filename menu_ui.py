import streamlit as st

# ─────────────────────────────────────────────
# Streamlit 기본 사이드바 비활성화 (햄버거 메뉴만 사용)
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* 기본 사이드바 탐색 메뉴 숨기기 */
[data-testid="stSidebarNav"] {display: none !important;}
[data-testid="stSidebarNav"] + div {display: none !important;}
section[data-testid="stSidebar"] {width: 0; min-width: 0;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 햄버거 메뉴 + 사이드 메뉴 구성
# ─────────────────────────────────────────────
def render_menu(active: str = "Dashboard"):
    """햄버거 메뉴 렌더링 (Dashboard / IssueForm 전환)"""
    if "menu_open" not in st.session_state:
        st.session_state.menu_open = False
    if "current_page" not in st.session_state:
        st.session_state.current_page = active

    # CSS
    st.markdown("""
    <style>
    #menu-btn {
        font-size: 26px;
        cursor: pointer;
        position: fixed;
        top: 18px;
        left: 25px;
        z-index: 9999;
        color: #2c7be5;
        background: none;
        border: none;
    }
    .sidebar-panel {
        position: fixed;
        top: 0; left: 0;
        width: 240px; height: 100%;
        background: linear-gradient(180deg, #1e293b, #334155);
        color: white;
        padding: 70px 20px 20px 20px;
        transform: translateX(-260px);
        transition: transform 0.35s ease-in-out;
        z-index: 9998;
        box-shadow: 2px 0 10px rgba(0,0,0,0.3);
    }
    .sidebar-panel.open { transform: translateX(0); }
    .menu-item {
        font-size: 17px;
        margin: 14px 0;
        padding: 10px 16px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.25s ease;
    }
    .menu-item:hover { background: rgba(255,255,255,0.15); }
    .menu-active { background: rgba(255,255,255,0.25); font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    # JS
    st.markdown("""
    <script>
    function toggleMenu() {
        const panel = window.parent.document.querySelector('.sidebar-panel');
        if (!panel) return;
        panel.classList.toggle('open');
    }
    function navSelect(target) {
        const url = new URL(window.location);
        url.searchParams.set('nav', target);
        window.history.replaceState({}, '', url);
        window.parent.postMessage({nav: target}, '*');
    }
    </script>
    """, unsafe_allow_html=True)

    # 햄버거 버튼
    st.markdown('<button id="menu-btn" onclick="toggleMenu()">☰</button>',
                unsafe_allow_html=True)

    # 메뉴 패널
    menu_html = f"""
    <div class="sidebar-panel {'open' if st.session_state.menu_open else ''}">
        <div class="menu-item {'menu-active' if active == 'Dashboard' else ''}" 
             onclick="navSelect('Dashboard')">📊 Dashboard</div>
        <div class="menu-item {'menu-active' if active == 'IssueForm' else ''}" 
             onclick="navSelect('IssueForm')">🧾 장애 접수</div>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 현재 페이지 네비게이션 판별
# ─────────────────────────────────────────────
def read_nav_target(default: str = "Dashboard") -> str:
    """현재 nav 파라미터 읽기"""
    nav = st.query_params.get("nav") if hasattr(st, "query_params") else None
    if isinstance(nav, list):
        nav = nav[0]
    if nav in ("Dashboard", "IssueForm"):
        return nav
    return default
