import csv
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import io
import re

from menu_ui import render_sidebar

st.set_page_config(
    page_title="🚀 981Park Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"  # ✅ 사이드바 항상 펼침
)

# ✅ 왼쪽 고정 사이드바 렌더
render_sidebar(active="Dashboard")

KST = ZoneInfo("Asia/Seoul")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI/export?format=csv&gid=389240943"


def fetch_csv(url: str) -> pd.DataFrame:
    """Google Sheets CSV를 안전하게 로드(HTML 응답/구분자/인코딩 보정)"""
    resp = requests.get(url, timeout=15)
    head = resp.text.strip()[:200].lower()
    if head.startswith("<"):
        raise RuntimeError("CSV 대신 HTML 응답 수신(공유 또는 인증 설정 확인 필요)")
    resp.encoding = "utf-8"
    raw = resp.text
    first = raw.splitlines()[0] if raw else ""
    sep = ";" if first.count(";") > first.count(",") else ","
    df = pd.read_csv(io.StringIO(raw), sep=sep, engine="python")
    df.columns = df.columns.str.replace("\n", "", regex=False).str.strip()
    df = df.loc[:, ~df.columns.str.contains(r"^Unnamed", na=False)]
    return df


def parse_jeju_date(val):
    """
    981파크 접수내용 날짜 파서 (예: '2025. 10. 20 오후 3:05:39')
    """
    if pd.isna(val):
        return pd.NaT
    s = str(val).strip()
    # 오전/오후 → AM/PM
    s = s.replace("오전", "AM").replace("오후", "PM")
    # '2025. 10. 20' → '2025-10-20'
    s = re.sub(r"\s*\.\s*", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")

    patterns = [
        "%Y-%m-%d %p %I:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%y-%m-%d",
    ]
    for fmt in patterns:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue

    if re.fullmatch(r"\d+(\.\d+)?", s):
        try:
            return pd.to_datetime(float(s), unit="D", origin="1899-12-30")
        except Exception:
            pass

    return pd.to_datetime(s, errors="coerce")


def normalize_status(s):
    """접수처리 원문 → 표준 상태"""
    if pd.isna(s):
        return "미정의"
    sv = str(s).strip()
    if sv in ["점검중", "진행중", "처리중"]:
        return "점검중"
    if sv in ["접수중", "대기", "미조치"]:
        return "미조치(접수중)"
    if sv in ["완료", "운영중", "사용중지"]:
        return "완료"
    return sv


def month_label(dt: pd.Timestamp) -> str:
    if pd.isna(dt):
        return ""
    return f"{dt.year}년 {dt.month}월"


def status_counts(frame: pd.DataFrame):
    total = len(frame)
    vc = frame["상태"].value_counts()
    prog = int(vc.get("점검중", 0))
    pend = int(vc.get("미조치(접수중)", 0))
    done = int(vc.get("완료", 0))
    rate = (done / total * 100) if total else 0.0
    return total, prog, pend, done, rate


def render_kpi(cards, columns=5):
    """큰 KPI 카드(HTML) 렌더링"""
    st.markdown(
        """
        <style>
        .kpi-card{padding:18px;border-radius:12px;border:1px solid rgba(255,255,255,0.08);
                  background:rgba(0,0,0,0.03);}
        .kpi-title{font-size:14px;color:#7e8b9c;margin-bottom:6px;}
        .kpi-value{font-size:28px;font-weight:700;}
        .c-blue{color:#2c7be5;}
        .c-orange{color:#f59f00;}
        .c-red{color:#e03131;}
        .c-green{color:#2b8a3e;}
        .c-navy{color:#233142;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(columns)
    for (title, value, cls), col in zip(cards, cols):
        col.markdown(
            f"""
            <div class="kpi-card">
              <div class="kpi-title">{title}</div>
              <div class="kpi-value {cls}">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


try:
    df = fetch_csv(SHEET_URL)
except Exception as e:
    st.error(f"❌ 접수내용 로드 실패: {e}")
    st.stop()

rename_map = {
    "우선순위": "우선순위",
    "날짜": "날짜",
    "작성자": "작성자",
    "포지션": "포지션",
    "위치": "위치",
    "설비명": "설비명",
    "세부장치": "세부장치",
    "장애유형": "장애유형",
    "장애내용": "장애내용",
    "접수처리": "접수처리",
    "장애등록": "장애등록",
    "점검자": "점검자",
    "완료일자": "완료일자",
    "점검내용": "점검내용",
    "장애관리": "장애관리",
    "소요시간": "소요시간",
    "종결": "종결",
    "상태": "접수처리",
}
norm_cols = {c: c.replace("\n", "").strip() for c in df.columns}
df.rename(columns=norm_cols, inplace=True)
for raw in list(df.columns):
    key = raw.replace("\n", "").strip()
    if key in rename_map and raw != rename_map[key]:
        df.rename(columns={raw: rename_map[key]}, inplace=True)

required = ["날짜", "포지션", "위치", "접수처리"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"❌ 접수내용 필수 컬럼 누락: {', '.join(missing)}")
    st.stop()

df["날짜"] = df["날짜"].apply(parse_jeju_date)
if "완료일자" in df.columns:
    df["완료일자"] = df["완료일자"].apply(parse_jeju_date)
df["상태"] = df["접수처리"].apply(normalize_status)
df = df.dropna(subset=["날짜"]).copy()

df["월"] = df["날짜"].apply(month_label)

if not df.empty:
    min_month = df["날짜"].min().to_period("M")
    max_month = df["날짜"].max().to_period("M")
    all_periods = pd.period_range(min_month, max_month, freq="M")
    all_month_labels = [f"{p.year}년 {p.month}월" for p in all_periods]
else:
    all_month_labels = []

st.title("🚀 981파크 장애관리 실시간 대시보드")
st.caption("접수내용 실시간 연동 (30초 자동 갱신) — 포지션/위치별 상태 분포까지")
with st.expander("필터 열기 / 닫기", expanded=False):
    st.write("원하는 범위를 선택하면 KPI/그래프가 즉시 재계산됩니다.")

    sel_months = st.multiselect(
        "📆 월 선택", all_month_labels, default=all_month_labels)

    all_positions = sorted(df["포지션"].dropna().astype(str).unique())
    sel_positions = st.multiselect(
        "📍 포지션 선택", all_positions, default=all_positions)

    all_locations = sorted(df["위치"].dropna().astype(str).unique())
    sel_locations = st.multiselect(
        "🏗️ 위치 선택", all_locations, default=all_locations)

    status_options = ["점검중", "미조치(접수중)", "완료"]
    sel_status = st.multiselect(
        "⏱ 상태 선택", status_options, default=status_options)

mask = (
    df["월"].isin(sel_months if sel_months else all_month_labels) &
    df["포지션"].astype(str).isin(sel_positions if sel_positions else all_positions) &
    df["위치"].astype(str).isin(sel_locations if sel_locations else all_locations) &
    df["상태"].isin(sel_status if sel_status else status_options)
)
df_f = df.loc[mask].copy()

total, prog, pend, done, rate = status_counts(df_f)

st.subheader("📊 전체 장애 접수 현황")
render_kpi([
    ("전체 접수", f"{total}", "c-blue"),
    ("점검중", f"{prog}", "c-orange"),
    ("미조치(접수중)", f"{pend}", "c-red"),
    ("완료", f"{done}", "c-green"),
    ("완료율", f"{rate:0.1f}%", "c-navy"),
])

st.divider()

st.subheader("📅 월별 장애 접수 현황")

now_dt = datetime.now(tz=KST)
try:
    current_month = now_dt.strftime("%Y년 %-m월")
except ValueError:
    current_month = now_dt.strftime("%Y년 %#m월")

available_months = sorted(df["월"].unique())

default_month = current_month if current_month in available_months else available_months[-1]
selected_month = st.selectbox(
    "📆 조회할 월 선택", available_months, index=available_months.index(default_month))

df_month = df[df["월"] == selected_month]
m_total, m_prog, m_pend, m_done, m_rate = status_counts(df_month)

render_kpi([
    (f"{selected_month} 전체 접수", f"{m_total}", "c-blue"),
    ("점검중", f"{m_prog}", "c-orange"),
    ("미조치(접수중)", f"{m_pend}", "c-red"),
    ("완료", f"{m_done}", "c-green"),
    ("완료율", f"{m_rate:0.1f}%", "c-navy"),
])

st.divider()

today_kst = datetime.now(tz=KST).date()
df_today = df[df["날짜"].dt.date == today_kst]
t_total, t_prog, t_pend, t_done, t_rate = status_counts(df_today)

st.subheader("📅 금일 접수 현황 (KST 기준)")
render_kpi([
    ("금일 접수", f"{t_total}", "c-blue"),
    ("금일 점검중", f"{t_prog}", "c-orange"),
    ("금일 미조치", f"{t_pend}", "c-red"),
    ("금일 완료", f"{t_done}", "c-green"),
    ("금일 완료율", f"{t_rate:0.1f}%", "c-navy"),
])

st.divider()

st.subheader("📊 월별 장애 접수 및 완료율 추이")

if not df_f.empty:
    monthly_stats = (
        df_f.groupby("월")["상태"]
        .value_counts()
        .unstack(fill_value=0)
        .reindex(columns=["미조치(접수중)", "점검중", "완료"], fill_value=0)
    )

    monthly_stats["전체건수"] = monthly_stats.sum(axis=1)
    monthly_stats["완료율(%)"] = (
        monthly_stats["완료"] / monthly_stats["전체건수"] * 100
    ).round(1)

    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=monthly_stats.index,
        y=monthly_stats["전체건수"],
        mode="lines+markers+text",
        name="전체 건수",
        line=dict(color="#4e79a7", width=3),
        marker=dict(size=8, color="#4e79a7"),
        text=monthly_stats["전체건수"],
        textposition="top center"
    ))

    fig.add_trace(go.Scatter(
        x=monthly_stats.index,
        y=monthly_stats["완료율(%)"],
        mode="lines+markers+text",
        name="완료율(%)",
        yaxis="y2",
        line=dict(color="#2b8a3e", width=2, dash="dot"),
        marker=dict(size=8, color="#2b8a3e"),
        text=monthly_stats["완료율(%)"].astype(str) + "%",
        textposition="bottom center"
    ))

    fig.update_layout(
        height=650,
        title=dict(
            text="📈 월별 장애 접수 및 완료율 추이",
            font=dict(size=20, color="#233142",
                      family="Pretendard, Noto Sans KR", weight="bold"),
            x=0.5, xanchor="center"
        ),
        xaxis=dict(title="월", tickfont=dict(size=13)),
        yaxis=dict(title="접수 건수", showgrid=True,
                   gridcolor="rgba(200,200,200,0.2)"),
        yaxis2=dict(
            title="완료율(%)",
            overlaying="y",
            side="right",
            showgrid=False,
            range=[0, 110],
            tickfont=dict(size=13)
        ),
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#334155", size=13),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(l=60, r=60, t=80, b=60),
        transition=dict(duration=700, easing="cubic-in-out"),
    )

    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

