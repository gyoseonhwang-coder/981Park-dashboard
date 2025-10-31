import streamlit as st

def render_menu(active: str = "Dashboard"):
    """981파크 커스텀 햄버거 메뉴"""

    # Streamlit 기본 탐색 메뉴 숨김
    st.markdown("""
    <style>
    [data-testid="stSidebarNav"], [data-testid="stSidebarNav"] + div {
        display:none !important;
    }
    section[data-testid="stSidebar"] {
        width:0 !important; min-width:0 !important; overflow:hidden !important;
    }
    div.block-container {
        padding-top: 0rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # HTML 콘텐츠 정의
    html_code = f"""
    <style>
    #menu-btn {{
        position: fixed;
        top: 14px;
        left: 20px;
        font-size: 28px;
        color: #2563eb;
        background: none;
        border: none;
        cursor: pointer;
        z-index: 9999;
    }}
    .menu-panel {{
        position: fixed;
        top: 0;
        left: 0;
        width: 240px;
        height: 100%;
        background: linear-gradient(180deg, #1e293b, #334155);
        color: white;
        transform: translateX(-260px);
        transition: transform 0.35s ease-in-out;
        z-index: 9998;
        padding: 70px 20px 20px 20px;
        box-shadow: 3px 0 10px rgba(0,0,0,0.3);
        border-right: 1px solid rgba(255,255,255,0.1);
    }}
    .menu-panel.open {{
        transform: translateX(0);
    }}
    .menu-item {{
        padding: 10px 14px;
        border-radius: 8px;
        margin: 8px 0;
        font-size: 17px;
        cursor: pointer;
        transition: all 0.25s;
    }}
    .menu-item:hover {{
        background: rgba(255,255,255,0.15);
    }}
    .menu-active {{
        background: rgba(255,255,255,0.25);
        font-weight: bold;
    }}
    .overlay {{
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.3);
        z-index: 9997;
        display: none;
    }}
    .overlay.show {{
        display: block;
    }}
    </style>

    <button id="menu-btn" onclick="toggleMenu()">☰</button>
    <div class="overlay" onclick="toggleMenu()"></div>
    <div class="menu-panel" id="menu-panel">
        <div class="menu-item {'menu-active' if active == 'Dashboard' else ''}" onclick="navSelect('Dashboard'); toggleMenu()">📊 Dashboard</div>
        <div class="menu-item {'menu-active' if active == 'IssueForm' else ''}" onclick="navSelect('IssueForm'); toggleMenu()">🧾 장애 접수</div>
    </div>

    <script>
    function toggleMenu() {{
        const panel = document.getElementById('menu-panel');
        const overlay = document.querySelector('.overlay');
        panel.classList.toggle('open');
        overlay.classList.toggle('show');
    }}
    function navSelect(target) {{
        const url = new URL(window.location);
        url.searchParams.set('nav', target);
        window.history.replaceState({{}}, '', url);
        window.parent.postMessage({{nav: target}}, '*');
    }}
    </script>
    """

    # ⛳ HTML을 실제 페이지 최상단에 렌더링
    st.html(html_code, height=0)


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
