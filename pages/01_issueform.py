import requests
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
from menu_ui import render_sidebar

# ─────────────────────────────────────────────
# 접수장애 웹훅 전송
# ─────────────────────────────────────────────


def send_google_chat_alert(form_data: dict):
    """Google Chat Webhook 알림 (981Park 장애 접수용)"""
    import requests
    from datetime import datetime, timezone, timedelta
    import streamlit as st

    WEBHOOK_URL = (
        "https://chat.googleapis.com/v1/spaces/AAAA--bBVFA/messages"
        "?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"
        "&token=KTqHuz3sZhnrpJXkFyo8__ZNNytvsZehQoRcluPCzVY"
    )

    now_kst = datetime.now(timezone(timedelta(hours=9)))
    formatted_time = now_kst.strftime("%Y-%m-%d %H:%M")

    # 긴급 여부
    is_urgent = form_data.get("긴급", False)

    # 카드 헤더 설정
    if is_urgent:
        header_color = "#D93025"
        header_title = "🔥 긴급 장애 접수"
    else:
        header_color = "#1A73E8"
        header_title = "📋 일반 장애 접수"

    # ✅ 1차 시도: 카드 메시지
    card_message = {
        "cardsV2": [
            {
                "cardId": "981park-issue",
                "card": {
                    "header": {
                        "title": header_title,
                        "subtitle": f"{formatted_time}",
                        "imageUrl": "https://cdn-icons-png.flaticon.com/512/906/906343.png",
                        "imageType": "CIRCLE",
                        "backgroundColor": header_color
                    },
                    "sections": [
                        {
                            "widgets": [
                                {"decoratedText": {
                                    "startIcon": {"knownIcon": "STAR"},
                                    "topLabel": "우선순위",
                                    "text": "🔥 긴급 장애" if form_data.get("긴급", False) else "✅ 일반 장애"
                                }},
                                {"decoratedText": {
                                    "startIcon": {"knownIcon": "PERSON"},
                                    "topLabel": "작성자",
                                    "text": form_data.get("작성자", "-")
                                }},
                                {"decoratedText": {
                                    "startIcon": {"knownIcon": "LOCATION_ON"},
                                    "topLabel": "포지션 / 위치",
                                    "text": f"{form_data.get('포지션', '-')} → {form_data.get('위치', '-')}"
                                }},
                                {"decoratedText": {
                                    "startIcon": {"knownIcon": "BUILD"},
                                    "topLabel": "설비명 / 세부기기",
                                    "text": f"{form_data.get('설비명', '-')} → {form_data.get('세부장치', '-')}"
                                }},
                                {"decoratedText": {
                                    "startIcon": {"knownIcon": "WARNING"},
                                    "topLabel": "장애유형",
                                    "text": form_data.get("장애유형", "-")
                                }},
                                {"decoratedText": {
                                    "startIcon": {"knownIcon": "DESCRIPTION"},
                                    "topLabel": "장애내용",
                                    "text": form_data.get("장애내용", "-")
                                }},
                                {"decoratedText": {
                                    "startIcon": {"knownIcon": "CLOCK"},
                                    "topLabel": "접수시각 (KST)",
                                    "text": formatted_time
                                }},
                            ]
                        }
                    ]
                }
            }
        ]
    }

    is_urgent = form_data.get("긴급", False)

    if is_urgent:
        alert_header = "🚨*[긴급] 장애가 접수되었습니다!*🚨"
        alert_bar = "━━━━━━━━━━━━🔥━━━━━━━━━━━━"
    else:
        alert_header = "⚙️ *[일반] 장애가 접수되었습니다!*"
        alert_bar = "━━━━━━━━━━━━🔵━━━━━━━━━━━━"
    text_message = {
        "text": (
            f"{alert_header}\n"
            f"{alert_bar}\n"
            f"👤 작성자: {form_data.get('작성자', '-')}\n"
            f"📍 포지션: {form_data.get('포지션', '-')}\n"
            f"🚩 위치: {form_data.get('위치', '-')}\n"
            f"⚙️ 설비명: {form_data.get('설비명', '-')}\n"
            f"⚙️ 세부장치: {form_data.get('세부장치', '-')}\n"
            f"🚨 장애유형: {form_data.get('장애유형', '-')}\n"
            f"📝 내용: {form_data.get('장애내용', '-')}\n"
            f"🕒 접수시각: {formatted_time}\n"
            f"{alert_bar}\n"
        )
    }

    try:
        # 1️⃣ 카드형 메시지 전송
        resp = requests.post(WEBHOOK_URL, json=card_message, timeout=10)
        st.write("📡 Webhook 응답 코드:", resp.status_code)
        st.write("📩 Webhook 응답 내용:", resp.text)

        # 2️⃣ 실패 시 fallback
        if resp.status_code != 200:
            st.warning("⚠️ 카드 전송 실패 → 텍스트 메시지로 대체 전송 중...")
            resp_fallback = requests.post(
                WEBHOOK_URL, json=text_message, timeout=10)
            st.write("📩 fallback 응답:", resp_fallback.text)

            if resp_fallback.status_code == 200:
                st.toast("✅ Google Chat 알림 (텍스트) 전송 완료", icon="💬")
            else:
                st.error(f"❌ Google Chat 알림 실패: {resp_fallback.text}")
        else:
            st.toast("✅ Google Chat 알림 (카드) 전송 완료", icon="💬")

    except Exception as e:
        st.error(f"❌ Webhook 전송 중 오류: {e}")


