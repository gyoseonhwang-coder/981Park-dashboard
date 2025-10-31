# 📄 pages/01_🧾_장애_접수.py
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

st.set_page_config(page_title="🧾 장애 접수", layout="wide")

st.title("🧾 981Park 장애 접수")
st.caption("App Script 폼 기능을 Streamlit 내에서 동일하게 구현한 버전")

# ────────────────────────────────────────────────
# Google Sheets & Slack 연동 설정
# ────────────────────────────────────────────────
SPREADSHEET_ID = "1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI"
SHEET_NAME = "접수내용"
WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/AAAA-Dl8vDs/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=qpitTslB-dlzAaxy3nqBCSfSxOcjm1ly6vYWDTaPRB8"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_file(
    "credentials.json", scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# ────────────────────────────────────────────────
# Streamlit Form UI
# ────────────────────────────────────────────────
with st.form("issue_form", clear_on_submit=True):
    st.subheader("📋 장애 접수 입력")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("작성자 이름")
        position = st.text_input("포지션")
        location = st.text_input("위치")
        equipment = st.text_input("설비명")
    with col2:
        category = st.text_input("세부기기")
        issue_type = st.text_input("장애유형")
        description = st.text_area("장애내용", height=80)
        priority = st.checkbox("🚨 긴급 장애")

    submitted = st.form_submit_button("📩 장애 접수")

# ────────────────────────────────────────────────
# 폼 제출 처리
# ────────────────────────────────────────────────
if submitted:
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row = [
            "긴급" if priority else "일반",
            now, name, position, location,
            equipment, category, issue_type, description,
            "접수중", "", "", "", "", "", "", ""
        ]
        sheet.append_row(new_row, value_input_option="USER_ENTERED")

        # Slack 알림 전송
        msg = {
            "cards": [{
                "header": {"title": "🚨 장애 접수", "subtitle": now},
                "sections": [{
                    "widgets": [
                        {"keyValue": {"topLabel": "작성자", "content": name}},
                        {"keyValue": {"topLabel": "위치",
                                      "content": f"{position} > {location}"}},
                        {"keyValue": {"topLabel": "설비",
                                      "content": f"{equipment} > {category}"}},
                        {"keyValue": {"topLabel": "장애 증상", "content": issue_type}},
                        {"keyValue": {"topLabel": "내용", "content": description}},
                    ]
                }]
            }]
        }
        requests.post(WEBHOOK_URL, json=msg)
        st.success("✅ 장애 접수가 성공적으로 등록되었습니다!")

    except Exception as e:
        st.error(f"❌ 오류 발생: {e}")
