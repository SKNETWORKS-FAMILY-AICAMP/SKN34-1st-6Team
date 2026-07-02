"""
map_view.py

[역할]
- 카카오맵 기반 주차장 위치 시각화 페이지

[기능]
1. 카카오맵 JS SDK 임베드 (streamlit.components.v1.html)
2. 난이도등급(A~D) 기준 색상 마커 + 클러스터링
3. 구 / 요금 / 등급 필터
4. 마커 클릭 시 인포윈도우(주소, 요금, 면수, 혼잡도 등급)
5. 메인(app.py) 검색어 연동 → 검색 결과를 지도에 자동 반영
"""

import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import apply_common_style
from database.select_data_test import get_parking_with_score

load_dotenv()
apply_common_style()


# =========================
# 🔑 카카오맵 JS 키
# =========================
KAKAO_JS_KEY = os.environ.get("KAKAO_JS_KEY") or st.secrets.get("KAKAO_JS_KEY", "")

GRADE_COLOR = {
    "A": "#22c55e",  # 여유 (초록)
    "B": "#3b82f6",  # 보통 (파랑)
    "C": "#f59e0b",  # 혼잡 (주황)
    "D": "#ef4444",  # 매우혼잡 (빨강)
}
GRADE_LABEL = {
    "A": "여유",
    "B": "보통",
    "C": "혼잡",
    "D": "매우혼잡",
}


# =========================
# 📌 데이터 로딩
# =========================
@st.cache_data
def load_data() -> pd.DataFrame:
    df = get_parking_with_score()
    df = df.dropna(subset=["latitude", "longitude"])
    df["district"] = df["pk_address"].str.split().str[0]
    return df


df = load_data()


def search_parking(data: pd.DataFrame, query: str) -> pd.DataFrame:
    """이름 / 주소 / 최근접역명을 통합해서 검색 (app.py와 동일 로직)"""
    if not query:
        return data
    cols = [c for c in ["pk_name", "pk_address", "최근접역명"] if c in data.columns]
    mask = pd.Series(False, index=data.index)
    for c in cols:
        mask |= data[c].astype(str).str.contains(query, case=False, na=False)
    return data[mask]


# =========================
# 📌 메인 검색어 연동
# =========================
# app.py에서 검색한 키워드를 session_state로 공유받아 자동 필터링
main_query = st.session_state.get("search_query", None)

# =========================
# 🎨 헤더
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
    .legend-chip {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        margin-right: 6px;
    }
    </style>
    <div class="map-header">
        <h1>🗺️ 주차장 위치 지도 (카카오맵)</h1>
        <p>난이도등급(주차 난이도) 기준으로 마커 색상이 표시됩니다. 마커를 클릭하면 상세 정보를 볼 수 있어요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not KAKAO_JS_KEY:
    st.warning(
        "카카오맵 JavaScript 키가 설정되지 않았습니다. "
        "환경변수 `KAKAO_JS_KEY` 또는 `.streamlit/secrets.toml`의 `KAKAO_JS_KEY` 값을 채워주세요.",
        icon="⚠️",
    )

# 메인에서 검색어를 갖고 온 경우 배너 표시
if main_query:
    st.info(f"🔍 메인에서 검색한 **'{main_query}'** 결과를 지도에 표시합니다. 아래 필터로 추가 조회할 수 있어요.", icon="🔗")

# =========================
# 🔍 필터 영역
# =========================
filt_col1, filt_col2, filt_col3, filt_col4 = st.columns([1.2, 1, 1, 1])

with filt_col1:
    districts = ["전체"] + sorted(df["district"].dropna().unique().tolist())
    selected_district = st.selectbox("구 선택", districts)

with filt_col2:
    fee_types = ["전체"] + sorted(df["fee_type"].dropna().unique().tolist())
    selected_fee = st.selectbox("요금 유형", fee_types)

with filt_col3:
    grades = ["전체", "A", "B", "C", "D"]
    selected_grade = st.selectbox("난이도 등급", grades)

with filt_col4:
    # 메인 검색어가 있으면 기본값으로 채워줌 (사용자가 수정 가능)
    keyword = st.text_input(
        "주차장 이름 검색",
        value=main_query or "",
        placeholder="예: 마장동",
    )

# =========================
# 📌 필터 적용
# =========================
# 1) 메인 검색어로 먼저 베이스 필터링 (이름/주소/역명 통합)
filtered = search_parking(df, main_query)

# 2) 지도 페이지 자체 필터 추가 적용
if selected_district != "전체":
    filtered = filtered[filtered["district"] == selected_district]
if selected_fee != "전체":
    filtered = filtered[filtered["fee_type"] == selected_fee]
if selected_grade != "전체":
    filtered = filtered[filtered["난이도등급"] == selected_grade]
if keyword and keyword != main_query:
    # 사용자가 직접 수정한 경우에만 재검색
    filtered = search_parking(df, keyword)
    if selected_district != "전체":
        filtered = filtered[filtered["district"] == selected_district]
    if selected_fee != "전체":
        filtered = filtered[filtered["fee_type"] == selected_fee]
    if selected_grade != "전체":
        filtered = filtered[filtered["난이도등급"] == selected_grade]