st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none !important;}
section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="🧾 981Park 장애 접수",
                   layout="wide", initial_sidebar_state="expanded")
render_sidebar(active="IssueForm")

try:
    creds_info = st.secrets["google_service_account"]
except Exception as e:
    st.error("🔐 `st.secrets['google_service_account']`가 없습니다. "
             "`.streamlit/secrets.toml`에 서비스계정 JSON을 넣어주세요.")
    st.stop()

creds = Credentials.from_service_account_info(
    creds_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]
)
gc = gspread.authorize(creds)

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_MAPPING = "설비매핑"
SHEET_LOG = "접수내용"


@st.cache_data(ttl=300)
def load_mapping_sheet():
    """설비매핑 전체를 DataFrame으로 로드"""
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_MAPPING)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df


@st.cache_data(ttl=30)
def get_recent_issues_by_position(position_name: str) -> pd.DataFrame:
    """포지션별 미조치/점검중 최근 10건"""
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(data[1:], columns=data[0])

    if "포지션" not in df.columns:
        return pd.DataFrame()

    df = df[df["포지션"] == position_name].copy()
    if "접수처리" in df.columns:
        df = df[df["접수처리"].isin(["접수중", "점검중"])]
    if "종결" in df.columns:
        df = df[df["종결"] != "종결"]

    if "날짜" in df.columns:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    df = df.sort_values("날짜", ascending=False).head(10)

    for col in ["위치", "설비명", "세부장치", "장애내용", "작성자"]:
        if col not in df.columns:
            df[col] = ""
    return df[["날짜", "위치", "설비명", "세부장치", "장애내용", "작성자"]].fillna("")


st.title("🧾 981Park 장애 접수")

df_map = load_mapping_sheet()
col_form, col_recent = st.columns([1.3, 0.9], gap="large")

