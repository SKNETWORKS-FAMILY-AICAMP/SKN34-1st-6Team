"""
analysis.py

[역할]
- 주차장 데이터 통계 분석

[기능]
1. 요금 분석
2. 구별 주차장 분포
3. 리뷰 기반 키워드 분석
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils import apply_common_style

st.set_page_config(page_title="분석", page_icon="📊", layout="wide")
apply_common_style()