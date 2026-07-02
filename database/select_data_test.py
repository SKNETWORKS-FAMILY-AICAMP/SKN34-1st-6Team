"""
database/select_data_test.py

[역할]
- DB에서 주차장 관련 데이터를 조회하는 함수 모음
- Streamlit 화면에서 사용하는 데이터 쿼리 담당

[기능]
1. parking 테이블 전체 조회
2. 조건 검색 (주소, 요금, 이름 등)
3. parking + parking_score 조인 데이터 조회
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
import pandas as pd


# ---------------------------------------------------------
# 1. 전체 주차장 데이터 조회
# ---------------------------------------------------------
def get_all_parking():
    """
    [역할]
    - parking 테이블 전체 데이터를 조회
    [사용처]
    - Streamlit 초기 화면 리스트 표시
    [Return]
    - pandas.DataFrame
    """
    conn = get_connection()
    query = "SELECT * FROM parking"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# ---------------------------------------------------------
# 2. 주소(지역) 기준 검색
# ---------------------------------------------------------
def get_parking_by_address(keyword):
    """
    [역할]
    - 주차장 주소에서 키워드로 검색
    [예시]
    - '강남', '마포', '홍대' 등
    [Parameter]
    keyword : str
    [Return]
    - pandas.DataFrame
    """
    conn = get_connection()
    query = """
    SELECT *
    FROM parking
    WHERE pk_address LIKE %s
    """
    df = pd.read_sql(query, conn, params=(f"%{keyword}%",))
    conn.close()
    return df


# ---------------------------------------------------------
# 3. 요금 기준 필터 조회
# ---------------------------------------------------------
def get_parking_by_fee(max_fee):
    """
    [역할]
    - 기본 요금 기준으로 주차장 필터링
    [예시]
    - 2000원 이하 주차장 조회
    [Parameter]
    max_fee : int / float
    [Return]
    - pandas.DataFrame
    """
    conn = get_connection()
    query = """
    SELECT *
    FROM parking
    WHERE basic_fee <= %s
    """
    df = pd.read_sql(query, conn, params=(max_fee,))
    conn.close()
    return df



# ---------------------------------------------------------
# 4. parking + parking_score 조인 데이터 조회
# ---------------------------------------------------------

def get_parking_with_score():
    """
    [역할]
    - parking 테이블과 parking_score 테이블을 LEFT JOIN하여 조회
    - 난이도 등급, 혼잡도, 역세권 정보 포함
    [사용처]
    - Streamlit 메인 대시보드, 지도 페이지
    [Return]
    - pandas.DataFrame
    """
    conn = get_connection()
    query = """
    SELECT
        p.pk_code,
        p.pk_name,
        p.pk_address,
        p.phone,
        p.pk_type_nm,
        p.oper_se_nm,
        p.fee_type,
        p.parking_space,
        p.basic_fee,
        p.basic_time,
        p.extra_fee,
        p.daily_max_fee,
        p.monthly_fee,
        p.weekday_start,
        p.weekday_end,
        p.weekend_start,
        p.weekend_end,
        p.latitude,
        p.longitude,
        p.collected_at,
        s.nearest_station_name  AS 최근접역명,
        s.nearest_station_line  AS 최근접역호선,
        s.nearest_station_m     AS 최근접역거리,
        s.in_subway_radius      AS 역세권여부,
        s.fee_score             AS 요금점수,
        s.capacity_score        AS 면수점수,
        s.subway_score          AS 역세권점수,
        s.difficulty_score      AS 난이도점수,
        s.difficulty_grade      AS 난이도등급,
        s.wd_dawn, s.wd_morning, s.wd_forenoon,
        s.wd_afternoon, s.wd_evening, s.wd_night,
        s.we_dawn, s.we_morning, s.we_forenoon,
        s.we_afternoon, s.we_evening, s.we_night
    FROM parking p
    LEFT JOIN parking_score s ON p.pk_code = s.pk_code
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# ---------------------------------------------------------
# 5. parking + parking_score + parking_review 조인
# ---------------------------------------------------------
def get_parking_with_review():
    """
    [역할]
    - parking + parking_score + parking_review 3개 테이블 조인
    - 별점/리뷰건수/URL 포함
    [사용처]
    - 분석 페이지, 혼잡도 페이지
    [Return]
    - pandas.DataFrame
    """
    conn = get_connection()
    query = """
    SELECT
        p.pk_code,
        p.pk_name,
        p.pk_address,
        p.fee_type,
        p.parking_space,
        p.basic_fee,
        p.latitude,
        p.longitude,
        s.nearest_station_name  AS 최근접역명,
        s.difficulty_grade      AS 난이도등급,
        s.difficulty_score      AS 난이도점수,
        s.in_subway_radius      AS 역세권여부,
        s.wd_dawn, s.wd_morning, s.wd_forenoon,
        s.wd_afternoon, s.wd_evening, s.wd_night,
        s.we_dawn, s.we_morning, s.we_forenoon,
        s.we_afternoon, s.we_evening, s.we_night,
        r.rating                AS 별점,
        r.review_count          AS 리뷰수,
        r.url                   AS 카카오URL,
        r.review_url            AS 리뷰URL
    FROM parking p
    LEFT JOIN parking_score  s ON p.pk_code = s.pk_code
    LEFT JOIN parking_review r ON p.pk_code = r.pk_code
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df