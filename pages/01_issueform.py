import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# ────────────────────────────────────────────────
# Google Sheets 설정
# ────────────────────────────────────────────────
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
CREDS_PATH = "credentials.json"
SPREADSHEET_NAME = "981파크 장애관리"
SHEET_MAPPING = "설비매핑"
SHEET_LOG = "접수내용"

# ────────────────────────────────────────────────
# 시트 로드 함수
# ────────────────────────────────────────────────


@st.cache_data(ttl=300)
def load_mapping_sheet():
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPE)
    gc = gspread.authorize(creds)
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_MAPPING)
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df


@st.cache_data(ttl=30)
def get_recent_issues_by_position(position_name: str):
    """포지션별 미조치/점검중 장애 10건 조회"""
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPE)
    gc = gspread.authorize(creds)
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])

    if "포지션" not in df.columns:
        return pd.DataFrame()

    df = df[df["포지션"] == position_name]
    if "접수처리" in df.columns:
        df = df[df["접수처리"].isin(["접수중", "점검중"])]
    if "종결" in df.columns:
        df = df[df["종결"] != "종결"]

    if "날짜" in df.columns:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    df = df.sort_values("날짜", ascending=False).head(10)
    return df[["날짜", "위치", "설비명", "세부장치", "장애내용", "작성자"]].fillna("")


# ────────────────────────────────────────────────
# UI 시작
# ────────────────────────────────────────────────
st.title("🧾 981Park 장애 접수")

df_map = load_mapping_sheet()
col_form, col_recent = st.columns([1.3, 0.9], gap="large")

# ────────────────────────────────────────────────
# 왼쪽: 장애 접수 폼
# ────────────────────────────────────────────────
with col_form:
    st.subheader("📋 장애 접수 등록")

    # 세션 상태 초기화
    for key in ["position", "location", "equipment", "detail", "issue", "reporter", "desc", "urgent"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    # 포지션 선택
    positions = sorted(df_map["포지션"].dropna().unique())
    st.session_state.position = st.selectbox("📍 포지션", [""] + positions)

    # 위치
    if st.session_state.position:
        locations = sorted(
            df_map[df_map["포지션"] == st.session_state.position]["위치"].dropna().unique())
    else:
        locations = []
    st.session_state.location = st.selectbox("🏗️ 위치", [""] + locations)

    # 설비명
    if st.session_state.position and st.session_state.location:
        equipments = sorted(df_map[
            (df_map["포지션"] == st.session_state.position) &
            (df_map["위치"] == st.session_state.location)
        ]["설비명"].dropna().unique())
    else:
        equipments = []
    st.session_state.equipment = st.selectbox("⚙️ 설비명", [""] + equipments)

    # 세부기기 (D~AG)
    if st.session_state.equipment:
        row = df_map[
            (df_map["포지션"] == st.session_state.position) &
            (df_map["위치"] == st.session_state.location) &
            (df_map["설비명"] == st.session_state.equipment)
        ]
        detail_start, detail_end = 3, 33
        details = row.iloc[0, detail_start:detail_end].tolist()
        details = [d for d in details if d and d.strip() != ""]
    else:
        details = []
    st.session_state.detail = st.selectbox("🔩 세부기기", [""] + details)

    # 장애유형 (AH~AM)
    try:
        issue_start, issue_end = 33, 39
        issue_types = sorted(
            set(df_map.iloc[:, issue_start:issue_end].values.flatten()) - {""})
    except Exception:
        issue_types = []
    st.session_state.issue = st.selectbox("🚨 장애유형", [""] + issue_types)

    # 작성자 / 내용 / 긴급 체크
    st.session_state.reporter = st.text_input(
        "👤 작성자 이름", st.session_state.reporter)
    st.session_state.desc = st.text_area(
        "📝 장애 내용 (상세히 작성)", st.session_state.desc)
    st.session_state.urgent = st.checkbox(
        "🚨 긴급 장애 (즉시 대응 필요)", value=st.session_state.urgent)

    # 버튼 영역
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submit = st.button("✅ 장애 접수 등록", use_container_width=True)

    # 전송 로직
    if submit:
        if not (st.session_state.position and st.session_state.location and st.session_state.equipment and st.session_state.reporter and st.session_state.desc):
            st.warning("⚠️ 필수 항목(포지션, 위치, 설비명, 작성자, 내용)을 모두 입력해주세요.")
        else:
            try:
                creds = Credentials.from_service_account_file(
                    CREDS_PATH, scopes=SCOPE)
                gc = gspread.authorize(creds)
                log_sheet = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                new_row = [
                    "긴급" if st.session_state.urgent else "일반",
                    now, st.session_state.reporter, st.session_state.position, st.session_state.location,
                    st.session_state.equipment, st.session_state.detail, st.session_state.issue,
                    st.session_state.desc, "접수중", "", "", "", "", ""
                ]
                log_sheet.append_row(
                    new_row, value_input_option="USER_ENTERED")

                # 🎉 가상 모달 팝업 (버전 호환)
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

                time.sleep(2.5)
                popup.empty()
                st.rerun()

            except Exception as e:
                st.error(f"❌ 전송 중 오류 발생: {e}")

# ────────────────────────────────────────────────
# 오른쪽: 포지션별 미조치 장애 현황
# ────────────────────────────────────────────────
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
