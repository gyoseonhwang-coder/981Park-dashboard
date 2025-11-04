# pages/02_issue_manage.py
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from menu_ui import render_sidebar

# ─────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="🧰 981Park 장애 처리", layout="wide")
render_sidebar(active="IssueManage")

# ─────────────────────────────────────────────
# Google 인증 (secrets.toml 기반)
# ─────────────────────────────────────────────
try:
    creds_info = st.secrets["google_service_account"]
except Exception:
    st.error("🔐 `st.secrets['google_service_account']` 항목이 없습니다.")
    st.stop()

creds = Credentials.from_service_account_info(
    creds_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"]
)
gc = gspread.authorize(creds)

SPREADSHEET_NAME = "981파크 장애관리"
SHEET_LOG = "접수내용"

# ─────────────────────────────────────────────
# UI Layout
# ─────────────────────────────────────────────
st.title("🧰 981Park 장애 처리")

# ─────────────────────────────────────────────
# 접수내용 시트 데이터 로드
# ─────────────────────────────────────────────


@st.cache_data(ttl=30)
def load_issue_log() -> pd.DataFrame:
    """981파크 장애관리 > 접수내용 시트 전체 로드"""
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(data[1:], columns=data[0])

    # 날짜 변환
    if "날짜" in df.columns:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    return df


# ✅ 1️⃣ 데이터 먼저 로드
df = load_issue_log()

if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

# ✅ 2️⃣ 포지션 목록 자동 구성
position_list = ["전체"]
if "포지션" in df.columns:
    position_list += sorted(df["포지션"].dropna().unique().tolist())

# ✅ 3️⃣ 필터 UI
col1, col2, col3 = st.columns([1.2, 1, 0.6])
with col1:
    selected_position = st.selectbox("📍 포지션 선택", position_list)
with col2:
    selected_status = st.selectbox("📋 상태", ["전체", "접수중", "점검중", "완료"])
with col3:
    refresh = st.button("🔄 새로고침")

st.markdown("---")


# ─────────────────────────────────────────────
# 접수내용 시트 데이터 로드
# ─────────────────────────────────────────────


@st.cache_data(ttl=30)
def load_issue_log() -> pd.DataFrame:
    """981파크 장애관리 > 접수내용 시트 전체 로드"""
    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(data[1:], columns=data[0])

    # 날짜 변환
    if "날짜" in df.columns:
        df["날짜"] = pd.to_datetime(df["날짜"], format="%Y-%m-%d", errors="coerce")
    return df


# ─────────────────────────────────────────────
# 데이터 표시
# ─────────────────────────────────────────────
df = load_issue_log()

if df.empty:
    st.warning("⚠️ 접수내용 시트에 데이터가 없습니다.")
    st.stop()

# 포지션 / 상태 필터 적용
filtered = df.copy()

if selected_position != "전체" and "포지션" in filtered.columns:
    filtered = filtered[filtered["포지션"] == selected_position]

if selected_status != "전체" and "접수처리" in filtered.columns:
    filtered = filtered[filtered["접수처리"] == selected_status]

# 최신순 정렬
if "날짜" in filtered.columns:
    filtered = filtered.sort_values("날짜", ascending=False)

# 표시 컬럼만 선택
display_cols = [
    "날짜", "작성자", "포지션", "위치", "설비명",
    "세부기기", "장애내용", "접수처리", "점검자"
]
existing_cols = [c for c in display_cols if c in filtered.columns]

st.subheader(f"📋 장애 목록 ({len(filtered)}건)")
st.dataframe(filtered[existing_cols], use_container_width=True)

# ─────────────────────────────────────────────
# 3️⃣ 상세 패널 (행 선택 및 처리)
# ─────────────────────────────────────────────

