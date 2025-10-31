import streamlit as st

# ─────────────────────────────────────────────
# Streamlit 기본 사이드바 숨김
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"], [data-testid="stSidebarNav"] + div {
  display:none !important;
}
section[data-testid="stSidebar"] {
  width:0 !important; min-width:0 !important; overflow:hidden !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 커스텀 햄버거 메뉴
# ─────────────────────────────────────────────
def render_menu(active: str = "Dashboard"):
    """좌측 상단 햄버거 메뉴 + 네비게이션"""
    st.markdown("""
    <style>
    /* 🔹 페이지 전체 상단 여백 제거 */
    div.block-container {
        padding-top: 0rem !important;
    }

    /* 🔹 햄버거 버튼 */
    #custom-menu-btn {
        position: fixed;
        top: 12px;
        left: 18px;
        z-index: 10001;
        background: none;
        border: none;
        color: #2563eb;
        font-size: 26px;
        cursor: pointer;
    }

    /* 🔹 메뉴 패널 */
    .custom-sidebar {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: 240px;
        background: linear-gradient(180deg, #1e293b, #334155);
        color: #fff;
        padding: 70px 20px 20px 20px;
        transform: translateX(-260px);
        transition: transform 0.35s ease;
        box-shadow: 3px 0 10px rgba(0,0,0,0.3);
        z-index: 10000;
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    .custom-sidebar.open { transform: translateX(0); }

    /* 🔹 메뉴 아이템 */
    .menu-item {
        font-size: 17px;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.25s;
    }
    .menu-item:hover { background: rgba(255,255,255,0.15); }
    .menu-active { background: rgba(255,255,255,0.25); font-weight: bold; }

    /* 🔹 오버레이 영역 */
    .overlay {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.3);
        z-index: 9999;
        display: none;
    }
    .overlay.show { display: block; }
    </style>
    """, unsafe_allow_html=True)

    # JavaScript
    st.markdown("""
    <script>
    function toggleMenu() {
        const sidebar = window.parent.document.querySelector('.custom-sidebar');
        const overlay = window.parent.document.querySelector('.overlay');
        if (sidebar && overlay) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
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

    # HTML 버튼 + 메뉴 삽입
    menu_html = f"""
    <div class="overlay" onclick="toggleMenu()"></div>
    <button id="custom-menu-btn" onclick="toggleMenu()">☰</button>
    <div class="custom-sidebar">
        <div class="menu-item {'menu-active' if active == 'Dashboard' else ''}" 
             onclick="navSelect('Dashboard'); toggleMenu()">📊 Dashboard</div>
        <div class="menu-item {'menu-active' if active == 'IssueForm' else ''}" 
             onclick="navSelect('IssueForm'); toggleMenu()">🧾 장애 접수</div>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 네비게이션 판별
# ─────────────────────────────────────────────
def read_nav_target(default: str = "Dashboard") -> str:
    try:
        nav = st.query_params.get("nav") if hasattr(st, "query_params") else None
        if isinstance(nav, list):
            nav = nav[0]
        if nav in ("Dashboard", "IssueForm"):
            return nav
        return default
    except Exception:
        return default
