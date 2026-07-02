"""
database/create_table.py
────────────────────────
parking_project DB + 테이블 생성

테이블:
  parking        주차장 기본정보 + 요금
  parking_score  난이도 점수 + 역세권 + 혼잡도
  subway_station 지하철역 좌표
  parking_review 네이버 리뷰 (크롤링용)

실행:
  python database/create_table.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pymysql
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

CREATE_DB = f"""
    CREATE DATABASE IF NOT EXISTS `{DB_NAME}`
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
"""

TABLES = {}

# ── 1. parking ──────────────────────────────────────────────────
TABLES["parking"] = """
CREATE TABLE IF NOT EXISTS `parking` (
    `pk_code`           VARCHAR(30)     NOT NULL            COMMENT '주차장코드',
    `pk_name`           VARCHAR(100)    DEFAULT NULL        COMMENT '주차장명',
    `pk_address`        VARCHAR(255)    DEFAULT NULL        COMMENT '주소',
    `phone`             VARCHAR(30)     DEFAULT NULL        COMMENT '전화번호',
    `pk_type_cd`        VARCHAR(10)     DEFAULT NULL        COMMENT '주차장종류코드(NW/NS)',
    `pk_type_nm`        VARCHAR(30)     DEFAULT NULL        COMMENT '주차장종류명',
    `oper_se`           VARCHAR(10)     DEFAULT NULL        COMMENT '운영구분코드',
    `oper_se_nm`        VARCHAR(50)     DEFAULT NULL        COMMENT '운영구분명',
    `fee_type`          VARCHAR(10)     DEFAULT NULL        COMMENT '유무료구분(Y/N)',
    `parking_space`     INT             DEFAULT NULL        COMMENT '주차구획수',
    `basic_fee`         DECIMAL(10,2)   DEFAULT NULL        COMMENT '기본요금(원)',
    `basic_time`        DECIMAL(10,2)   DEFAULT NULL        COMMENT '기본시간(분)',
    `extra_fee`         DECIMAL(10,2)   DEFAULT NULL        COMMENT '추가요금(원)',
    `extra_time`        DECIMAL(10,2)   DEFAULT NULL        COMMENT '추가단위시간(분)',
    `daily_max_fee`     DECIMAL(10,2)   DEFAULT NULL        COMMENT '일최대요금(원)',
    `monthly_fee`       DECIMAL(10,2)   DEFAULT NULL        COMMENT '월정기권(원)',
    `weekday_start`     VARCHAR(6)      DEFAULT NULL        COMMENT '평일운영시작',
    `weekday_end`       VARCHAR(6)      DEFAULT NULL        COMMENT '평일운영종료',
    `weekend_start`     VARCHAR(6)      DEFAULT NULL        COMMENT '주말운영시작',
    `weekend_end`       VARCHAR(6)      DEFAULT NULL        COMMENT '주말운영종료',
    `holi_start`        VARCHAR(6)      DEFAULT NULL        COMMENT '공휴일운영시작',
    `holi_end`          VARCHAR(6)      DEFAULT NULL        COMMENT '공휴일운영종료',
    `latitude`          DECIMAL(10,7)   DEFAULT NULL        COMMENT '위도',
    `longitude`         DECIMAL(10,7)   DEFAULT NULL        COMMENT '경도',
    `coord_src`         VARCHAR(10)     DEFAULT NULL        COMMENT '좌표출처',
    `ev_charge_yn`      CHAR(1)         DEFAULT 'N'         COMMENT '전기차 충전 가능 여부(Y/N)',
    `collected_at`      DATETIME        DEFAULT NULL        COMMENT '수집일시',
    PRIMARY KEY (`pk_code`),
    INDEX `idx_address`   (`pk_address`(100)),
    INDEX `idx_location`  (`latitude`, `longitude`),
    INDEX `idx_fee`       (`basic_fee`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='주차장 기본정보'
"""

# ── 2. subway_station ───────────────────────────────────────────
TABLES["subway_station"] = """
CREATE TABLE IF NOT EXISTS `subway_station` (
    `id`            INT             NOT NULL AUTO_INCREMENT,
    `station_name`  VARCHAR(50)     NOT NULL    COMMENT '역명',
    `line`          VARCHAR(30)     DEFAULT NULL COMMENT '호선',
    `latitude`      DECIMAL(10,7)   NOT NULL    COMMENT '위도',
    `longitude`     DECIMAL(10,7)   NOT NULL    COMMENT '경도',
    PRIMARY KEY (`id`),
    INDEX `idx_name`     (`station_name`),
    INDEX `idx_location` (`latitude`, `longitude`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='지하철역 좌표'
"""

# ── 3. parking_score ────────────────────────────────────────────
TABLES["parking_score"] = """
CREATE TABLE IF NOT EXISTS `parking_score` (
    `id`                    INT         NOT NULL AUTO_INCREMENT,
    `pk_code`               VARCHAR(30) NOT NULL    COMMENT '주차장코드(FK)',
    `nearest_station_id`    INT         DEFAULT NULL COMMENT '최근접역ID(FK)',
    `nearest_station_name`  VARCHAR(50) DEFAULT NULL COMMENT '최근접역명',
    `nearest_station_line`  VARCHAR(30) DEFAULT NULL COMMENT '최근접역호선',
    `nearest_station_m`     INT         DEFAULT NULL COMMENT '최근접역거리(m)',
    `in_subway_radius`      CHAR(1)     DEFAULT NULL COMMENT '역세권여부(Y/N)',
    `fee_score`             INT         DEFAULT NULL COMMENT '요금점수(0~40)',
    `capacity_score`        INT         DEFAULT NULL COMMENT '면수점수(0~30)',
    `subway_score`          INT         DEFAULT NULL COMMENT '역세권점수(0~30)',
    `difficulty_score`      INT         DEFAULT NULL COMMENT '난이도점수(0~100)',
    `difficulty_grade`      VARCHAR(10) DEFAULT NULL COMMENT '난이도등급',
    -- 평일 혼잡도 (구간별 최고값)
    `wd_dawn`               VARCHAR(6)  DEFAULT NULL COMMENT '평일새벽(00~05)',
    `wd_morning`            VARCHAR(6)  DEFAULT NULL COMMENT '평일아침(06~09)',
    `wd_forenoon`           VARCHAR(6)  DEFAULT NULL COMMENT '평일오전(10~12)',
    `wd_afternoon`          VARCHAR(6)  DEFAULT NULL COMMENT '평일오후(13~16)',
    `wd_evening`            VARCHAR(6)  DEFAULT NULL COMMENT '평일저녁(17~19)',
    `wd_night`              VARCHAR(6)  DEFAULT NULL COMMENT '평일밤(20~23)',
    -- 주말 혼잡도 (구간별 최고값)
    `we_dawn`               VARCHAR(6)  DEFAULT NULL COMMENT '주말새벽(00~05)',
    `we_morning`            VARCHAR(6)  DEFAULT NULL COMMENT '주말아침(06~09)',
    `we_forenoon`           VARCHAR(6)  DEFAULT NULL COMMENT '주말오전(10~12)',
    `we_afternoon`          VARCHAR(6)  DEFAULT NULL COMMENT '주말오후(13~16)',
    `we_evening`            VARCHAR(6)  DEFAULT NULL COMMENT '주말저녁(17~19)',
    `we_night`              VARCHAR(6)  DEFAULT NULL COMMENT '주말밤(20~23)',
    `scored_at`             DATETIME    DEFAULT CURRENT_TIMESTAMP COMMENT '점수계산일시',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_pk_code` (`pk_code`),
    CONSTRAINT `fk_score_parking`
        FOREIGN KEY (`pk_code`) REFERENCES `parking`(`pk_code`)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_score_station`
        FOREIGN KEY (`nearest_station_id`) REFERENCES `subway_station`(`id`)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX `idx_difficulty` (`difficulty_score`),
    INDEX `idx_grade`      (`difficulty_grade`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='주차장 난이도 점수'
"""


def main():
    print("=" * 55)
    print("  DB / 테이블 생성")
    print("=" * 55)

    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_DB)
            print(f"✅ DB: `{DB_NAME}`")
            cur.execute(f"USE `{DB_NAME}`")
            for name, ddl in TABLES.items():
                cur.execute(ddl)
                print(f"✅ 테이블: `{name}`")
        conn.commit()
        print(f"\n 완료! DBeaver에서 {DB_NAME} 새로고침(F5)하세요.")
    except Exception as e:
        print(f"❌ 오류: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()