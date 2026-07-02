"""
database/insert_review.py

[역할]
- data/processed/parking_review_crawled.csv → parking_review 테이블 적재

[테이블 컬럼]
pk_code, rating, review_count, url, review_url, crawled_at

[CSV 컬럼 매핑 - clean.py 출력 기준]
pk_code      → pk_code
pk_rate      → rating
pk_review    → review_count
pk_url       → url
pk_reviewurl → review_url

[실행]
python database/insert_review.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from pathlib import Path
from datetime import datetime

import pymysql
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DIR = Path("data/processed")
CSV_PATH      = PROCESSED_DIR / "parking_review_crawled.csv"
BATCH         = 500


# ---------------------------------------------------------
# DB 연결
# ---------------------------------------------------------
def get_connection():
    return pymysql.connect(
        host     = os.getenv("DB_HOST", "localhost"),
        port     = int(os.getenv("DB_PORT", 3306)),
        user     = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        database = os.getenv("DB_NAME"),
        charset  = "utf8mb4",
        autocommit = False,
    )


# ---------------------------------------------------------
# 유틸
# ---------------------------------------------------------
def _pk_code(v) -> str | None:
    try:
        return str(int(float(str(v).strip())))
    except (TypeError, ValueError):
        return None

def _rating(v) -> float | None:
    """0.0 → None(평가없음), 나머지 → float"""
    try:
        val = round(float(str(v).strip()), 1)
        return val if val > 0 else None
    except (TypeError, ValueError):
        return None

def _review_count(v) -> int | None:
    """0 → None, 나머지 → int"""
    try:
        val = int(float(str(v).strip()))
        return val if val > 0 else None
    except (TypeError, ValueError):
        return None

def _url(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() not in ("nan", "none", "", "평가없음", "없음") else None

def batch_execute(conn, sql: str, records: list, label: str):
    total = len(records)
    with conn.cursor() as cur:
        for i in range(0, total, BATCH):
            cur.executemany(sql, records[i : i + BATCH])
            conn.commit()
            done = min(i + BATCH, total)
            print(f"\r  [{label}] {done:,}/{total:,}", end="", flush=True)
    print(f"\r  ✅ {label}: {total:,}건 완료          ")


# ---------------------------------------------------------
# 리뷰 적재
# ---------------------------------------------------------
def insert_review(conn, csv_path: Path):
    print(f"\n【parking_review 적재】")
    print(f"  📂 입력: {csv_path}")

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    print(f"  📊 전체: {len(rows):,}건 로드")

    records    = []
    skipped    = 0
    has_review = 0
    no_review  = 0

    for row in rows:
        pk_code = _pk_code(row.get("pk_code"))
        if not pk_code:
            skipped += 1
            continue

        rating       = _rating(row.get("pk_rate"))
        review_count = _review_count(row.get("pk_review"))

        if rating or review_count:
            has_review += 1
        else:
            no_review += 1

        records.append({
            "pk_code":      pk_code,
            "rating":       rating,
            "review_count": review_count,
            "url":          _url(row.get("pk_url")),
            "review_url":   _url(row.get("pk_reviewurl")),
            "crawled_at":   datetime.now(),
        })

    print(f"  ⭐ 별점/리뷰 있음: {has_review}곳 / 평가없음: {no_review}곳")
    if skipped:
        print(f"  ⚠️  pk_code 변환 실패 건너뜀: {skipped}건")

    sql = """
        INSERT INTO parking_review
            (pk_code, rating, review_count, url, review_url, crawled_at)
        VALUES
            (%(pk_code)s, %(rating)s, %(review_count)s,
             %(url)s, %(review_url)s, %(crawled_at)s)
        ON DUPLICATE KEY UPDATE
            rating       = VALUES(rating),
            review_count = VALUES(review_count),
            url          = VALUES(url),
            review_url   = VALUES(review_url),
            crawled_at   = VALUES(crawled_at)
    """
    batch_execute(conn, sql, records, "parking_review")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    print("=" * 55)
    print("  ⭐ 리뷰 데이터 → MySQL 적재")
    print("=" * 55)

    if not CSV_PATH.exists():
        print(f"❌ 파일 없음: {CSV_PATH}")
        print("   clean.py 를 먼저 실행해주세요.")
        return

    conn = get_connection()
    try:
        insert_review(conn, CSV_PATH)
        print("\n🎉 parking_review 적재 완료!")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 오류: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()