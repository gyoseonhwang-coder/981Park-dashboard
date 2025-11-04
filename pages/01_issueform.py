import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
from menu_ui import render_sidebar

# ─────────────────────────────────────────────
# 기본 사이드바 숨김 + 우리가 만든 사이드바 사용
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none !important;}
section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="🧾 981Park 장애 접수",
                   layout="wide", initial_sidebar_state="expanded")
render_sidebar(active="IssueForm")  # ✅ 왼쪽 고정 메뉴 유지

# ─────────────────────────────────────────────
# Google 인증 (st.secrets만 사용! 파일 경로 X)
# ─────────────────────────────────────────────
# secrets.toml 예)
# [google_service_account]
# type="service_account"
# project_id="..."
# private_key_id="..."
# private_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
# client_email="..."
# client_id="..."
# token_uri="https://oauth2.googleapis.com/token"
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

# ─────────────────────────────────────────────
# Google Sheets 설정
# ─────────────────────────────────────────────
SPREADSHEET_NAME = "981파크 장애관리"
SHEET_MAPPING = "설비매핑"
SHEET_LOG = "접수내용"

# ─────────────────────────────────────────────
# 시트 로드 함수 (전역 gc 재사용)
# ─────────────────────────────────────────────


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

    # 상태 필터
    df = df[df["포지션"] == position_name].copy()
    if "접수처리" in df.columns:
        df = df[df["접수처리"].isin(["접수중", "점검중"])]
    if "종결" in df.columns:
        df = df[df["종결"] != "종결"]

    # 날짜 정렬
    if "날짜" in df.columns:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    df = df.sort_values("날짜", ascending=False).head(10)

    # 표시 컬럼만 반환 (없을 수 있는 컬럼은 기본값 처리)
    for col in ["위치", "설비명", "세부장치", "장애내용", "작성자"]:
        if col not in df.columns:
            df[col] = ""
    return df[["날짜", "위치", "설비명", "세부장치", "장애내용", "작성자"]].fillna("")


# ─────────────────────────────────────────────
# UI 시작
# ─────────────────────────────────────────────
st.title("🧾 981Park 장애 접수")

df_map = load_mapping_sheet()
col_form, col_recent = st.columns([1.3, 0.9], gap="large")

# ─────────────────────────────────────────────
# 왼쪽: 장애 접수 폼 (기존 UX/로직 그대로)
# ─────────────────────────────────────────────
with col_form:
    st.subheader("📋 장애 접수 등록")

    # 세션 상태 초기화 (기존 키 유지)
    for key in ["position", "location", "equipment", "detail", "issue", "reporter", "desc", "urgent"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key != "urgent" else False

    # 포지션 선택
    positions = sorted(df_map["포지션"].dropna().unique(
    )) if not df_map.empty and "포지션" in df_map.columns else []
    st.session_state.position = st.selectbox(
        "📍 포지션", [""] + positions, index=0)

    # 위치
    if st.session_state.position:
        locations = sorted(
            df_map[df_map["포지션"] ==
                   st.session_state.position]["위치"].dropna().unique()
        ) if "위치" in df_map.columns else []
    else:
        locations = []
    st.session_state.location = st.selectbox(
        "🏗️ 위치", [""] + locations, index=0)

    # 설비명
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

    # 세부기기 (D~AG → 0-index: 3:33)
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

    # 장애유형 (AH~AM → 0-index: 33:39)
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

    # 작성자 / 내용 / 긴급 체크
    st.session_state.reporter = st.text_input(
        "👤 작성자 이름", st.session_state.reporter or "")
    st.session_state.desc = st.text_area(
        "📝 장애 내용 (상세히 작성)", st.session_state.desc or "")
    st.session_state.urgent = st.checkbox(
        "🚨 긴급 장애 (즉시 대응 필요)", value=bool(st.session_state.urgent))

    # 버튼 영역
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submit = st.button("✅ 장애 접수 등록", use_container_width=True)

    # 전송 로직 (기존 그대로, 인증만 st.secrets 기반 gc 사용)
    if submit:
        if not (st.session_state.position and st.session_state.location and
                st.session_state.equipment and st.session_state.reporter and st.session_state.desc):
            st.warning("⚠️ 필수 항목(포지션, 위치, 설비명, 작성자, 내용)을 모두 입력해주세요.")
        else:
            try:
                log_sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
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
                    "접수중",  # 접수처리
                    "", "", "", "", ""  # 이후 컬럼 여유분 (시트 구조 유지)
                ]
                log_sheet.append_row(
                    new_row, value_input_option="USER_ENTERED")

                # 🎉 가상 모달 팝업 (기존 스타일 유지)
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

                # 모달 표시 잠깐 후 닫고 리런 (폼 초기화 유지)
                time.sleep(2.0)
                popup.empty()
                st.rerun()

            except Exception as e:
                st.error(f"❌ 전송 중 오류 발생: {e}")

