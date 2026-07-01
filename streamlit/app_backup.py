"""
app.py

[역할]
- 주차장 데이터 대시보드 메인 페이지
- API + 크롤링 데이터 기반 기본 시각화

[구성]
1. 전체 데이터 조회
2. 주차장 리스트 테이블
3. 간단한 통계
4. 지도 표시 (기본)
"""
# 파일경로설정
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =========================
# 📌 라이브러리 import
# =========================
import streamlit as st          # 웹 대시보드 UI 프레임워크
import pandas as pd             # 데이터 처리 (DataFrame)
import folium                   # 지도 시각화 라이브러리
from streamlit_folium import st_folium  # Streamlit에서 folium 출력

from database.select_data_test import get_parking_with_score
# → DB에서 주차장 + 난이도/혼잡도 점수 조인 데이터 가져오는 함수

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
# 📌 페이지 기본 설정
# =========================
st.set_page_config(
    page_title="주차장 대시보드",
    page_icon="🚗",
    layout="wide",
)

# =========================
# 🎨 공통 스타일
# =========================
st.markdown(
    """
    <style>
    .map-header {
        padding: 1.2rem 1.6rem;
        border-radius: 14px;
        background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%);
        color: white;
        margin-bottom: 1rem;
    }
    .map-header h1 { margin: 0; font-size: 1.6rem; }
    .map-header p { margin: 0.3rem 0 0 0; opacity: 0.85; font-size: 0.92rem; }

    .stat-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stat-card .label { font-size: 0.85rem; color: #6b7280; margin-bottom: 4px; }
    .stat-card .value { font-size: 1.7rem; font-weight: 700; color: #111827; }
    .stat-card .sub { font-size: 0.78rem; color: #9ca3af; margin-top: 2px; }

    .legend-chip {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        margin-right: 6px;
    }

    section[data-testid="stSidebar"] { background-color: #f8fafc; }
    div[data-testid="stMetricValue"] { font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="map-header">
        <h1>🚗 서울시 공영주차장 분석 대시보드</h1>
        <p>API + 크롤링 데이터를 기반으로 시각화한 페이지입니다. 좌측 메뉴에서 지도 / 혼잡도 / 분석 페이지로 이동할 수 있어요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# 📌 데이터 로딩 (캐싱 적용)
# =========================
@st.cache_data
def load_data() -> pd.DataFrame:
    """
    데이터 로딩 함수 (캐싱 적용)

    - DB(parking + parking_score 조인)에서 데이터 가져옴
    - Streamlit 재실행 시 속도 개선
    """
    df = get_parking_with_score()
    df = df.rename(columns={"latitude": "lat", "longitude": "lng"})
    df = df.dropna(subset=["lat", "lng"])
    df["district"] = df["pk_address"].str.split().str[0]
    return df


df = load_data()

# =========================
# 📊 기본 통계 영역
# =========================
st.subheader("📊 전체 통계")

stat_cols = st.columns(4)

stat_defs = [
    ("전체 주차장 수", f"{len(df):,}곳", None),
    ("유료 주차장", f"{len(df[df['fee_type'] == '유료']):,}곳", f"전체의 {len(df[df['fee_type'] == '유료']) / len(df) * 100:.0f}%"),
    ("무료 주차장", f"{len(df[df['fee_type'] == '무료']):,}곳", f"전체의 {len(df[df['fee_type'] == '무료']) / len(df) * 100:.0f}%"),
    ("총 주차 면수", f"{int(df['parking_space'].fillna(0).sum()):,}면", None),
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

# 난이도등급 분포 (있을 경우)
if "난이도등급" in df.columns:
    grade_counts = df["난이도등급"].value_counts()
    legend_html = "".join(
        f'<span class="legend-chip" style="background:{GRADE_COLOR.get(g, "#6b7280")}">'
        f'{g} · {GRADE_LABEL.get(g, g)} {grade_counts.get(g, 0)}곳</span>'
        for g in ["A", "B", "C", "D"]
        if g in grade_counts.index
    )
    st.markdown(legend_html, unsafe_allow_html=True)

st.divider()

# =========================
# 🔍 필터 영역 (구 단위 검색)
# =========================
st.subheader("🔍 지역별 검색")

filt_col1, filt_col2 = st.columns([1, 2])

with filt_col1:
    district_list = sorted(df["district"].dropna().unique())
    selected_district = st.selectbox("구 선택", ["전체"] + district_list)

with filt_col2:
    keyword = st.text_input("주차장 이름 검색", placeholder="예: 마장동")

filtered_df = df.copy()
if selected_district != "전체":
    filtered_df = filtered_df[filtered_df["district"] == selected_district]
if keyword:
    filtered_df = filtered_df[filtered_df["pk_name"].str.contains(keyword, na=False)]

st.caption(f"검색 결과: **{len(filtered_df)}곳** / 전체 {len(df)}곳")

st.divider()

# =========================
# 🗺️ 지도 시각화
# =========================
st.subheader("🗺️ 주차장 위치 지도")
st.caption("간단 미리보기용 지도입니다. 카카오맵 기반의 상세 지도는 좌측 메뉴의 '지도' 페이지를 이용해주세요.")

map_center = [37.5665, 126.9780]
m = folium.Map(location=map_center, zoom_start=11, tiles="cartodbpositron")

for _, row in filtered_df.iterrows():
    grade = row.get("난이도등급", None)
    color = {"A": "green", "B": "blue", "C": "orange", "D": "red"}.get(grade, "blue")

    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=5,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=folium.Popup(
            f"<b>{row.get('pk_name', '이름 없음')}</b><br>{row.get('pk_address', '')}<br>"
            f"요금: {row.get('fee_type', '-')}",
            max_width=250,
        ),
    ).add_to(m)

st_folium(m, width=1100, height=560)

st.divider()

# =========================
# 📋 데이터 테이블 출력
# =========================
st.subheader("📋 주차장 데이터")

show_cols = [
    "pk_name", "pk_address", "fee_type", "basic_fee",
    "parking_space", "난이도등급", "최근접역명",
]
show_cols = [c for c in show_cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[show_cols] if show_cols else filtered_df,
    use_container_width=True,
    hide_index=True,
)