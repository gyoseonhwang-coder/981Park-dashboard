import streamlit as st

# ─────────────────────────────────────────────
# Streamlit 기본 사이드바 탐색 메뉴 비활성화
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"], [data-testid="stSidebarNav"] + div {display:none !important;}
section[data-testid="stSidebar"] {width:0 !important; min-width:0 !important; overflow:hidden !important;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 커스텀 햄버거 메뉴 렌더링
# ─────────────────────────────────────────────
def render_menu(active: str = "Dashboard"):
    """좌측 상단 햄버거 + 메뉴창 렌더링 (Streamlit 1.50 호환)"""
    if "menu_open" not in st.session_state:
        st.session_state.menu_open = False

    # ✅ 메뉴 스타일 (iframe-safe)
    st.markdown("""
    <style>
    /* 햄버거 버튼 */
    button[data-testid="hamburger-menu"] {
        display:none;
    }
    div#custom-menu {
        position: fixed;
        top: 16px;
        left: 20px;
        z-index: 9999;
        font-size: 26px;
        cursor: pointer;
        color: #2c7be5;
        background: none;
        border: none;
    }
    div#custom-menu:hover {
        color: #1d4ed8;
    }

    /* 사이드 패널 */
    div#custom-sidebar {
        position: fixed;
        top: 0;
        left: 0;
        height: 100%;
        width: 250px;
        background: linear-gradient(180deg, #1e293b, #334155);
        color: white;
        padding: 70px 24px 24px 24px;
        box-shadow: 3px 0 12px rgba(0,0,0,0.3);
        border-right: 1px solid rgba(255,255,255,0.1);
        transform: translateX(-270px);
        transition: transform 0.35s ease-in-out;
        z-index: 9998;
    }
    div#custom-sidebar.open {
        transform: translateX(0);
    }
    .menu-item {
        font-size: 17px;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 10px 0;
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

    # ✅ JavaScript 코드 (전역 적용)
    js_code = """
    <script>
    function toggleMenu() {
        const sidebar = window.parent.document.getElementById('custom-sidebar');
        if (sidebar) {
            sidebar.classList.toggle('open');
        }
    }
    function navSelect(target) {
        const url = new URL(window.location);
        url.searchParams.set('nav', target);
        window.history.replaceState({}, '', url);
        window.parent.postMessage({nav: target}, '*');
        const sidebar = window.parent.document.getElementById('custom-sidebar');
        if (sidebar) sidebar.classList.remove('open');
    }
    </script>
    """
    st.components.v1.html(js_code, height=0)

    # ✅ HTML 코드 삽입
    html_menu = f"""
    <div id="custom-menu" onclick="toggleMenu()">☰</div>
    <div id="custom-sidebar" class="{'open' if st.session_state.menu_open else ''}">
        <div class="menu-item {'menu-active' if active == 'Dashboard' else ''}" onclick="navSelect('Dashboard')">📊 Dashboard</div>
        <div class="menu-item {'menu-active' if active == 'IssueForm' else ''}" onclick="navSelect('IssueForm')">🧾 장애 접수</div>
    </div>
    """
    st.components.v1.html(html_menu, height=0)


# ─────────────────────────────────────────────
# 네비게이션 상태 관리
# ─────────────────────────────────────────────
def read_nav_target(default: str = "Dashboard") -> str:
    """현재 nav 파라미터 읽기"""
    try:
        nav = st.query_params.get("nav") if hasattr(
            st, "query_params") else None
        if isinstance(nav, list):
            nav = nav[0]
        if nav in ("Dashboard", "IssueForm"):
            return nav
        return default
    except Exception:
        return default
