"""
home.py

[역할]
- 홈 화면: 첫 진입 시 검색창, 검색 후 통계 + 정보 표시

[구성]
1. 첫 화면: 중앙 검색창 (이름 / 주소 / 최근접역명 통합 검색)
2. 검색 후: 통계 카드 + 등급 분포 + 데이터 테이블
3. 테이블에서 주차장 행을 선택하면 하단에 해당 주차장 리뷰 작성/조회 섹션 표시
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =========================
# 📌 라이브러리 import
# =========================
import streamlit as st
import pandas as pd

from database.select_data_test import get_parking_with_score, get_user_reviews
from database.insert_user_review import insert_user_review
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
    """
    이름 / 주소 / 최근접역명을 통합해서 검색
    - 역명은 '역' 접미사 유무에 상관없이, 양방향(포함관계)으로 매칭
      예: 검색어 '강남역' ↔ 데이터 '강남'  → 매칭됨
          검색어 '강남'   ↔ 데이터 '강남역' → 매칭됨
    """
    if not query:
        return data

    query = query.strip()
    query_norm = query[:-1] if query.endswith("역") else query  # '강남역' -> '강남'

    mask = pd.Series(False, index=data.index)

    # 이름 / 주소는 기존처럼 단순 포함 검색
    for c in ["pk_name", "pk_address"]:
        if c in data.columns:
            mask |= data[c].astype(str).str.contains(query, case=False, na=False)

    # 최근접역명은 '역' 접미사를 떼고 양방향으로 비교 (인접권역 기반 매칭)
    if "최근접역명" in data.columns:
        station = data["최근접역명"].astype(str)
        station_norm = station.str.replace("역", "", regex=False)

        mask |= station.str.contains(query, case=False, na=False)
        mask |= station_norm.str.contains(query_norm, case=False, na=False)
        # 데이터 쪽 역명이 검색어보다 짧은 경우(예: 데이터 '강남' vs 검색어 '강남역')도 매칭되도록 반대 방향도 확인
        mask |= station_norm.apply(lambda s: s != "" and s in query_norm)

    return data[mask]


def render_stars(rating):
    rating = int(round(rating))
    return "⭐" * rating + "☆" * (5 - rating)


def render_review_section(pk_code, pk_name):
    """선택된 주차장에 대한 리뷰 작성 폼 + 기존 리뷰 목록"""
    st.subheader(f"💬 {pk_name} 리뷰")

    with st.form(key=f"review_form_{pk_code}", clear_on_submit=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            user_name = st.text_input("닉네임", max_chars=20, placeholder="예: 홍길동")
        with col2:
            rating = st.slider("별점", min_value=1, max_value=5, value=5)

        comment = st.text_area("리뷰 내용", placeholder="주차 편의성, 요금, 접근성 등 자유롭게 남겨주세요.")

        submitted = st.form_submit_button("리뷰 등록")

        if submitted:
            if not user_name.strip():
                st.warning("닉네임을 입력해주세요.")
            elif not comment.strip():
                st.warning("리뷰 내용을 입력해주세요.")
            else:
                result = insert_user_review(pk_code, user_name.strip(), rating, comment.strip())
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])

    reviews_df = get_user_reviews(pk_code)

    if reviews_df.empty:
        st.info("아직 등록된 리뷰가 없습니다. 첫 리뷰를 남겨보세요!")
        return

    avg_rating = round(reviews_df["rating"].mean(), 1)
    st.markdown(f"**평균 별점: {render_stars(avg_rating)} ({avg_rating}점 / {len(reviews_df)}개 리뷰)**")

    for _, row in reviews_df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{row['user_name']}**")
            with c2:
                st.markdown(render_stars(row["rating"]))
            st.write(row["comment"])
            st.caption(str(row["created_at"]))


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
# 📋 데이터 테이블 출력 (버튼으로 선택)
# =========================
st.subheader("📋 주차장 정보")

if "selected_pk_code" not in st.session_state:
    st.session_state.selected_pk_code = None
if "selected_pk_name" not in st.session_state:
    st.session_state.selected_pk_name = None

show_cols = [
    "pk_code", "pk_name", "pk_address", "fee_type", "basic_fee",
    "parking_space", "난이도등급", "최근접역명",
]
show_cols = [c for c in show_cols if c in base_df.columns]

col_rename = {
    "pk_code":       "코드",
    "pk_name":       "주차장명",
    "pk_address":    "주소",
    "fee_type":      "요금유형",
    "basic_fee":     "기본요금",
    "parking_space": "주차면수",
    "난이도등급":    "난이도",
    "최근접역명":    "인근 지하철역",
}

table_df = base_df[show_cols].rename(columns=col_rename).reset_index(drop=True)

ROW_COL_WIDTHS = [1, 2, 3, 1.2, 1, 1, 1, 1.5]
ROW_HEADERS = ["", "주차장명", "주소", "요금유형", "기본요금", "주차면수", "난이도", "인근 지하철역"]


def render_table_row(row, key_suffix):
    row_cols = st.columns(ROW_COL_WIDTHS)
    is_selected = st.session_state.selected_pk_code == row["코드"]
    btn_label = "✅" if is_selected else "선택"
    if row_cols[0].button(btn_label, key=f"select_btn_{row['코드']}_{key_suffix}", use_container_width=True):
        if is_selected:
            st.session_state.selected_pk_code = None
            st.session_state.selected_pk_name = None
        else:
            st.session_state.selected_pk_code = row["코드"]
            st.session_state.selected_pk_name = row["주차장명"]
        st.rerun()

    row_cols[1].write(row.get("주차장명", "-"))
    row_cols[2].write(row.get("주소", "-"))
    row_cols[3].write(row.get("요금유형", "-"))
    row_cols[4].write(row.get("기본요금", "-"))
    row_cols[5].write(row.get("주차면수", "-"))
    row_cols[6].write(row.get("난이도", "-"))
    row_cols[7].write(row.get("인근 지하철역", "-"))


if st.session_state.selected_pk_code:
    # ---- 선택된 주차장 1건만 표시 ----
    st.caption("선택된 주차장입니다. 다시 누르면 선택이 해제돼요.")

    header_cols = st.columns(ROW_COL_WIDTHS)
    for hc, h in zip(header_cols, ROW_HEADERS):
        hc.markdown(f"**{h}**")
    st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)

    matched = table_df[table_df["코드"] == st.session_state.selected_pk_code]
    if matched.empty:
        st.warning("선택한 주차장 정보를 찾을 수 없습니다. 선택이 초기화됩니다.")
        st.session_state.selected_pk_code = None
        st.session_state.selected_pk_name = None
        st.rerun()
    else:
        render_table_row(matched.iloc[0], key_suffix="selected")

else:
    # ---- 전체 목록 (페이지네이션) ----
    st.caption("목록에서 왼쪽 '선택' 버튼을 누르면 해당 주차장의 리뷰를 작성/확인할 수 있어요")

    PAGE_SIZE = 20
    total_rows = len(table_df)
    total_pages = max(1, (total_rows - 1) // PAGE_SIZE + 1)

    if "table_page" not in st.session_state:
        st.session_state.table_page = 1

    page = st.session_state.table_page
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_df = table_df.iloc[start_idx:end_idx]

    header_cols = st.columns(ROW_COL_WIDTHS)
    for hc, h in zip(header_cols, ROW_HEADERS):
        hc.markdown(f"**{h}**")
    st.markdown("<hr style='margin: 4px 0;'>", unsafe_allow_html=True)

    for idx, row in page_df.iterrows():
        render_table_row(row, key_suffix=idx)

    if total_pages > 1:
        st.write("")
        pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
        with pcol1:
            if st.button("◀ 이전", disabled=(page <= 1), use_container_width=True):
                st.session_state.table_page -= 1
                st.rerun()
        with pcol2:
            st.markdown(f"<div style='text-align:center;'>{page} / {total_pages} 페이지 (전체 {total_rows}곳)</div>", unsafe_allow_html=True)
        with pcol3:
            if st.button("다음 ▶", disabled=(page >= total_pages), use_container_width=True):
                st.session_state.table_page += 1
                st.rerun()

st.divider()

# =========================
# 💬 선택된 주차장 리뷰 섹션
# =========================
if st.session_state.selected_pk_code:
    render_review_section(st.session_state.selected_pk_code, st.session_state.selected_pk_name)
else:
    st.info("👆 위 목록에서 주차장을 선택하면 리뷰를 작성하거나 볼 수 있어요.")