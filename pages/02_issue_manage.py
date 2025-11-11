import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
from menu_ui import render_sidebar, get_current_user, AUTHORIZED_USERS
import html


st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

email, name = get_current_user()

if not email or email.strip().lower() not in [e.lower() for e in AUTHORIZED_USERS]:
    st.error("🚫 이 메뉴는 기술지원 전용입니다.")
    st.stop()

def move_issue_to_position(payload, gc):
    """981파크 장애관리 - 접수내용 → 포지션 시트 이동"""
    try:
        SPREADSHEET_NAME = "981파크 장애관리"
        sh = gc.open(SPREADSHEET_NAME)

        position = payload.get("포지션", "").strip()
        if not position:
            st.warning("⚠️ 포지션 정보가 없어 포지션 시트로 이동하지 못했습니다.")
            return

        try:
            target_ws = sh.worksheet(position)
        except Exception:
            target_ws = sh.add_worksheet(title=position, rows="500", cols="20")
            headers = [
                "우선순위", "날짜", "작성자", "포지션", "위치", "설비",
                "구분", "장애유형", "장애내용", "점검자", "점검일자",
                "점검내용", "비고", "중단설비", "완결"
            ]
            target_ws.append_row(headers)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [
            "긴급" if payload.get("긴급") else "일반",
            now,
            payload.get("작성자", ""),
            payload.get("포지션", ""),
            payload.get("위치", ""),
            payload.get("설비명", ""),
            payload.get("세부장치", ""),
            payload.get("장애유형", ""),
            payload.get("장애내용", ""),
            payload.get("점검자", ""),
            "", "", "", "",
            "점검중"
        ]

        target_ws.append_row(new_row, value_input_option="USER_ENTERED")
        st.toast(f"📤 '{position}' 시트로 자동 이동 완료", icon="✅")

    except Exception as e:
        st.error(f"❌ 포지션 시트 이동 중 오류 발생: {e}")

st.set_page_config(page_title="🧰 장애 처리", layout="wide")

st.markdown("""
<style>
/* 기본: 안전한 상단 여백 (데스크탑 기준) */
:root { --top-gap: 48px; } /* 필요시 px값 조절: 40~80 권장 */

div[data-testid="stAppViewContainer"] > .main > div.block-container,
div[data-testid="stAppViewContainer"] .main .block-container,
main .block-container,
div.block-container {
    padding-top: var(--top-gap) !important;
    margin-top: 0 !important;
}

/* 타이틀(헤더) 마진/라인하이트 보정 */
div.block-container h1, div.block-container h2 {
    margin-top: 0 !important;
    padding-top: 0 !important;
    line-height: 1.05 !important;
}

/* 상단 툴바(menu)가 겹치는 경우 z-index 보정(툴바가 타이틀 위에 있을 때 비활성화 가능) */
header, [data-testid="stToolbar"] {
    position: relative;
    z-index: 1000;
}

/* 작은 화면(모바일/좁은) 에선 여백 축소 */
@media (max-width: 900px) {
  :root { --top-gap: 20px; }
  div.block-container h1 { font-size: 1.35rem !important; }
}

/* 만약 기존 JS/다른 스타일이 계속 0으로 덮어쓴다면, 마지막에 다시 강제 적용 */
</style>

<script>
(function(){
  function ensureTopGap(){
    try {
      const gap = getComputedStyle(document.documentElement).getPropertyValue('--top-gap') || '48px';
      const selectors = [
        'div[data-testid="stAppViewContainer"] > .main > div.block-container',
        'div[data-testid="stAppViewContainer"] .main .block-container',
        'main .block-container',
        'div.block-container'
      ];
      selectors.forEach(s => {
        const el = document.querySelector(s);
        if (el) {
          el.style.paddingTop = gap;
        }
      });
    } catch(e){ console && console.warn && console.warn("ensureTopGap err", e); }
  }
  // 즉시 적용 + 지연 적용(동적 DOM 대비)
  ensureTopGap();
  setTimeout(ensureTopGap, 150);
  setTimeout(ensureTopGap, 600);
})();
</script>
""", unsafe_allow_html=True)

render_sidebar(active="IssueManage")

try:
    creds_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    gc = gspread.authorize(creds)
except Exception:
    st.error("🔐 Google 서비스 계정 정보가 누락되었습니다. `.streamlit/secrets.toml`을 확인하세요.")
    st.stop()

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_LOG = "접수내용"

