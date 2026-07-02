"""
database/create_review_table.py

[역할]
- parking_review 테이블 생성
- 주차장별 리뷰 요약 (별점 평균, 리뷰 건수, URL)

[ERD 관계]
parking (pk_code) ──1:1──> parking_review (pk_code)

[실행]
python database/create_review_table.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


CREATE_PARKING_REVIEW = """
CREATE TABLE IF NOT EXISTS `parking_review` (
    `id`           INT          NOT NULL AUTO_INCREMENT,
    `pk_code`      VARCHAR(30)  NOT NULL                  COMMENT '주차장코드(FK)',
    `rating`       DECIMAL(3,1) DEFAULT NULL              COMMENT '별점 평균 (0.0 ~ 5.0)',
    `review_count` INT          DEFAULT NULL              COMMENT '리뷰 건수',
    `url`          VARCHAR(500) DEFAULT NULL              COMMENT '리뷰 페이지 URL',
    `review_url`   VARCHAR(500) DEFAULT NULL              COMMENT '카카오맵_후기_URL',
    `crawled_at`   DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '크롤링 일시',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_pk_code` (`pk_code`),
    CONSTRAINT `fk_parking_review`
        FOREIGN KEY (`pk_code`)
        REFERENCES `parking` (`pk_code`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    INDEX `idx_rating` (`rating`),
    INDEX `idx_count`  (`review_count`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='주차장별 리뷰 요약 (별점/건수/URL)'
"""


def main():
    print("=" * 55)
    print("  ⭐ parking_review 테이블 생성")
    print("=" * 55)

    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        db=DB_NAME, charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_PARKING_REVIEW)
            print("✅ 테이블 생성: `parking_review`")
        conn.commit()
        print(f"\n🎉 완료! DBeaver에서 {DB_NAME} 새로고침(F5)하세요.")
        print("\n【ERD 관계】")
        print("parking (pk_code) ──1:1──> parking_review (pk_code)")
    except Exception as e:
        print(f"❌ 오류: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()