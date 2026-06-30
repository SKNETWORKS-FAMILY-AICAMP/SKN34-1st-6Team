"""
select_data.py

[역할]
- DB에서 주차장 데이터를 조회하는 모듈
- Streamlit 화면에서 사용할 데이터 제공 역할

[기능]
1. parking 테이블 전체 조회
2. 조건 검색 (구/주소, 요금, 혼잡도 등)
3. 분석/시각화용 데이터 전달
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
    [설명]
    - parking 테이블 전체 데이터를 조회

    [사용처]
    - Streamlit 초기 화면 리스트 출력

    [Return]
    - pandas.DataFrame
    """
    conn = get_connection()

    query = "SELECT * FROM parking"

    df = pd.read_sql(query, conn)

    conn.close()
    return df


# ---------------------------------------------------------
# 2. 주소(지역) 기반 검색
# ---------------------------------------------------------
def get_parking_by_address(keyword):
    """
    [설명]
    - 주차장 주소에서 키워드 검색

    [예시]
    - '강남', '마포', '종로' 등

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
    [설명]
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