else:
    st.info("선택한 필터에 해당하는 데이터가 없습니다.")


st.divider()

st.subheader("📍 포지션별 장애 상태 분포")

try:
    url_stats = "https://docs.google.com/spreadsheets/d/1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI/export?format=csv&gid=1138857357"
    raw = pd.read_csv(url_stats, header=None, dtype=str, encoding="utf-8")
except Exception as e:
    st.error(f"❌ 장애통계 시트를 불러오지 못했습니다: {e}")
    st.stop()

# 전처리
raw = raw.applymap(lambda x: x.strip() if isinstance(x, str) else x)
raw = raw.loc[:, ~(raw.isna() | (raw == "")).all(axis=0)]
raw = raw.dropna(how="all").reset_index(drop=True)

first_col = raw.iloc[:, 0].astype(str)
month_title_idx = first_col[first_col.str.contains(
    r"(📅\s*)?\d{4}-\d{2}.*포지션별.*장애", na=False)].index.tolist()
month_blocks = []

for i, idx in enumerate(month_title_idx):
    title_text = str(raw.iloc[idx, 0])
    m = re.search(r"(\d{4}-\d{2})", title_text)
    if not m:
        continue
    month = m.group(1)
    header_row = idx + 1
    if header_row >= len(raw):
        continue
    headers = raw.iloc[header_row, :].tolist()
    headers = [h if isinstance(h, str) and h != "" else None for h in headers]

    def normalize_col(nm: str | None):
        if nm is None:
            return None
        nm = nm.strip().replace(" ", "")
        if "포지션" in nm:
            return "포지션"
        if "전체" in nm or "접수" in nm:
            return "전체접수"
        if "미조치" in nm:
            return "미조치"
        return nm

    norm_headers = [normalize_col(h) for h in headers]

    next_idx = month_title_idx[i + 1] if i + \
        1 < len(month_title_idx) else len(raw)
    data_start = header_row + 1
    data_end = next_idx
    if data_start >= data_end:
        continue
    block = raw.iloc[data_start:data_end, :].copy()

    try:
        pos_idx = norm_headers.index("포지션")
        total_idx = norm_headers.index("전체접수")
    except ValueError:
        continue
    pend_idx = norm_headers.index("미조치") if "미조치" in norm_headers else None

    df_b = pd.DataFrame({
        "포지션": block.iloc[:, pos_idx],
        "전체접수": block.iloc[:, total_idx],
        "미조치": block.iloc[:, pend_idx] if pend_idx is not None and pend_idx < block.shape[1] else 0
    })
    df_b["월"] = month
    df_b = df_b[~df_b["포지션"].isin(["합계", "계", None, ""])]
    month_blocks.append(df_b)