st.caption(f"표시 중인 주차장: **{len(filtered)}곳** / 전체 {len(df)}곳")

# 범례
legend_html = "".join(
    f'<span class="legend-chip" style="background:{GRADE_COLOR[g]}">{g} · {GRADE_LABEL[g]}</span>'
    for g in ["A", "B", "C", "D"]
)
st.markdown(legend_html, unsafe_allow_html=True)
st.write("")

# =========================
# 📦 마커 데이터 준비
# =========================
def _safe(v, default=""):
    """NaN/None을 JSON에 안전한 값으로 변환"""
    if v is None:
        return default
    try:
        if pd.isna(v):
            return default
    except (TypeError, ValueError):
        pass
    return v


markers = []
for _, row in filtered.iterrows():
    grade = row.get("난이도등급", "B")
    if pd.isna(grade) or grade not in GRADE_COLOR:
        grade = "B"
    markers.append(
        {
            "name": _safe(row.get("pk_name"), "이름 없음"),
            "address": _safe(row.get("pk_address")),
            "lat": float(row["latitude"]),
            "lng": float(row["longitude"]),
            "fee_type": _safe(row.get("fee_type")),
            "basic_fee": _safe(row.get("basic_fee")),
            "space": _safe(row.get("parking_space")),
            "grade": grade,
            "grade_label": GRADE_LABEL.get(grade, ""),
            "color": GRADE_COLOR.get(grade, "#3b82f6"),
            "station": _safe(row.get("최근접역명")),
            "ev_charge": str(_safe(row.get("전기차충전소여부"), "N")).strip().upper() or "N",
        }
    )

markers_json = json.dumps(markers, ensure_ascii=False)

# =========================
# 🗺️ 카카오맵 HTML
# =========================
kakao_map_html = f"""
<div id="map" style="width:100%; height:640px; border-radius:14px; overflow:hidden;"></div>
<script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}&libraries=clusterer&autoload=false"></script>
<script>
  kakao.maps.load(function () {{
    var container = document.getElementById('map');
    var options = {{
      center: new kakao.maps.LatLng(37.5665, 126.9780),
      level: 7,
    }};
    var map = new kakao.maps.Map(container, options);
    map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);

    var data = {markers_json};
    var bounds = new kakao.maps.LatLngBounds();
    var clusterMarkers = [];

    function svgMarkerImage(color) {{
      var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="30" height="38" viewBox="0 0 30 38">' +
        '<path d="M15 0C6.7 0 0 6.7 0 15c0 11 15 23 15 23s15-12 15-23C30 6.7 23.3 0 15 0z" fill="' + color + '"/>' +
        '<circle cx="15" cy="15" r="6" fill="white"/>' +
        '</svg>';
      var url = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg);
      return new kakao.maps.MarkerImage(url, new kakao.maps.Size(30, 38), {{ offset: new kakao.maps.Point(15, 38) }});
    }}

    var infowindow = new kakao.maps.InfoWindow({{ zIndex: 10 }});

    data.forEach(function (p) {{
      var pos = new kakao.maps.LatLng(p.lat, p.lng);
      var marker = new kakao.maps.Marker({{
        position: pos,
        image: svgMarkerImage(p.color),
      }});
      marker.setMap(map);
      bounds.extend(pos);
      clusterMarkers.push(marker);

      kakao.maps.event.addListener(marker, 'click', function () {{
        var content = '<div style="padding:10px 12px; font-size:13px; line-height:1.5; max-width:230px;">' +
          '<div style="font-weight:700; margin-bottom:4px;">' + p.name + '</div>' +
          '<div style="color:#555;">' + p.address + '</div>' +
          '<div style="margin-top:6px;">요금: ' + (p.fee_type || '-') + (p.basic_fee ? ' (기본 ' + p.basic_fee + '원)' : '') + '</div>' +
          '<div>면수: ' + (p.space || '-') + '면</div>' +
          '<div>혼잡도: <b style="color:' + p.color + '">' + p.grade + ' · ' + p.grade_label + '</b></div>' +
          (p.station ? '<div>인근역: ' + p.station + '</div>' : '') +
          '<div>전기차 충전소 여부: <b>' + p.ev_charge + '</b></div>' +
          '</div>';
        infowindow.setContent(content);
        infowindow.open(map, marker);
      }});
    }});

    if (data.length > 0) {{
      map.setBounds(bounds);
    }}

    if (typeof kakao.maps.MarkerClusterer !== 'undefined') {{
      var clusterer = new kakao.maps.MarkerClusterer({{
        map: map,
        averageCenter: true,
        minLevel: 6,
      }});
      clusterer.addMarkers(clusterMarkers);
    }}
  }});
</script>
"""

components.html(kakao_map_html, height=660, scrolling=False)

st.divider()

# =========================
# 📋 선택 결과 테이블
# =========================
with st.expander("📋 필터링 결과 표로 보기"):
    show_cols = [
        "pk_name", "pk_address", "fee_type", "basic_fee",
        "parking_space", "난이도등급", "최근접역명", "전기차충전소여부",
    ]
    show_cols = [c for c in show_cols if c in filtered.columns]
    st.dataframe(filtered[show_cols], use_container_width=True)