# Streamlit 1.50 기준: st.dataframe에는 on_click 이벤트 없음 → selectbox로 행 선택 구현
if not filtered.empty:
    st.markdown("### 🧾 장애 상세 처리")
    row_labels = [
        f"{i+1}. {r['포지션']} / {r['설비명']} / {r['장애내용']} ({r['접수처리']})"
        for i, r in filtered.iterrows()
    ]
    selected_row = st.selectbox("처리할 장애 선택", ["선택 안 함"] + row_labels, index=0)

    if selected_row != "선택 안 함":
        try:
            # 선택된 라벨의 실제 텍스트 추출
            selected_label = selected_row.split(". ", 1)[1]

            # 라벨 내용(포지션/설비명/장애내용)으로 매칭
            issue = None
            for _, row in filtered.iterrows():
                label = f"{row['포지션']} / {row['설비명']} / {row['장애내용']} ({row['접수처리']})"
                if label == selected_label:
                    issue = row
                    break

            if issue is None:
                st.warning("⚠️ 선택한 항목이 현재 목록에 없습니다. 다시 선택해주세요.")
                st.stop()

        except Exception as e:
            st.error(f"❌ 선택 항목 처리 중 오류 발생: {e}")
            st.stop()

        st.markdown("---")
        st.markdown(f"#### 🧩 선택된 장애 ({issue['포지션']})")
        st.write(f"**📅 날짜:** {issue.get('날짜', '')}")
        st.write(f"**👤 작성자:** {issue.get('작성자', '')}")
        st.write(f"**📍 위치:** {issue.get('위치', '')}")
        st.write(f"**⚙️ 설비명:** {issue.get('설비명', '')}")
        st.write(f"**🧩 세부기기:** {issue.get('세부기기', '')}")
        st.write(f"**📝 장애내용:** {issue.get('장애내용', '')}")
        st.write(f"**📋 현재상태:** {issue.get('접수처리', '')}")

        st.markdown("---")

        colA, colB = st.columns(2)

        with colA:
            담당자 = st.text_input("👷 점검자 이름", issue.get("점검자", ""))
            선택포지션 = st.selectbox(
                "📍 포지션 시트 선택",
                ["선택 안 함", "Audio/Video", "RACE",
                    "LAB", "운영설비", "충전설비", "정비고", "기타"]
            )

        with colB:
            점검내용 = st.text_area("🧰 점검내용", height=120)
            비고 = st.text_area("📝 비고 (선택)", height=80)

        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        # ✅ 점검 시작
        with col_btn1:
            if st.button("🚧 점검 시작", use_container_width=True):
                try:
                    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
                    # 해당 행 찾기
                    row_index = df.index[df["날짜"] == issue["날짜"]].tolist()[
                        0] + 2  # header offset
                    ws.update_cell(row_index, 10, "점검중")   # J열 접수처리
                    ws.update_cell(row_index, 12, 담당자)     # L열 점검자
                    ws.update_cell(row_index, 11, 선택포지션)  # K열 장애등록
                    ws.update_cell(row_index, 15, "장애 등록")  # O열 장애관리
                    st.success(f"✅ 점검중으로 변경 및 {선택포지션} 시트 등록 완료")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 점검 시작 중 오류: {e}")

        # ✅ 완료 처리
        with col_btn2:
            if st.button("✅ 완료 처리", use_container_width=True):
                try:
                    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
                    row_index = df.index[df["날짜"] == issue["날짜"]].tolist()[
                        0] + 2
                    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    ws.update_cell(row_index, 10, "완료")     # J열
                    ws.update_cell(row_index, 13, now)        # M열
                    ws.update_cell(row_index, 14, 점검내용)    # N열
                    ws.update_cell(row_index, 15, "장애 처리")  # O열
                    ws.update_cell(row_index, 17, "종결")     # Q열
                    st.success("✅ 장애 완료 처리 및 종결 완료")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 완료 처리 중 오류: {e}")

        # ✅ 간단 완료
        with col_btn3:
            if st.button("⚡ 간단 완료 (포지션 이동 없음)", use_container_width=True):
                try:
                    ws = gc.open(SPREADSHEET_NAME).worksheet(SHEET_LOG)
                    row_index = df.index[df["날짜"] == issue["날짜"]].tolist()[
                        0] + 2
                    now = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                    ws.update_cell(row_index, 10, "완료")      # 접수처리
                    ws.update_cell(row_index, 14, 점검내용)    # 점검내용
                    ws.update_cell(row_index, 15, "장애 처리")  # 장애관리
                    ws.update_cell(row_index, 17, "종결")      # 종결
                    st.success("⚡ 간단 장애 완료 및 종결 처리됨")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 간단 완료 중 오류: {e}")

st.caption("※ ‘접수중’ 또는 ‘점검중’ 상태의 건만 처리 가능합니다.")