if not month_blocks:
    st.error("⚠️ 장애통계 시트에서 유효한 월별 데이터 블록을 찾지 못했습니다.")
    st.stop()

df_stats = pd.concat(month_blocks, ignore_index=True)
for col in ["전체접수", "미조치"]:
    df_stats[col] = pd.to_numeric(
        df_stats[col], errors="coerce").fillna(0).astype(int)
df_stats["조치완료"] = (df_stats["전체접수"] - df_stats["미조치"]).clip(lower=0)
df_stats["포지션"] = df_stats["포지션"].astype(str).str.strip()

available_months = sorted(df_stats["월"].unique())
selected_month = st.selectbox(
    "📅 조회할 월 선택", available_months, index=len(available_months) - 1)

df_m = df_stats[df_stats["월"] == selected_month].copy()
df_long = df_m.melt(
    id_vars="포지션",
    value_vars=["조치완료", "미조치"],
    var_name="상태",
    value_name="건수"
)
df_long = df_long.merge(
    df_m[["포지션", "전체접수"]].rename(columns={"전체접수": "총건수"}),
    on="포지션"
)
df_long = df_long.sort_values("총건수", ascending=True)

color_map = {
    "조치완료": "rgba(78,121,167,0.9)",
    "미조치": "rgba(225,87,89,0.9)",
}

