import requests

WEBHOOK_URL = (
    "https://chat.googleapis.com/v1/spaces/AAAA-Dl8vDs/messages"
    "?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI"
    "&token=qpitTslB-dlzAaxy3nqBCSfSxOcjm1ly6vYWDTaPRB8"
)

test_msg = {"text": "✅ 테스트 메시지 — Streamlit Webhook 연결 확인"}
resp = requests.post(WEBHOOK_URL, json=test_msg)
print(resp.status_code, resp.text)
