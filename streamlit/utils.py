"""
utils.py

[역할]
- 전 페이지 공통으로 사용하는 유틸 함수 모음
- 공통 CSS 스타일 적용 함수 포함
- 사이드바 네비게이션은 app.py의 st.navigation()이 담당
"""
"""
모든 페이지에서 공통으로 적용할 CSS 스타일
각 페이지 상단에서 apply_common_style() 한 줄로 호출하면 됨
"""
import streamlit as st


def apply_common_style():
    st.markdown(
        """
        <style>
        #MainMenu, footer { visibility: hidden; }

        /* ---- 사이드바 ---- */
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
        }
        section[data-testid="stSidebar"] * {
            color: #e5e7eb;
        }

        /* ---- 공통 헤더 박스 ---- */
        .map-header {
            padding: 1.2rem 1.6rem;
            border-radius: 14px;
            background: linear-gradient(135deg, #1d4ed8 0%, #1e3a8a 100%);
            color: white;
            margin-bottom: 1rem;
        }
        .map-header h1 { margin: 0; font-size: 1.6rem; }
        .map-header p  { margin: 0.3rem 0 0 0; opacity: 0.85; font-size: 0.92rem; }

        /* ---- 통계 카드 ---- */
        .stat-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1.1rem 1.3rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.25);
        }
        .stat-card .label { font-size: 0.85rem; color: #94a3b8; margin-bottom: 4px; }
        .stat-card .value { font-size: 1.7rem; font-weight: 700; color: #f1f5f9; }
        .stat-card .sub   { font-size: 0.78rem; color: #64748b; margin-top: 2px; }

        /* ---- 등급 뱃지 ---- */
        .legend-chip {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
            color: white;
            margin-right: 6px;
        }

        /* ---- 버튼 공통 ---- */
        .stButton button {
            height: 2.7rem;
            width: 100%;
            border-radius: 10px;
            border: 1px solid #334155;
            background: #1e293b;
            color: #f1f5f9 !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            padding: 0 1rem;
            box-sizing: border-box;
            line-height: 1 !important;
        }
        .stButton button:hover {
            border-color: #3b82f6;
            color: #3b82f6 !important;
        }

        /* ---- page_link를 버튼과 동일한 모양으로 ---- */
        div[data-testid="stPageLink"] {
            height: 2.7rem;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            border: 1px solid #334155;
            background: #1e293b;
            box-sizing: border-box;
            padding: 0;
        }
        div[data-testid="stPageLink"]:hover { border-color: #3b82f6; }
        div[data-testid="stPageLink"] a {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            line-height: 1 !important;
            color: #f1f5f9 !important;
        }
        div[data-testid="stPageLink"] a *,
        div[data-testid="stPageLink"] a span,
        div[data-testid="stPageLink"] a p {
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            line-height: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stPageLink"]:hover a,
        div[data-testid="stPageLink"]:hover a * { color: #3b82f6 !important; }
        div[data-testid="stPageLink"] svg { display: none; }

        /* ---- 첫 화면 검색창 ---- */
        .hero-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 58vh;
        }
        .hero-title {
            font-size: 1.9rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 0.3rem;
            text-align: center;
        }
        .hero-sub {
            font-size: 0.95rem;
            color: #94a3b8;
            margin-bottom: 1.8rem;
            text-align: center;
        }
        div[data-testid="stForm"] {
            border: 1px solid #334155;
            border-radius: 18px;
            padding: 0.5rem 0.6rem;
            background: #1e293b;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        div[data-testid="stForm"] input {
            border: none !important;
            box-shadow: none !important;
            font-size: 1.02rem;
            background: transparent !important;
            color: #f1f5f9 !important;
        }
        div[data-testid="stForm"] input:focus {
            outline: none !important;
            box-shadow: none !important;
        }
        .hero-hint {
            margin-top: 1rem;
            font-size: 0.82rem;
            color: #64748b;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )