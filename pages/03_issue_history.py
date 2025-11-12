# pages/03_issue_history.py
"""
981Park Dashboard - 장애 이력(완료) 개선판
- 날짜 파싱 강화, 상단 필터 UX 개선 (월: selectbox, 포지션: multiselect, 검색),
  reset 안전 구현(st.session_state), 테이블 index 제거(HTML 렌더링)
"""
import streamlit as st
import pandas as pd
import numpy as np
import io, json, requests, re
from datetime import datetime, timedelta
from typing import Optional
from menu_ui import render_sidebar

st.set_page_config(page_title="장애 조치 이력", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display: none !important;}
    section[data-testid="stSidebar"] div[role="listbox"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

render_sidebar(active="IssueHistory")



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

SHEET_ID_DEFAULT = "1Gm0GPsWm1H9fPshiBo8gpa8djwnPa4ordj9wWTGG_vI"
SHEET_LOG_GID_DEFAULT = "389240943"
SHEET_LOG_NAME = "접수내용"

def normalize_col_name(s: str) -> str:
    if s is None:
        return ""
    return str(s).replace("\n", " ").replace("\r", " ").strip()

def make_unique_column_names(cols):
    seen = {}
    out = []
    for c in cols:
        base = normalize_col_name(c)
        if base == "":
            base = "unnamed"
        if base in seen:
            seen[base] += 1
            new = f"{base}__dup{seen[base]}"
        else:
            seen[base] = 0
            new = base
        out.append(new)
    return out

def try_regex_ymd(s: str):
    if not s or not isinstance(s, str):
        return pd.NaT
    m = re.search(r'(\d{4})\D+(\d{1,2})\D+(\d{1,2})', s)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        try:
            return pd.to_datetime(f"{int(y)}-{int(mo)}-{int(d)}")
        except Exception:
            return pd.NaT
    return pd.NaT

def parse_date_safe(val):
    try:
        if val is None:
            return pd.NaT
        if isinstance(val, (pd.Timestamp, datetime)):
            return pd.to_datetime(val)
        if isinstance(val, (int, float)) and not np.isnan(val):
            try:
                return pd.to_datetime(datetime(1899,12,30) + timedelta(days=int(val)))
            except Exception:
                pass
        s = str(val).strip()
        if s == "" or s.lower() in ["nan","none","nat"]:
            return pd.NaT
        p = pd.to_datetime(s, errors="coerce")
        if not pd.isna(p):
            return p
        p2 = try_regex_ymd(s)
        if not pd.isna(p2):
            return p2
        m2 = re.search(r'(\d{4})\s*[-./]?\s*(\d{1,2})\s*[-./]?\s*(\d{1,2})', s)
        if m2:
            y, mo, d = m2.groups()
            try:
                return pd.to_datetime(f"{int(y)}-{int(mo)}-{int(d)}")
            except:
                return pd.NaT
        return pd.NaT
    except Exception:
        return pd.NaT

def init_gspread_client():
    if "google_service_account" not in st.secrets:
        return None
    try:
        from google.oauth2.service_account import Credentials
        import gspread
    except Exception:
        return None
    info = st.secrets["google_service_account"]
    if isinstance(info, str):
        try:
            info = json.loads(info)
        except:
            return None
    try:
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
        client = gspread.authorize(creds)
        return client
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_via_gspread(sheet_name: str = SHEET_LOG_NAME) -> pd.DataFrame:
    client = init_gspread_client()
    if client is None:
        raise RuntimeError("gspread client 미설정 (서비스계정 없음).")
    sheet_id = st.secrets.get("SPREADSHEET_ID") or SHEET_ID_DEFAULT
    try:
        sh = client.open_by_key(sheet_id)
    except Exception as e:
        sh_name = st.secrets.get("SPREADSHEET_NAME")
        if sh_name:
            try:
                sh = client.open(sh_name)
            except Exception as e2:
                raise RuntimeError(f"open_by_key 실패: {e}; fallback name 실패: {e2}")
        else:
            raise RuntimeError(f"open_by_key 실패: {e}")
    try:
        ws = sh.worksheet(sheet_name)
    except Exception as e:
        raise RuntimeError(f"워크시트 '{sheet_name}' 접근 실패: {e}")
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()
    header = data[0]
    body = data[1:]
    unique_header = make_unique_column_names(header)
    df = pd.DataFrame(body, columns=unique_header)
    empty_cols = [c for c in df.columns if df[c].replace("", pd.NA).isna().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
    return df

@st.cache_data(ttl=300)
def fetch_sheet_via_csv(csv_url: Optional[str] = None, gid: Optional[str] = None) -> pd.DataFrame:
    if not csv_url:
        sheet_id = st.secrets.get("SPREADSHEET_ID") or SHEET_ID_DEFAULT
        gid = gid or st.secrets.get("SHEET_LOG_GID") or SHEET_LOG_GID_DEFAULT
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    resp = requests.get(csv_url, timeout=15)
    if resp.status_code != 200:
        raise RuntimeError(f"CSV fetch 실패 (HTTP {resp.status_code})")
    raw = resp.text
    head = raw.strip()[:1024].lower()
    if "<html" in head or "accounts.google" in head:
        raise RuntimeError("CSV가 HTML을 반환함(권한 필요).")
    sep = "," if raw.count(",") >= raw.count(";") else ";"
    df = pd.read_csv(io.StringIO(raw), sep=sep)
    df.columns = make_unique_column_names(list(df.columns))
    empty_cols = [c for c in df.columns if df[c].replace("", pd.NA).isna().all()]
    if empty_cols:
        df = df.drop(columns=empty_cols)
    return df

def detect_columns_from_df(cols):
    status_col = next((c for c in cols if any(x in c for x in ["상태","접수처리","처리상태","status"])), None)
    closure_col = next((c for c in cols if any(x in c for x in ["종결","종결여부","완결"])), None)
    date_col = next((c for c in cols if any(x in c for x in ["날짜","접수일","date","등록일","완료일자"])), None)
    pos_col = next((c for c in cols if any(x in c for x in ["포지션","위치","site","position"])), None)
    return status_col, closure_col, date_col, pos_col

def is_completed_row_from_df(r, status_col, closure_col):
    try:
        if status_col and str(r.get(status_col,"")).strip() == "완료":
            return True
        if closure_col and str(r.get(closure_col,"")).strip() == "종결":
            return True
    except Exception:
        return False
    return False

def load_completed_issues():
    last_err = ""
    df = pd.DataFrame()
    source = None
    try:
        df = fetch_via_gspread(SHEET_LOG_NAME)
        source = "gspread"
    except Exception as e:
        last_err += f"gspread: {e} | "
        try:
            df = fetch_sheet_via_csv()
            source = "csv"
        except Exception as e2:
            last_err += f"csv: {e2}"
            raise RuntimeError("스프레드시트 로드 실패: " + last_err)

    if df is None or df.empty:
        raise RuntimeError("시트 로드 성공했으나 데이터(헤더 제외 행)가 없습니다. 원인: " + last_err)

    cols = list(df.columns)
    status_col, closure_col, date_col, pos_col = detect_columns_from_df(cols)

    parsed_series = pd.Series(pd.NaT, index=df.index)
    if date_col and date_col in df.columns:
        parsed_series = df[date_col].apply(parse_date_safe)
    else:
        candidates = []
        for c in df.columns:
            if any(k in c for k in ["날", "date", "완료", "접수", "등록"]):
                candidates.append(c)
        for cand in candidates:
            try:
                this_parsed = df[cand].apply(parse_date_safe)
                if this_parsed.notna().sum() > 0:
                    parsed_series = parsed_series.combine_first(this_parsed)
            except Exception:
                continue

    df["_parsed_date"] = parsed_series
    df["_is_completed"] = df.apply(lambda r: is_completed_row_from_df(r, status_col, closure_col), axis=1)
    completed_df = df[df["_is_completed"]].copy().reset_index(drop=True)
    return completed_df, (status_col, closure_col, date_col, pos_col, source)

st.markdown("<style>"
            ".kpi-card{background:white;padding:12px;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.04);}"
            ".kpi-title{font-size:13px;color:#1f6feb;margin-bottom:6px;}"
            ".kpi-value{font-size:24px;font-weight:600;}"
            ".filter-area{background:#fbfbfd;padding:12px;border-radius:8px;border:1px solid #f0f0f2;margin-bottom:10px}"
            ".table-wrap table{border-collapse:collapse;width:100%} .table-wrap th, .table-wrap td{padding:8px;border-bottom:1px solid #eee;font-size:13px}"
            "</style>", unsafe_allow_html=True)

st.title("✅ 조치완료 장애 이력")
st.caption("Apps Script의 '완료'/'종결' 기준으로 완료 처리된 항목만 표시합니다.")

try:
    completed_df, (status_col, closure_col, date_col, pos_col, data_source) = load_completed_issues()
except Exception as e:
    st.error("접수내용 시트 로드 실패: " + str(e))
    st.stop()

if "날짜" in completed_df.columns:
    try:
        parsed_from_str = pd.to_datetime(completed_df["날짜"], errors="coerce")
        mask_parsed = ~parsed_from_str.isna()
        completed_df.loc[mask_parsed, "날짜"] = parsed_from_str[mask_parsed].dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass

if "_parsed_date" in completed_df.columns:
    mask_missing = (~completed_df.get("날짜", pd.Series("")).astype(str).str.strip().astype(bool)) | (completed_df.get("날짜", pd.Series("")).isna())
    completed_df.loc[mask_missing, "날짜"] = completed_df.loc[mask_missing, "_parsed_date"].apply(
        lambda d: pd.to_datetime(d).strftime("%Y-%m-%d %H:%M") if not pd.isna(d) else ""
    )
else:
    completed_df["날짜"] = completed_df.get("날짜", "")

try:
    completed_df["_month"] = pd.to_datetime(completed_df["_parsed_date"], errors="coerce").dt.strftime("%Y-%m")
except Exception:
    completed_df["_month"] = "unknown"
completed_df["_month"] = completed_df["_month"].fillna("unknown").replace("NaT", "unknown")

if not pos_col or pos_col not in completed_df.columns:
    pos_col = next((c for c in completed_df.columns if "포지션" in c or "위치" in c or c.lower().startswith("pos")), None)

fc1, fc2, fc3, fc4 = st.columns([3,3,2,1])

all_months = [m for m in completed_df["_month"].unique() if m is not None]
valid_months = sorted([m for m in all_months if str(m).strip() and m != "unknown"], reverse=True)
month_options = ["전체"] + valid_months + (["unknown"] if "unknown" in all_months else [])
default_month = valid_months[0] if valid_months else "전체"

if "sel_month" not in st.session_state:
    st.session_state["sel_month"] = default_month
if "sel_positions" not in st.session_state:
    st.session_state["sel_positions"] = []

sel_month = fc1.selectbox("월(YYYY-MM)", options=month_options, index=month_options.index(st.session_state["sel_month"]) if st.session_state["sel_month"] in month_options else 0, format_func=lambda x: x)
st.session_state["sel_month"] = sel_month

if pos_col and pos_col in completed_df.columns:
    pos_options = sorted([str(x) for x in completed_df[pos_col].astype(str).unique() if x and str(x).strip()])
else:
    pos_options = []
sel_positions = fc2.multiselect("포지션 (선택없음 = 전체)", options=pos_options, default=st.session_state.get("sel_positions", []))
st.session_state["sel_positions"] = sel_positions

search_q = fc3.text_input("검색 (설비명 / 장애내용 / 작성자)", value=st.session_state.get("search_q",""), placeholder="키워드 입력해서 좁히기")
st.session_state["search_q"] = search_q

df_filtered = completed_df.copy()

if st.session_state.get("sel_month","전체") != "전체":
    chosen = st.session_state.get("sel_month")
    df_filtered = df_filtered[df_filtered["_month"] == chosen]

if st.session_state.get("sel_positions"):
    df_filtered = df_filtered[df_filtered[pos_col].astype(str).isin(st.session_state["sel_positions"])]

q = st.session_state.get("search_q","").strip()
if q:
    ql = q.lower()
    df_filtered = df_filtered[df_filtered.apply(lambda r: ql in str(r.get("설비명","")).lower() or ql in str(r.get("장애내용","")).lower() or ql in str(r.get("작성자","")).lower(), axis=1)]

total_after = len(df_filtered)
urgent_after = int(df_filtered.apply(lambda r: r.astype(str).str.contains(r'\b긴급\b|\burgent\b', case=False, na=False).any(), axis=1).sum())

wanted = ["날짜", "작성자",  "위치", "설비명", "세부장치", "장애내용", "점검자", "완료일자", "점검내용"]
if "_parsed_date" in df_filtered.columns and "완료일자" not in df_filtered.columns:
    df_filtered["완료일자"] = df_filtered["_parsed_date"].apply(lambda d: pd.to_datetime(d).strftime("%Y-%m-%d %H:%M") if not pd.isna(d) else "")

available = list(df_filtered.columns)
col_map = {}
for w in wanted:
    if w in df_filtered.columns:
        col_map[w] = w
        continue
    found = None
    for c in available:
        if w.replace(" ", "") in c.replace(" ", ""):
            found = c; break
    if not found:
        for c in available:
            if w.split()[0].lower() in c.lower():
                found = c; break
    if found:
        col_map[w] = found
display_cols = [col_map[w] for w in wanted if w in col_map]

# === 기존 AgGrid 부분 삭제 후 아래 코드로 교체 ===

# ✅ 표 표시 (st.data_editor 버전)
st.markdown("""
<style>
div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    background: #fff !important;
    box-shadow: 0 4px 18px rgba(0,0,0,0.05) !important;
    padding: 10px !important;
}
thead tr th {
    background-color: #f8fafc !important;
    font-weight: 600 !important;
    color: #334155 !important;
    font-size: 13px !important;
    border-bottom: 1px solid #e2e8f0 !important;
}
tbody tr:hover td {
    background-color: #f1f5f9 !important;
}
</style>
""", unsafe_allow_html=True)

# 🔹 표 표시용 데이터 구성
df_show = df_filtered[display_cols].copy().fillna("")
df_show.insert(0, "번호", np.arange(1, len(df_show) + 1))

# 🔹 컬럼 폭/유형 지정
column_config = {
    "번호": st.column_config.Column("번호", width="small"),
    "날짜": st.column_config.Column("날짜", width="small"),
    "작성자": st.column_config.Column("작성자", width="small"),
    "위치": st.column_config.Column("위치", width="medium"),
    "설비명": st.column_config.Column("설비명", width="medium"),
    "세부장치": st.column_config.Column("세부장치", width="medium"),
    "장애내용": st.column_config.Column("장애내용", width="large"),
    "점검자": st.column_config.Column("점검자", width="small"),
    "완료일자": st.column_config.Column("완료일자", width="small"),
    "점검내용": st.column_config.Column("점검내용", width="large"),
}

# 🔹 필터 정보 표시
st.markdown(
    f"""
    <div style='margin-top:10px;margin-bottom:6px;color:#64748b;font-size:14px;'>
    총 <b>{len(df_filtered)}</b>건 중 <b>{len(df_show)}</b>건 표시됨 
    {f"(월: {st.session_state['sel_month']})" if st.session_state.get('sel_month') else ''}
    </div>
    """,
    unsafe_allow_html=True
)

# ✅ st.data_editor로 표 출력
st.data_editor(
    df_show,
    hide_index=True,
    use_container_width=True,
    height=700,
    disabled=True,
    column_config=column_config
)
