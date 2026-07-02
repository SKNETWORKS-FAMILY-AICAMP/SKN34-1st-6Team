"""
app.py - 페이지 라우터
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# 반드시 다른 st 명령보다 먼저 호출되어야 함
st.set_page_config(
    page_title="서울시 공영주차장 분석",
    page_icon="🅿️",
    layout="wide",
)

from utils import apply_common_style, render_car_restriction_sidebar

pg = st.navigation([
    st.Page("home.py",             title="홈",    icon="🏠", default=True),
    st.Page("pages/지도.py",       title="지도",  icon="🗺️"),
    st.Page("pages/analysis.py",   title="분석",  icon="📊"),
    st.Page("pages/congestion.py", title="혼잡도", icon="🚦"),
])

# 지도 페이지 객체를 session_state에 저장 → home.py에서 st.switch_page()로 이동
st.session_state["_page_지도"] = "pages/지도.py"

# 사이드바 상단 공통 위젯 (모든 페이지에 표시되도록 pg.run() 이전에 렌더링)
apply_common_style()
render_car_restriction_sidebar()

pg.run()