fig_pos = px.bar(
    df_long,
    x="건수",
    y="포지션",
    color="상태",
    orientation="h",
    barmode="stack",
    text="건수",
    color_discrete_map=color_map,
    title=f"📊 {selected_month} 기준 포지션별 장애 상태 분포",
)

totals = df_m[["포지션", "전체접수"]].rename(columns={"전체접수": "총건수"})
for _, r in totals.iterrows():
    fig_pos.add_annotation(
        x=float(r["총건수"]) + 0.5,
        y=r["포지션"],
        text=f"{int(r['총건수'])}건",
        showarrow=False,
        font=dict(color="#1e293b", size=12),
    )

fig_pos.update_traces(
    textfont_size=12,
    textposition="inside",
    marker_line_width=0.4,
    marker_line_color="rgba(255,255,255,0.4)",
)
fig_pos.update_layout(
    height=700,
    bargap=0.25,
    yaxis=dict(categoryorder="total ascending"),
    plot_bgcolor="rgba(255,255,255,0)",
    paper_bgcolor="rgba(255,255,255,0)",
    font=dict(color="#334155", size=13),
    transition=dict(duration=700, easing="cubic-in-out"),
    legend_title_text="상태 구분",
    margin=dict(l=60, r=40, t=80, b=40),
)

