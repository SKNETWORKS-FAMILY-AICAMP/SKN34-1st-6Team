"""
congestion.py

[역할]
- 주차장 혼잡도 분석 페이지

[기능]
1. 혼잡도 점수 시각화
2. 등급(A~D) 표시
3. 인기 주차장 분석
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import apply_common_style

st.set_page_config(page_title="분석", page_icon="📊", layout="wide")
apply_common_style()