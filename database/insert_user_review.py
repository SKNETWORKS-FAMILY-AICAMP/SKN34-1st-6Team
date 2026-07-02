"""
database/insert_user_review.py

[역할]
- Streamlit에서 사용자가 작성한 리뷰를 user_review 테이블에 바로 INSERT
- 리뷰 작성 폼(review_ui.py 등)에서 호출하여 사용

[사전 조건]
- database/create_user_review_table.py 를 먼저 실행해서 user_review 테이블이 생성되어 있어야 함
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def insert_user_review(pk_code, user_name, rating, comment):
    """
    [역할]
    - 사용자가 작성한 리뷰 1건을 user_review 테이블에 저장
    [사용처]
    - Streamlit 리뷰 작성 폼 제출 시 호출
    [Parameter]
    pk_code   : str  - 주차장 코드 (parking.pk_code)
    user_name : str  - 작성자 닉네임
    rating    : int  - 1~5점 평점
    comment   : str  - 리뷰 내용
    [Return]
    - dict : {"success": bool, "message": str}
    """
    # 입력값 기본 검증
    if not pk_code or not user_name or not comment:
        return {"success": False, "message": "필수 입력값이 누락되었습니다."}

    if not (1 <= int(rating) <= 5):
        return {"success": False, "message": "평점은 1~5점 사이여야 합니다."}

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO user_review (pk_code, user_name, rating, comment)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (pk_code, user_name.strip(), int(rating), comment.strip()))
        conn.commit()
        cursor.close()
        return {"success": True, "message": "리뷰가 등록되었습니다."}

    except Exception as e:
        if conn:
            conn.rollback()
        return {"success": False, "message": f"리뷰 등록 실패: {e}"}

    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------
# 단독 실행 테스트용
# ---------------------------------------------------------
if __name__ == "__main__":
    result = insert_user_review(
        pk_code="TEST001",
        user_name="테스트유저",
        rating=5,
        comment="테스트 리뷰입니다."
    )
    print(result)