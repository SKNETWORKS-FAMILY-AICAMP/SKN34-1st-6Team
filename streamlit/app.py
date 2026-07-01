"""
app.py - 페이지 라우터
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

pg = st.navigation([
    st.Page("home.py",             title="홈",    icon="🏠", default=True),
    st.Page("pages/지도.py",       title="지도",  icon="🗺️"),
    st.Page("pages/analysis.py",   title="분석",  icon="📊"),
    st.Page("pages/congestion.py", title="혼잡도", icon="🚦"),
])

# 지도 페이지 객체를 session_state에 저장 → home.py에서 st.switch_page()로 이동
st.session_state["_page_지도"] = "pages/지도.py"

pg.run()