with col_form:
    st.subheader("📋 장애 접수 등록")

    for key in ["position", "location", "equipment", "detail", "issue", "reporter", "desc", "urgent"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key != "urgent" else False

    positions = sorted(df_map["포지션"].dropna().unique(
    )) if not df_map.empty and "포지션" in df_map.columns else []
    st.session_state.position = st.selectbox(
        "📍 포지션", [""] + positions, index=0)

    if st.session_state.position:
        locations = sorted(
            df_map[df_map["포지션"] ==
                   st.session_state.position]["위치"].dropna().unique()
        ) if "위치" in df_map.columns else []
    else:
        locations = []
    st.session_state.location = st.selectbox(
        "🏗️ 위치", [""] + locations, index=0)

    if st.session_state.position and st.session_state.location:
        if all(col in df_map.columns for col in ["포지션", "위치", "설비명"]):
            equipments = sorted(
                df_map[
                    (df_map["포지션"] == st.session_state.position) &
                    (df_map["위치"] == st.session_state.location)
                ]["설비명"].dropna().unique()
            )
        else:
            equipments = []
    else:
        equipments = []
    st.session_state.equipment = st.selectbox(
        "⚙️ 설비명", [""] + equipments, index=0)

    if st.session_state.equipment:
        row = df_map[
            (df_map.get("포지션") == st.session_state.position) &
            (df_map.get("위치") == st.session_state.location) &
            (df_map.get("설비명") == st.session_state.equipment)
        ]
        if not row.empty:
            detail_start, detail_end = 3, 33
            details = [d for d in row.iloc[0, detail_start:detail_end].tolist(
            ) if d and str(d).strip() != ""]
        else:
            details = []
    else:
        details = []
    st.session_state.detail = st.selectbox("🔩 세부기기", [""] + details, index=0)

    try:
        issue_start, issue_end = 33, 39
        if not df_map.empty and df_map.shape[1] >= issue_end:
            vals = df_map.iloc[:,
                               issue_start:issue_end].values.flatten().tolist()
            issue_types = sorted(
                {v for v in vals if v and str(v).strip() != ""})
        else:
            issue_types = []
    except Exception:
        issue_types = []
    st.session_state.issue = st.selectbox(
        "🚨 장애유형", [""] + issue_types, index=0)

    st.session_state.reporter = st.text_input(
        "👤 작성자 이름", st.session_state.reporter or "")
    st.session_state.desc = st.text_area(
        "📝 장애 내용 (상세히 작성)", st.session_state.desc or "")
    st.session_state.urgent = st.checkbox(
        "🚨 긴급 장애 (즉시 대응 필요)", value=bool(st.session_state.urgent))

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submit = st.button("✅ 장애 접수 등록", use_container_width=True)

    # 전송 로직
    if submit:
        if not (st.session_state.position and st.session_state.location and
                st.session_state.equipment and st.session_state.reporter and st.session_state.desc):
            st.warning("⚠️ 필수 항목(포지션, 위치, 설비명, 작성자, 내용)을 모두 입력해주세요.")
        else:
            try:
                # ✅ Google Sheet 로드
                sh = gc.open(SPREADSHEET_NAME)
                log_sheet = sh.worksheet(SHEET_LOG)

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                new_row = [
                    "긴급" if st.session_state.urgent else "일반",
                    now,
                    st.session_state.reporter,
                    st.session_state.position,
                    st.session_state.location,
                    st.session_state.equipment,
                    st.session_state.detail,
                    st.session_state.issue,
                    st.session_state.desc,
                    "접수중", "", "", "", "", ""
                ]

                # ✅ 시트에 장애 행 추가
                log_sheet.append_row(
                    new_row, value_input_option="USER_ENTERED")

                # ✅ Webhook 알림용 데이터 구성
                form_payload = {
                    "작성자": st.session_state.reporter,
                    "포지션": st.session_state.position,
                    "위치": st.session_state.location,
                    "설비명": st.session_state.equipment,
                    "세부장치": st.session_state.detail,
                    "장애유형": st.session_state.issue,
                    "장애내용": st.session_state.desc,
                    "긴급": st.session_state.urgent,
                }

                # ✅ Webhook 호출
                st.toast("🚀 Google Chat 알림 전송 중...", icon="💬")
                send_google_chat_alert(form_payload)
                st.toast("✅ Google Chat 알림 완료", icon="✅")

                # 🎉 팝업 (장애 접수 완료 안내)
                popup = st.empty()
                with popup.container():
                    st.markdown(
                        """
                        <div style="
                            position: fixed;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            background: white;
                            padding: 40px;
                            border-radius: 12px;
                            box-shadow: 0 4px 25px rgba(0,0,0,0.2);
                            text-align: center;
                            z-index: 9999;
                            width: 400px;">
                            <h3>✅ 장애 접수 완료</h3>
                            <p>장애 접수가 정상적으로 등록되었습니다.</p>
                            <p><b>해당 포지션의 현황은 오른쪽 [📌 미조치 장애 현황]</b><br>에서 확인 가능합니다.</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # 잠시 대기 후 화면 리셋
                time.sleep(2.0)
                popup.empty()
                st.rerun()

            except Exception as e:
                st.error(f"❌ 전송 중 오류 발생: {e}")


with col_recent:
    st.subheader("📌 미조치 / 점검중 장애 현황")

    if st.session_state.position:
        df_recent = get_recent_issues_by_position(st.session_state.position)
        if not df_recent.empty:
            for _, row in df_recent.iterrows():
                date_str = ""
                if pd.notna(row["날짜"]):
                    try:
                        date_str = row["날짜"].strftime("%y.%m.%d %H:%M")
                    except Exception:
                        date_str = str(row["날짜"])
                else:
                    date_str = "—"

                st.markdown(
                    f"""
                    <div style="
                        background-color: rgba(255,255,255,0.9);
                        padding:12px;
                        border-radius:10px;
                        box-shadow:0 2px 6px rgba(0,0,0,0.08);
                        margin-bottom:10px;">
                        <b>📅 {date_str}</b><br>
                        <b>위치:</b> {row['위치']}<br>
                        <b>설비:</b> {row['설비명']} | <b>세부:</b> {row['세부장치']}<br>
                        <b>내용:</b> {row['장애내용']}<br>
                        <span style="color:#666;">접수자: {row['작성자']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("✅ 현재 미조치 또는 점검중 장애가 없습니다.")
    else:
        st.info("🔎 포지션을 선택하면 해당 포지션의 최근 장애 현황이 표시됩니다.")

st.caption("© 2025 981Park Technical Support Team — Streamlit 장애 접수 및 실시간 현황")