# ─────────────────────────────────────────────
# 오른쪽: 포지션별 미조치/점검중 현황 (기존 그대로)
# ─────────────────────────────────────────────
with col_recent:
    st.subheader("📌 미조치 / 점검중 장애 현황")

    if st.session_state.position:
        df_recent = get_recent_issues_by_position(st.session_state.position)
        if not df_recent.empty:
            for _, row in df_recent.iterrows():
                # 날짜 안전 포맷
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


def send_google_chat_alert(form_data: dict):
    """
    Google Chat Webhook 알림 전송 함수
    - Apps Script sendSlackAlert(form, now)와 동일 구조
    - 카드형 메시지로 시각적 완성도 향상
    """
    import requests
    from datetime import datetime, timezone, timedelta

    try:
        WEBHOOK_URL = (
            "https://chat.googleapis.com/v1/spaces/AAAA-Dl8vDs/messages"
            "?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"
            "&token=qpitTslB-dlzAaxy3nqBCSfSxOcjm1ly6vYWDTaPRB8"
        )

        # 현재 시간 (KST)
        now_kst = datetime.now(timezone(timedelta(hours=9)))
        formatted_time = now_kst.strftime("%Y-%m-%d %H:%M")

        # Google Chat 카드 메시지 구조
        message = {
            "cardsV2": [
                {
                    "cardId": "981park_issue_alert",
                    "card": {
                        "header": {
                            "title": "🚨 장애 접수 알림",
                            "subtitle": "981Park Technical Support System",
                            "imageUrl": "https://cdn-icons-png.flaticon.com/512/564/564619.png",
                            "imageType": "CIRCLE"
                        },
                        "sections": [
                            {
                                "header": f"📍 포지션: {form_data['포지션']} → {form_data['위치']}",
                                "widgets": [
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "PERSON"},
                                            "text": f"<b>작성자:</b> {form_data['작성자']}"
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "GEAR"},
                                            "text": f"<b>설비명:</b> {form_data['설비명']} → {form_data.get('세부장치', '')}"
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "WARNING"},
                                            "text": f"<b>장애유형:</b> {form_data['장애유형']}"
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "DESCRIPTION"},
                                            "text": f"<b>내용:</b> {form_data['장애내용']}"
                                        }
                                    },
                                    {
                                        "decoratedText": {
                                            "startIcon": {"knownIcon": "CLOCK"},
                                            "text": f"<b>접수시각:</b> {formatted_time}"
                                        }
                                    }
                                ]
                            },
                            {
                                "header": "🧾 시스템 기록",
                                "widgets": [
                                    {
                                        "textParagraph": {
                                            "text": "📊 해당 접수건은 Google Sheets **[981파크 장애관리 → 접수내용]** 시트에 자동 저장되었습니다."
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }

        # Google Chat Webhook POST 요청
        resp = requests.post(WEBHOOK_URL, json=message)
        if resp.status_code != 200:
            print(f"🚨 Webhook 전송 실패: {resp.status_code} - {resp.text}")
        else:
            print("✅ Google Chat 알림 전송 완료")

    except Exception as e:
        print(f"🚨 Google Chat 알림 오류: {e}")
