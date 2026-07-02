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
import datetime


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

        /* ---- 사이드바: 내 차 확인하기 ---- */
        .car-check-box {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.9rem;
        }
        .car-check-title {
            font-size: 1rem;
            font-weight: 700;
            color: #f1f5f9 !important;
            margin-bottom: 0.2rem;
        }
        .car-check-sub {
            font-size: 0.76rem;
            color: #94a3b8 !important;
            margin-bottom: 0.2rem;
            line-height: 1.4;
        }
        .car-result-ok, .car-result-bad {
            margin-top: 0.7rem;
            padding: 0.55rem 0.7rem;
            border-radius: 10px;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .car-result-ok {
            background: rgba(34,197,94,0.15);
            border: 1px solid rgba(34,197,94,0.4);
            color: #4ade80 !important;
        }
        .car-result-bad {
            background: rgba(239,68,68,0.15);
            border: 1px solid rgba(239,68,68,0.4);
            color: #f87171 !important;
        }
        .week-row { display: flex; gap: 4px; margin-top: 0.6rem; }
        .day-chip {
            flex: 1;
            text-align: center;
            border-radius: 10px;
            padding: 0.4rem 0.1rem;
            background: #0f172a;
            border: 1px solid #334155;
        }
        .day-chip.today { border-color: #3b82f6; background: #1e2a4a; }
        .day-chip .dow { font-size: 0.7rem; color: #94a3b8 !important; }
        .day-chip .dom { font-size: 0.9rem; font-weight: 700; color: #f1f5f9 !important; margin: 1px 0; }
        .day-chip .stat { font-size: 0.66rem; font-weight: 700; }
        .day-chip .stat.ok { color: #4ade80 !important; }
        .day-chip .stat.no { color: #f87171 !important; }

        /* ---- 제외 대상 차량 ---- */
        .exempt-title {
            font-size: 0.88rem;
            font-weight: 700;
            color: #f1f5f9 !important;
            margin-bottom: 0.55rem;
        }
        .exempt-chip {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            background: #0f172a;
            border: 1px solid #334155;
            color: #93c5fd !important;
            font-size: 0.76rem;
            font-weight: 600;
            margin: 0 4px 6px 0;
        }
        .exempt-note {
            font-size: 0.74rem;
            color: #94a3b8 !important;
            margin-top: 0.3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================================
# 🚗 사이드바 - 내 차 확인하기 (차량 5부제 조회)
# =========================================================================
WEEKDAY_KOR = ["월", "화", "수", "목", "금", "토", "일"]


def _buje_group(n: int) -> int:
    """차량 5부제 그룹 번호 계산 (끝자리 0·5 / 1·6 / 2·7 / 3·8 / 4·9)"""
    return n % 5


def render_car_restriction_sidebar():
    """
    사이드바 상단에 '내 차 확인하기' 위젯을 렌더링한다.

    - 위: 차량번호 끝자리 입력/조회
    - 아래: 이번 주(월~금) 차량 5부제 제한 현황
      (날짜 끝자리와 차량번호 끝자리가 같은 그룹이면 해당 요일 운행 제한)
    """
    with st.sidebar:
        st.markdown(
            """
            <div class="car-check-box">
                <div class="car-check-title">🚗 내 차 확인하기</div>
                <div class="car-check-sub">번호판 끝 4자리를 입력하면<br>차량 5부제 제한 여부를 확인해요.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        car_number = st.text_input(
            "번호판 끝 4자리",
            max_chars=4,
            placeholder="예: 2312",
            label_visibility="collapsed",
            key="car_last4_input",
        )
        st.button("🔍 조회", use_container_width=True, key="car_check_btn")

        digits = "".join(ch for ch in (car_number or "") if ch.isdigit())

        if digits:
            last_digit = int(digits[-1])
            group = _buje_group(last_digit)

            today = datetime.date.today()
            monday = today - datetime.timedelta(days=today.weekday())
            week_days = [monday + datetime.timedelta(days=i) for i in range(5)]  # 월~금

            chips_html = ""
            for d in week_days:
                restricted = _buje_group(d.day) == group
                cls = "day-chip today" if d == today else "day-chip"
                stat_cls = "no" if restricted else "ok"
                stat_txt = "제한" if restricted else "가능"
                chips_html += f"""
                <div class="{cls}">
                    <div class="dow">{WEEKDAY_KOR[d.weekday()]}</div>
                    <div class="dom">{d.day}</div>
                    <div class="stat {stat_cls}">{stat_txt}</div>
                </div>
                """

            if today.weekday() >= 5:
                result_html = f'<div class="car-result-ok">끝번호 {last_digit} — 오늘은 주말이라 제한이 없어요 🙆</div>'
            elif _buje_group(today.day) == group:
                result_html = f'<div class="car-result-bad">끝번호 {last_digit} — 오늘은 5부제 제한일이에요 🚫</div>'
            else:
                result_html = f'<div class="car-result-ok">끝번호 {last_digit} — 오늘 이용 가능해요 ✅</div>'

            st.markdown(
                f"""
                <div class="car-check-box">
                    <div class="car-check-title" style="font-size:0.88rem;">이번 주 제한 현황</div>
                    <div class="car-check-sub">끝번호 {last_digit} 기준</div>
                    <div class="week-row">{chips_html}</div>
                    {result_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("번호판 끝자리를 입력하면 이번 주 제한 현황을 볼 수 있어요.")

        # ── 3) 제외 대상 차량 안내 (항상 표시) ──────────────
        exempt_vehicles = ["장애인 차량", "전기차", "수소차", "긴급 차량", "임산부 차량", "영유아 차량"]
        exempt_chips_html = "".join(f'<span class="exempt-chip">{v}</span>' for v in exempt_vehicles)

        st.markdown(
            f"""
            <div class="car-check-box">
                <div class="exempt-title">제외 대상 차량</div>
                <div>{exempt_chips_html}</div>
                <div class="exempt-note">위 차량은 요일에 관계없이 이용 가능합니다.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )