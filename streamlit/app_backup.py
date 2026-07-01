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

from database.select_data_test import get_all_parking
# → DB 또는 CSV에서 주차장 데이터 가져오는 함수

# =========================
# 📌 페이지 기본 설정
# =========================
st.set_page_config(
    page_title="주차장 대시보드",   # 브라우저 탭 제목
    layout="wide"                  # 화면 넓게 사용 (대시보드용)
)

st.title("🚗 서울시 공영주차장")

# =========================
# 📌 데이터 로딩 (캐싱 적용)
# =========================
@st.cache_data
def load_data():
    """
    데이터 로딩 함수 (캐싱 적용)

    - DB 또는 CSV에서 데이터 가져옴
    - Streamlit 재실행 시 속도 개선
    """
    df = get_all_parking()
    return df

df = load_data()

# =========================
# 📊 기본 통계 영역
# =========================
st.header("📊 전체 통계")

col1, col2, col3 = st.columns(3)

col1.metric(
    "전체 주차장 수",
    len(df)
)

col2.metric(
    "유료 주차장 수",
    len(df[df["fee_type"] == "유료"])
)

col3.metric(
    "무료 주차장 수",
    len(df[df["fee_type"] == "무료"])
)

st.divider()

# =========================
# 📋 데이터 테이블 출력
# =========================
st.header("📋 주차장 전체 데이터")

st.dataframe(
    df,
    use_container_width=True  # 화면 넓이에 맞게 출력
)

st.divider()

# =========================
# 🗺️ 지도 시각화
# =========================
st.header("🗺️ 주차장 위치 지도")

# 서울 중심 좌표
map_center = [37.5665, 126.9780]

# 지도 생성 (서울 기준)
m = folium.Map(location=map_center, zoom_start=11)

# 데이터에 좌표가 있는 경우 마커 표시
for _, row in df.iterrows():
    if "lat" in df.columns and "lng" in df.columns:

        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=row.get("pk_name", "주차장 이름 없음"),
            icon=folium.Icon(color="blue")
        ).add_to(m)

# Streamlit에 지도 출력
st_folium(m, width=1100, height=600)

# =========================
# 🔍 필터 기능 (구 단위 검색)
# =========================
st.header("🔍 지역별 검색")

# 주소에서 '구' 추출 (예: 서울시 강남구 ...)
district_list = sorted(
    df["pk_address"].dropna().str.split().str[0].unique()
)

selected_district = st.selectbox(
    "구 선택",
    district_list
)

# 선택된 구 포함 데이터 필터링
filtered_df = df[df["pk_address"].str.contains(selected_district)]

st.write(f"### 📍 {selected_district} 검색 결과")
st.dataframe(filtered_df, use_container_width=True)