"""
database/select_data_test.py

[역할]
- DB에서 주차장 관련 데이터를 조회하는 함수 모음
- Streamlit 화면에서 사용하는 데이터 쿼리 담당

[기능]
1. parking 테이블 전체 조회
2. 조건 검색 (주소, 요금, 이름 등)
3. parking + parking_score 조인 데이터 조회
4. parking + parking_score + parking_review(카카오 리뷰) 조인 데이터 조회
5. 사용자 직접 작성 리뷰(user_review) 등록 / 조회
6. 카카오 리뷰 + 사용자 리뷰를 함께 보여주는 통합 조회
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
        p.ev_charge_yn           AS 전기차충전소여부,
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
# 5. parking + parking_score + parking_review(카카오 리뷰) 조인
# ---------------------------------------------------------
def get_parking_with_review():
    """
    [역할]
    - parking + parking_score + parking_review 3개 테이블 조인
    - 별점/리뷰건수/URL 포함 (카카오에서 수집한 리뷰)
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


# ---------------------------------------------------------
# 6. 사용자 직접 작성 리뷰 (user_review) 관련
# ---------------------------------------------------------
#
# [필요 테이블 - 없다면 아래 SQL로 먼저 생성]
#
# CREATE TABLE IF NOT EXISTS user_review (
#     id          INT AUTO_INCREMENT PRIMARY KEY,
#     pk_code     VARCHAR(50)  NOT NULL,          -- parking.pk_code FK
#     user_name   VARCHAR(50)  NOT NULL,          -- 작성자 (닉네임/아이디)
#     rating      TINYINT      NOT NULL,          -- 1~5점
#     comment     TEXT         NULL,              -- 리뷰 내용
#     created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (pk_code) REFERENCES parking(pk_code)
# );

def add_user_review(pk_code, user_name, rating, comment):
    """
    [역할]
    - 사용자가 특정 주차장에 대해 작성한 리뷰를 user_review 테이블에 저장
    [사용처]
    - Streamlit 리뷰 작성 폼 (2번 기능)
    [Parameter]
    pk_code   : str   - 주차장 코드
    user_name : str   - 작성자명/닉네임
    rating    : int   - 1~5점 평점
    comment   : str   - 리뷰 내용
    [Return]
    - bool (성공 여부)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
        INSERT INTO user_review (pk_code, user_name, rating, comment)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (pk_code, user_name, rating, comment))
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        conn.rollback()
        print(f"[add_user_review] 리뷰 저장 실패: {e}")
        return False
    finally:
        conn.close()


def get_user_reviews(pk_code=None):
    """
    [역할]
    - user_review 테이블에서 리뷰 조회
    - pk_code를 지정하면 해당 주차장 리뷰만, 없으면 전체 조회
    [사용처]
    - 주차장 상세 페이지에서 사용자가 남긴 리뷰 목록 표시
    [Parameter]
    pk_code : str or None
    [Return]
    - pandas.DataFrame
    """
    conn = get_connection()
    if pk_code:
        query = """
        SELECT id, pk_code, user_name, rating, comment, created_at
        FROM user_review
        WHERE pk_code = %s
        ORDER BY created_at DESC
        """
        df = pd.read_sql(query, conn, params=(pk_code,))
    else:
        query = """
        SELECT id, pk_code, user_name, rating, comment, created_at
        FROM user_review
        ORDER BY created_at DESC
        """
        df = pd.read_sql(query, conn)
    conn.close()
    return df


# ---------------------------------------------------------
# 7. parking + parking_score + 카카오리뷰 + 사용자리뷰(집계) 통합 조회
# ---------------------------------------------------------
def get_parking_with_all_reviews():
    """
    [역할]
    - parking + parking_score + parking_review(카카오) + user_review(사용자, 집계)
      를 모두 합쳐서 조회
    - 사용자 리뷰는 평균 별점(내 리뷰 평균)과 리뷰 개수로 집계해서 붙임
    [사용처]
    - 메인 대시보드/상세 페이지에서 카카오 평점과 우리 서비스 사용자 평점을 함께 표시
    [Return]
    - pandas.DataFrame
      (컬럼: ..., 카카오별점, 카카오리뷰수, 사용자평균별점, 사용자리뷰수)
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
        r.rating                AS 카카오별점,
        r.review_count          AS 카카오리뷰수,
        ur.avg_rating           AS 사용자평균별점,
        ur.review_cnt           AS 사용자리뷰수
    FROM parking p
    LEFT JOIN parking_score s ON p.pk_code = s.pk_code
    LEFT JOIN parking_review r ON p.pk_code = r.pk_code
    LEFT JOIN (
        SELECT pk_code,
               ROUND(AVG(rating), 1) AS avg_rating,
               COUNT(*)              AS review_cnt
        FROM user_review
        GROUP BY pk_code
    ) ur ON p.pk_code = ur.pk_code
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df