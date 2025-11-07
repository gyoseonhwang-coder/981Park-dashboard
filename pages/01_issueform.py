# ─────────────────────────────────────────────
# 📦 Imports
# ─────────────────────────────────────────────
import streamlit as st
import pandas as pd
import gspread
import requests
import time
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials
from menu_ui import render_sidebar, get_current_user


# ─────────────────────────────────────────────
# ⚙️ 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="📝 장애 접수", layout="wide")
render_sidebar(active="IssueForm")

email, name = get_current_user()

st.title("🧾 981Park 장애 접수")
st.caption(f"현재 접속 계정: {email or '게스트 (로그인 필요 없음)'}")


# ─────────────────────────────────────────────
# 💬 Google Chat Webhook 전송
# ─────────────────────────────────────────────
def send_google_chat_alert(form_data: dict):
    """981Park 장애 접수용 Google Chat 알림"""
    WEBHOOK_URL = (
        "https://chat.googleapis.com/v1/spaces/AAAA-Dl8vDs/messages"
        "?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"
        "&token=qpitTslB-dlzAaxy3nqBCSfSxOcjm1ly6vYWDTaPRB8"
    )

    now_kst = datetime.now(timezone(timedelta(hours=9)))
    formatted_time = now_kst.strftime("%Y-%m-%d %H:%M")

    urgent = form_data.get("긴급", False)
    header_color = "#D93025" if urgent else "#1A73E8"
    header_title = "🔥 긴급 장애 접수" if urgent else "📋 일반 장애 접수"

    card_msg = {
        "cardsV2": [{
            "cardId": "981park-issue",
            "card": {
                "header": {
                    "title": header_title,
                    "subtitle": formatted_time,
                    "imageUrl": "https://cdn-icons-png.flaticon.com/512/906/906343.png",
                    "imageType": "CIRCLE",
                    "backgroundColor": header_color
                },
                "sections": [{
                    "widgets": [
                        {"decoratedText": {"topLabel": "작성자", "text": form_data.get("작성자", "-")}},
                        {"decoratedText": {"topLabel": "포지션/위치", "text": f"{form_data.get('포지션', '-')}/{form_data.get('위치', '-')}"}},
                        {"decoratedText": {"topLabel": "설비/세부장치", "text": f"{form_data.get('설비명', '-')}/{form_data.get('세부장치', '-')}"}},
                        {"decoratedText": {"topLabel": "장애유형", "text": form_data.get("장애유형", "-")}},
                        {"decoratedText": {"topLabel": "장애내용", "text": form_data.get("장애내용", "-")}},
                        {"decoratedText": {"topLabel": "긴급도", "text": "🔥 긴급" if urgent else "✅ 일반"}},
                        {"decoratedText": {"topLabel": "접수시각", "text": formatted_time}},
                    ]
                }]
            }
        }]
    }

    try:
        resp = requests.post(WEBHOOK_URL, json=card_msg, timeout=10)
        if resp.status_code != 200:
            st.warning(f"⚠️ 카드 전송 실패: {resp.text[:120]}")
            requests.post(WEBHOOK_URL, json={"text": str(form_data)}, timeout=10)
        else:
            st.toast("💬 Google Chat 알림 전송 완료", icon="✅")
    except Exception as e:
        st.error(f"❌ Webhook 전송 오류: {e}")


# ─────────────────────────────────────────────
# 🔐 Google Sheets 인증
# ─────────────────────────────────────────────
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
except Exception as e:
    st.error("🔐 `st.secrets['google_service_account']` 설정이 필요합니다.")
    st.stop()

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_MAPPING = "설비매핑"
SHEET_LOG = "접수내용"


# ─────────────────────────────────────────────
# 📘 데이터 로드
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_mapping_sheet() -> pd.DataFrame:
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_MAPPING)
    data = ws.get_all_values()
    return pd.DataFrame(data[1:], columns=data[0]) if data else pd.DataFrame()


@st.cache_data(ttl=30)
def get_recent_issues_by_position(position: str) -> pd.DataFrame:
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    if "포지션" not in df.columns:
        return pd.DataFrame()

    df = df[df["포지션"] == position]
    df = df[df["접수처리"].isin(["접수중", "점검중"])]
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.sort_values("날짜", ascending=False).head(10)
    return df[["날짜", "위치", "설비명", "세부장치", "장애내용", "작성자"]].fillna("")


# ─────────────────────────────────────────────
# 🧩 UI 구성
# ─────────────────────────────────────────────
df_map = load_mapping_sheet()

col_form, col_recent = st.columns([1.3, 0.9])