st.markdown("""
<style>
div[data-testid="stPlotlyChart"] {
  background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(245,247,250,0.95));
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  padding: 20px;
  transition: all .35s ease-in-out;
}
div[data-testid="stPlotlyChart"]:hover {
  transform: scale(1.008);
  box-shadow: 0 6px 22px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

st.plotly_chart(fig_pos, use_container_width=True, config={"responsive": True})

st.divider()

st.subheader("📈 통합 장애 통계 요약")

# ✅ CSV 다시 로드
try:
    raw_stats = pd.read_csv(url_stats, header=None, dtype=str)
except Exception as e:
    st.error(f"❌ 장애통계 시트 로드 실패: {e}")
    st.stop()


def extract_block(df, start, end):
    """주어진 행 범위(A열~B열)에서 통계 블록 추출"""
    block = df.iloc[start:end, :2].dropna(how="all")
    block.columns = ["항목", "건수"]
    block = block.dropna(subset=["항목"])
    block["건수"] = pd.to_numeric(
        block["건수"], errors="coerce").fillna(0).astype(int)
    return block


block_gubun = extract_block(raw_stats, 25, 30)
block_type = extract_block(raw_stats, 33, 38)
block_gun = extract_block(raw_stats, 41, 44)
block_keyword = extract_block(raw_stats, 47, 56)

color_seq = ["#4e79a7", "#59a14f", "#f28e2b", "#e15759", "#76b7b2", "#edc948"]


def render_bar(df_block, title, container):
    fig = px.bar(
        df_block,
        x="항목",
        y="건수",
        text="건수",
        color="항목",
        color_discrete_sequence=color_seq,
        title=title,
    )
    fig.update_traces(
        textfont_size=12,
        textposition="outside",
        marker_line_width=0,
        width=0.55,
    )
    fig.update_layout(
        height=400,
        plot_bgcolor="rgba(255,255,255,0)",
        paper_bgcolor="rgba(255,255,255,0)",
        font=dict(color="#334155", size=13, family="Pretendard, Noto Sans KR"),
        margin=dict(l=40, r=20, t=60, b=40),
        transition=dict(duration=500, easing="cubic-in-out"),
        title=dict(
            font=dict(size=18, color="#233142",
                      family="Pretendard, Noto Sans KR", weight="bold"),  # ✅ 수정
            x=0.5, xanchor="center"
        ),
        showlegend=False
    )

    container.plotly_chart(fig, use_container_width=True,
                           config={"responsive": True})


row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

render_bar(block_gubun, "🧩 세부기기별 통계", row1_col1)
render_bar(block_type, "🚨 장애유형별 통계", row1_col2)
render_bar(block_gun, "🔫 총기 모델별 고장 횟수", row2_col1)
render_bar(block_keyword, "🛠 서바이벌 키워드별 장애 횟수", row2_col2)

st.markdown("""
<style>
div[data-testid="stPlotlyChart"] {
  background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(245,247,250,0.95));
  border-radius: 16px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.08);
  padding: 16px;
  transition: all .35s ease-in-out;
}
div[data-testid="stPlotlyChart"]:hover {
  transform: scale(1.005);
  box-shadow: 0 6px 22px rgba(0,0,0,0.12);
}
</style>
""", unsafe_allow_html=True)

st.divider()

st.subheader("🧾 조치 필요 목록 (미조치/점검중)")
pending = df_f[df_f["상태"].isin(["미조치(접수중)", "점검중"])]
cols_show = [c for c in ["날짜", "포지션", "위치", "설비명",
                         "장애내용", "상태", "점검자"] if c in pending.columns]
st.dataframe(
    pending.sort_values("날짜", ascending=False)[cols_show],
    use_container_width=True, height=320
)

st.caption(
    "© 2025 981Park Technical Support Team — Premium UX Dashboard (접수내용 실시간)")
