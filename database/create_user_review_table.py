"""
database/create_user_review_table.py

[역할]
- user_review 테이블이 없을 경우 생성
- 최초 1회만 실행하면 됨 (python database/create_user_review_table.py)
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection


def create_user_review_table():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = """
        CREATE TABLE IF NOT EXISTS user_review (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            pk_code     VARCHAR(50)  NOT NULL,
            user_name   VARCHAR(50)  NOT NULL,
            rating      TINYINT      NOT NULL,
            comment     TEXT         NULL,
            created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pk_code) REFERENCES parking(pk_code)
        )
        """
        cursor.execute(query)
        conn.commit()
        cursor.close()
        print("user_review 테이블 생성 완료 (이미 있으면 무시됨)")
    except Exception as e:
        conn.rollback()
        print(f"테이블 생성 실패: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    create_user_review_table()