with col_form:
    st.subheader("📋 장애 접수 등록")

    # 폼 초기화
    fields = ["position", "location", "equipment", "detail", "issue", "reporter", "desc", "urgent"]
    for f in fields:
        if f not in st.session_state:
            st.session_state[f] = "" if f != "urgent" else False

    # 선택 항목
    positions = sorted(df_map["포지션"].dropna().unique()) if "포지션" in df_map.columns else []
    st.session_state.position = st.selectbox("📍 포지션", [""] + positions, index=0)

    if st.session_state.position:
        locations = sorted(df_map[df_map["포지션"] == st.session_state.position]["위치"].dropna().unique())
    else:
        locations = []
    st.session_state.location = st.selectbox("🏗️ 위치", [""] + locations, index=0)

    if st.session_state.location:
        equipments = sorted(
            df_map[
                (df_map["포지션"] == st.session_state.position)
                & (df_map["위치"] == st.session_state.location)
            ]["설비명"].dropna().unique()
        )
    else:
        equipments = []
    st.session_state.equipment = st.selectbox("⚙️ 설비명", [""] + equipments, index=0)

    if st.session_state.equipment:
        row = df_map[
            (df_map["포지션"] == st.session_state.position)
            & (df_map["위치"] == st.session_state.location)
            & (df_map["설비명"] == st.session_state.equipment)
        ]
        details = [v for v in row.iloc[0, 3:33].tolist() if v.strip()] if not row.empty else []
    else:
        details = []
    st.session_state.detail = st.selectbox("🔩 세부기기", [""] + details, index=0)

    issue_types = sorted(
        {v for v in df_map.iloc[:, 33:39].values.flatten().tolist() if v.strip()}
    ) if not df_map.empty else []
    st.session_state.issue = st.selectbox("🚨 장애유형", [""] + issue_types, index=0)

    # 작성자, 내용
    st.session_state.reporter = st.text_input("👤 작성자 이름", value=st.session_state.reporter or "")
    st.session_state.desc = st.text_area("📝 장애 내용 (상세히 작성)", value=st.session_state.desc or "")
    st.session_state.urgent = st.checkbox("🚨 긴급 장애 (즉시 대응 필요)", value=st.session_state.urgent)

    if st.button("✅ 장애 접수 등록", use_container_width=True):
        if not (st.session_state.position and st.session_state.location and st.session_state.equipment
                and st.session_state.reporter and st.session_state.desc):
            st.warning("⚠️ 필수 항목을 모두 입력해주세요.")
        else:
            try:
                ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
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
                ws.append_row(new_row, value_input_option="USER_ENTERED")

                form_payload = {
                    "작성자": st.session_state.reporter,
                    "포지션": st.session_state.position,
                    "위치": st.session_state.location,
                    "설비명": st.session_state.equipment,
                    "세부장치": st.session_state.detail,
                    "장애유형": st.session_state.issue,
                    "장애내용": st.session_state.desc,
                    "긴급": st.session_state.urgent
                }
                send_google_chat_alert(form_payload)

                popup = st.empty()
                with popup.container():
                    st.markdown(
                        """
                        <div style='background:white;padding:30px;border-radius:12px;text-align:center;
                        box-shadow:0 4px 25px rgba(0,0,0,0.2);'>
                            <h3>✅ 장애 접수 완료</h3>
                            <p>장애가 정상적으로 등록되었습니다.</p>
                            <p><b>📌 오른쪽 [미조치 장애 현황]</b>에서 확인 가능합니다.</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                time.sleep(2)
                popup.empty()
                st.rerun()
            except Exception as e:
                st.error(f"❌ 전송 중 오류: {e}")


# ─────────────────────────────────────────────
# 📌 미조치 장애 현황
# ─────────────────────────────────────────────
with col_recent:
    st.subheader("📌 미조치 / 점검중 장애 현황")

    if st.session_state.position:
        df_recent = get_recent_issues_by_position(st.session_state.position)
        if df_recent.empty:
            st.info("✅ 현재 미조치 또는 점검중 장애가 없습니다.")
        else:
            for _, row in df_recent.iterrows():
                date_str = row["날짜"].strftime("%y.%m.%d %H:%M") if pd.notna(row["날짜"]) else "—"
                st.markdown(
                    f"""
                    <div style="background-color:rgba(255,255,255,0.9);
                    padding:12px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.08);
                    margin-bottom:10px;">
                        <b>📅 {date_str}</b><br>
                        <b>위치:</b> {row['위치']}<br>
                        <b>설비:</b> {row['설비명']} | <b>세부:</b> {row['세부장치']}<br>
                        <b>내용:</b> {row['장애내용']}<br>
                        <span style="color:#666;">접수자: {row['작성자']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("🔎 포지션을 선택하면 해당 포지션의 최근 장애 현황이 표시됩니다.")

st.caption("© 2025 981Park Technical Support Team — Streamlit 장애 접수 시스템")
