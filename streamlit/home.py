"""
home.py

[역할]
- 홈 화면: 첫 진입 시 검색창, 검색 후 통계 + 정보 표시

[구성]
1. 첫 화면: 중앙 검색창 (이름 / 주소 / 최근접역명 통합 검색)
2. 검색 후: 통계 카드 + 등급 분포 + 필터 + 데이터 테이블
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =========================
# 📌 라이브러리 import
# =========================
import streamlit as st
import pandas as pd

from database.select_data_test import get_parking_with_score
from utils import apply_common_style

GRADE_COLOR = {
    "A": "#22c55e",  # 여유
    "B": "#3b82f6",  # 보통
    "C": "#f59e0b",  # 혼잡
    "D": "#ef4444",  # 매우혼잡
}
GRADE_LABEL = {
    "A": "여유",
    "B": "보통",
    "C": "혼잡",
    "D": "매우혼잡",
}

# =========================
# 📌 세션 상태 초기화
# =========================
if "search_query" not in st.session_state:
    st.session_state.search_query = None

# =========================
# 🎨 공통 스타일
# =========================
apply_common_style()

# =========================
# 📌 데이터 로딩 (캐싱 적용)
# =========================
@st.cache_data
def load_data() -> pd.DataFrame:
    df = get_parking_with_score()
    df = df.rename(columns={"latitude": "lat", "longitude": "lng"})
    df = df.dropna(subset=["lat", "lng"])
    df["district"] = df["pk_address"].str.split().str[0]
    return df


df = load_data()


def search_parking(data: pd.DataFrame, query: str) -> pd.DataFrame:
    """이름 / 주소 / 최근접역명을 통합해서 검색"""
    if not query:
        return data
    cols = [c for c in ["pk_name", "pk_address", "최근접역명"] if c in data.columns]
    mask = pd.Series(False, index=data.index)
    for c in cols:
        mask |= data[c].astype(str).str.contains(query, case=False, na=False)
    return data[mask]


# =========================================================================
# 🏁 첫 화면: 검색창만 표시
# =========================================================================
if st.session_state.search_query is None:
    st.markdown('<div class="hero-title">어떤 주차장을 찾으세요?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">주차장 이름, 주소, 가까운 지하철역으로 검색해보세요</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        with st.form("hero_search", clear_on_submit=False):
            query = st.text_input(
                "검색",
                placeholder="예: 마장동, 강남역, 공영주차장 ...",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("검색", use_container_width=True)

        st.markdown(
            '<div class="hero-hint">검색어를 비워두고 검색하면 전체 주차장을 볼 수 있어요</div>',
            unsafe_allow_html=True,
        )

    if submitted:
        st.session_state.search_query = query.strip()
        st.rerun()

    st.stop()


# =========================================================================
# 📊 검색 후: 통계 + 정보 화면
# =========================================================================
top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown(
        f"""
        <div class="map-header">
            <h1>🚗 서울시 공영주차장 분석 </h1>
            <p>검색어: <b>{st.session_state.search_query or "전체"}</b> </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_right:
    st.write("")
    if st.button("🗺️ 지도로 보기", use_container_width=True, key="btn_map"):
        st.switch_page("pages/지도.py")
    st.button("🔄 새로 검색", use_container_width=True, key="btn_reset",
              on_click=lambda: st.session_state.update(search_query=None))

base_df = search_parking(df, st.session_state.search_query)

# =========================================================================
# 🚫 검색 결과 없음: 중앙 카드만 표시하고 이하 내용 중단
# =========================================================================
if len(base_df) == 0:
    st.markdown(
        f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 45vh;
        ">
            <div style="
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 18px;
                padding: 2.5rem 3rem;
                text-align: center;
                box-shadow: 0 2px 12px rgba(0,0,0,0.3);
                max-width: 420px;
                width: 100%;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">🅿️</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.4rem;">
                    검색 결과가 없습니다.
                </div>
                <div style="font-size: 0.9rem; color: #94a3b8;">
                    <b style="color:#e2e8f0;">'{st.session_state.search_query}'</b>에 해당하는 주차장을 찾지 못했어요.<br>
                    다른 검색어로 다시 시도해보세요.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# =========================
# 📊 기본 통계 영역
# =========================
st.subheader("📊 전체 통계")

stat_cols = st.columns(4)

paid_count = len(base_df[base_df["fee_type"] == "유료"]) if len(base_df) else 0
free_count = len(base_df[base_df["fee_type"] == "무료"]) if len(base_df) else 0
total_count = len(base_df)

stat_defs = [
    ("검색된 주차장 수", f"{total_count:,}곳", None),
    ("유료 주차장", f"{paid_count:,}곳", f"검색결과의 {paid_count / total_count * 100:.0f}%" if total_count else "-"),
    ("무료 주차장", f"{free_count:,}곳", f"검색결과의 {free_count / total_count * 100:.0f}%" if total_count else "-"),
    ("총 주차 면수", f"{int(base_df['parking_space'].fillna(0).sum()):,}면", None),
]

for col, (label, value, sub) in zip(stat_cols, stat_defs):
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    col.markdown(
        f"""
        <div class="stat-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# 난이도등급 분포
if "난이도등급" in base_df.columns and len(base_df):
    grade_counts = base_df["난이도등급"].value_counts()
    legend_html = "".join(
        f'<span class="legend-chip" style="background:{GRADE_COLOR.get(g, "#6b7280")}">'
        f'{g} · {GRADE_LABEL.get(g, g)} {grade_counts.get(g, 0)}곳</span>'
        for g in ["A", "B", "C", "D"]
        if g in grade_counts.index
    )
    st.markdown(legend_html, unsafe_allow_html=True)

st.divider()

# =========================
# 🔍 추가 필터 영역
# =========================
st.subheader("🔍 추가 필터")

filt_col1, filt_col2 = st.columns([1, 2])

with filt_col1:
    district_list = sorted(base_df["district"].dropna().unique())
    selected_district = st.selectbox("구 선택", ["전체"] + district_list)

with filt_col2:
    keyword = st.text_input(
        "검색어 수정",
        value=st.session_state.search_query or "",
        placeholder="이름 / 주소 / 역명으로 다시 검색",
    )

filtered_df = base_df.copy()
if selected_district != "전체":
    filtered_df = filtered_df[filtered_df["district"] == selected_district]
if keyword != st.session_state.search_query:
    filtered_df = search_parking(df, keyword)
    if selected_district != "전체":
        filtered_df = filtered_df[filtered_df["district"] == selected_district]

st.caption(f"검색 결과: **{len(filtered_df)}곳** / 전체 {len(df)}곳")

st.divider()

# =========================
# 📋 데이터 테이블 출력
# =========================
st.subheader("📋 주차장 정보")

if len(filtered_df) == 0:
    st.info("필터 조건에 맞는 주차장이 없습니다. 필터를 조정해보세요.")
else:
    show_cols = [
        "pk_name", "pk_address", "fee_type", "basic_fee",
        "parking_space", "난이도등급", "최근접역명",
    ]
    show_cols = [c for c in show_cols if c in filtered_df.columns]

    col_rename = {
        "pk_name":       "주차장명",
        "pk_address":    "주소",
        "fee_type":      "요금유형",
        "basic_fee":     "기본요금",
        "parking_space": "주차면수",
        "난이도등급":    "난이도",
        "최근접역명":    "인근 지하철역",
    }

    st.dataframe(
        filtered_df[show_cols].rename(columns=col_rename),
        use_container_width=True,
        hide_index=True,
    )