@st.cache_data(ttl=30)
def load_issue_log() -> pd.DataFrame:
    """981파크 장애관리 > 접수내용 시트 전체 로드"""
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(data[1:], columns=data[0])

    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].replace("", "—")

    if "상태" not in df.columns and "접수처리" in df.columns:
        df["상태"] = df["접수처리"]
    df["상태"] = df["상태"].replace({
        "접수중": "미조치(접수중)",
        "점검중": "점검중",
        "완료": "완료"
    })
    return df

st.title("🧰 981Park 장애 처리")
st.caption(f"접속 계정: {email}")

def render_pending_alerts(df, max_items=5, show_details=False):
    """
    상단 알림용 큰 카드 3개 표시. 기본적으로 상세 리스트는 숨김 (show_details=False).
    - df: load_issue_log()로 읽은 DataFrame
    - max_items: 상세 보기 시 최대 표시 건수
    """
    try:
        if df is None or df.empty:
            return

        status_col = None
        for c in ["상태", "접수처리", "접수", "status", "처리상태"]:
            if c in df.columns:
                status_col = c
                break
        if status_col is None:
            for c in df.columns:
                if "접수" in c or "처리" in c or "status" in c.lower():
                    status_col = c
                    break
        if status_col is None:
            return

        mask_pending = df[status_col].astype(str).str.contains(r"접수중|^접수$|접수\b", na=False)
        mask_not_checking = ~df[status_col].astype(str).str.contains("점검중", na=False)
        pending_df = df[mask_pending & mask_not_checking].copy()

        total_pending = len(pending_df)

        import re

        priority_candidates = [c for c in df.columns if re.search(r'우선|priority', str(c), re.I)]
        priority_col = priority_candidates[0] if priority_candidates else None

        urgent_count = 0
        if priority_col and priority_col in pending_df.columns:
            urgent_count = int(pending_df[priority_col].astype(str).str.contains(r'긴급|urgent', na=False).sum())
        else:
            mask_urgent = pending_df.apply(
                lambda row: row.astype(str).str.contains(r'\b긴급\b|\burgent\b', case=False, na=False).any(),
                axis=1
            )
            urgent_count = int(mask_urgent.sum())

        st.markdown(
            """
            <style>
            .pending-card {
                padding:20px 22px;
                border-radius:12px;
                border:1px solid rgba(0,0,0,0.06);
                background: linear-gradient(180deg, #ffffff, #fbfdff);
                box-shadow: 0 6px 18px rgba(29, 41, 58, 0.04);
                margin-bottom:12px;
            }
            .pending-count {
                font-size:26px;
                font-weight:800;
                color:#0b5394;
                margin-top:6px;
            }
            .pending-title { font-size:15px; font-weight:700; color:#2c7be5; }
            .pending-sub { font-size:13px; color:#6b7280; margin-top:6px; }
            .pending-row { gap: 18px; display:flex; align-items:stretch; }
            @media (max-width: 900px) { .pending-row { flex-direction: column; } }
            .pending-list { margin-top:8px; padding-left:6px; }
            .pending-item { margin-bottom:6px; color:#333; }
            </style>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([1,1,2])
        col1.markdown(
            f"""
            <div class="pending-card">
              <div class="pending-title">📥 접수중</div>
              <div class="pending-count">{total_pending}</div>
              <div class="pending-sub">점검 처리되지 않은 장애</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        col2.markdown(
            f"""
            <div class="pending-card">
              <div class="pending-title">🚨 긴급</div>
              <div class="pending-count">{urgent_count}</div>
              <div class="pending-sub">긴급 표기가 된 접수 건수</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if show_details and total_pending > 0:
            date_col = next((c for c in ["날짜", "접수일", "date", "등록일"] if c in df.columns), None)
            if date_col:
                pending_df[date_col] = pd.to_datetime(pending_df[date_col], errors="coerce")
                pending_df = pending_df.sort_values(by=date_col, ascending=False)

            show_df = pending_df.head(max_items)
            if not show_df.empty:
                st.markdown("<div class='pending-list'>", unsafe_allow_html=True)
                for _, r in show_df.iterrows():
                    parts = []
                    if "포지션" in r.index and r.get("포지션"): parts.append(str(r.get("포지션")))
                    elif "위치" in r.index and r.get("위치"): parts.append(str(r.get("위치")))
                    if "설비명" in r.index and r.get("설비명"): parts.append(str(r.get("설비명")))
                    desc = str(r.get("장애내용", "")).strip()
                    date_str = ""
                    if date_col:
                        dt = pd.to_datetime(r.get(date_col), errors="coerce")
                        if not pd.isna(dt):
                            try:
                                date_str = dt.strftime("%m-%d %H:%M")
                            except:
                                date_str = str(r.get(date_col))
                    line = " / ".join(parts) + (" — " + desc if desc else "")
                    if date_str:
                        line = f"{line} ({date_str})"
                    st.markdown(f"<div class='pending-item'>{html.escape(line)}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    except Exception:
        return


st.divider()

df = load_issue_log()

if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

render_pending_alerts(df, max_items=6)

pending = df[df["상태"].isin(["미조치(접수중)", "점검중"])].copy()
pending = pending.sort_values("날짜", ascending=False)

cols_show = [c for c in ["날짜", "포지션", "위치", "설비명", "장애내용", "상태", "점검자"] if c in pending.columns]
st.dataframe(pending[cols_show], use_container_width=True, height=320)

st.divider()

st.markdown("""
<style>
div[data-baseweb="select"] span {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    line-height: 1.5em !important;
}
div.stSelectbox > label > div {
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #222 !important;
    margin-bottom: 6px !important;
}
</style>
""", unsafe_allow_html=True)

row_labels = [f"[{r['상태']}] {r['설비명']} — {r['장애내용']}" for _, r in pending.iterrows()]
selected_label = st.selectbox("📋 처리할 장애 선택", ["선택 안 함"] + row_labels, index=0)

if selected_label == "선택 안 함":
    st.info("📋 위 목록에서 처리할 장애를 선택하세요.")
    st.stop()

selected_index = row_labels.index(selected_label)
issue = pending.iloc[selected_index]

st.markdown("---")
st.markdown(
    f"### 🧩 선택된 장애 — <span style='color:#16a34a;font-weight:600'>{issue.get('포지션', '-')} {issue.get('설비명', '-')}</span>",
    unsafe_allow_html=True
)

담당자 = st.text_input("👷 점검자 이름", issue.get("점검자", ""))
포지션_이동 = st.selectbox(
    "📍 포지션 시트로 이동 (선택 안 함 가능)",
    ["선택 안 함", "Audio/Video", "RACE", "LAB", "운영설비", "충전설비", "정비고", "기타"]
)

ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
match = df[
    (df["작성자"] == issue.get("작성자")) &
    (df["장애내용"] == issue.get("장애내용")) &
    (df["설비명"] == issue.get("설비명"))
]

if match.empty:
    st.error("⚠️ 해당 장애를 시트에서 찾을 수 없습니다.")
    st.stop()

row_index = match.index[0] + 2

if issue.get("상태") == "미조치(접수중)":
    st.info("📩 아직 조치되지 않은 장애입니다. 점검 시작 시 아래 버튼을 클릭하세요.")
    if st.button("🚧 장애 접수 (→ 점검중)", use_container_width=True):
        try:
            ws.update_cell(row_index, 10, "점검중")
            ws.update_cell(row_index, 12, 담당자)
            ws.update_cell(row_index, 11, 포지션_이동 if 포지션_이동 != "선택 안 함" else "")
            
            if 포지션_이동 != "선택 안 함":
                ws.update_cell(row_index, 15, "장애 등록")

                payload = issue.to_dict()
                payload["점검자"] = 담당자
                payload["포지션"] = 포지션_이동
                move_issue_to_position(payload, gc)
            else:
                ws.update_cell(row_index, 15, "")

            st.toast(f"✅ '{issue['설비명']}' 장애가 점검중으로 변경되었습니다.", icon="⚙️")
            with st.spinner("🔄 시트 업데이트 중..."):
                import time
                time.sleep(1.5)
            st.rerun()
        except Exception as e:
            st.error(f"❌ 장애 접수 중 오류 발생: {e}")

elif issue.get("상태") == "점검중":
    st.info("🧰 점검이 완료되면 아래 내용을 입력 후 완료 처리하세요.")
    점검내용 = st.text_area("🔧 점검내용", height=120, placeholder="점검 결과나 조치 내용을 입력하세요.")
    if st.button("✅ 완료 처리 (→ 완료)", use_container_width=True):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.update_cell(row_index, 10, "완료")
            ws.update_cell(row_index, 13, now)
            ws.update_cell(row_index, 14, 점검내용)
            ws.update_cell(row_index, 15, "장애 처리")
            ws.update_cell(row_index, 17, "종결")

            st.toast(f"🎉 '{issue['설비명']}' 장애가 완료 처리되었습니다.", icon="✅")
            with st.spinner("💾 변경 내용 저장 중..."):
                import time
                time.sleep(1.5)
            st.rerun()
        except Exception as e:
            st.error(f"❌ 완료 처리 중 오류: {e}")

else:
    st.info("✅ 이 장애는 이미 완료 상태입니다.")

st.caption("© 2025 981Park Technical Support Team — 기술지원 전용 장애 처리 시스템")
