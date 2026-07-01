"""
database/insert_review.py

[역할]
- 크롤링된 리뷰 요약 CSV → parking_review_summary 테이블 적재

[입력 CSV 컬럼]
pk_code (또는 pk_name), rating, review_count, url

[실행 순서]
1. python database/create_review_table.py   (테이블 생성)
2. python database/insert_review.py          (데이터 적재)  ← 이 파일

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

RAW_DIR       = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
BATCH = 500


# ---------------------------------------------------------
# DB 연결
# ---------------------------------------------------------
def get_connection():
    return pymysql.connect(
        host     = os.getenv("DB_HOST", "localhost"),
        port     = int(os.getenv("DB_PORT", 3306)),
        user     = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD"),
        db       = os.getenv("DB_NAME"),
        charset  = "utf8mb4",
        autocommit = False,
    )


# ---------------------------------------------------------
# 유틸
# ---------------------------------------------------------
def _s(v) -> str | None:
    if v is None or str(v).strip() in ("", "nan", "None"):
        return None
    return str(v).strip()

def _f(v) -> float | None:
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return None

def _i(v) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None

def _dt(v) -> datetime | None:
    if not v or str(v).strip() in ("", "nan"):
        return None
    try:
        return datetime.strptime(str(v).strip()[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def find_latest(pattern: str) -> Path | None:
    """RAW_DIR 또는 PROCESSED_DIR에서 최신 파일 탐색"""
    for d in [PROCESSED_DIR, RAW_DIR]:
        files = sorted(d.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
        if files:
            return files[0]
    return None

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
# pk_name → pk_code 매핑 (이름으로 크롤링한 경우)
# ---------------------------------------------------------
def get_name_to_code_map(conn) -> dict[str, str]:
    """parking 테이블에서 pk_name → pk_code 매핑 딕셔너리 반환"""
    with conn.cursor() as cur:
        cur.execute("SELECT pk_code, pk_name FROM parking")
        return {row[1]: row[0] for row in cur.fetchall()}


# ---------------------------------------------------------
# 리뷰 요약 적재
# ---------------------------------------------------------
def insert_review_summary(conn, csv_path: Path, name_to_code: dict):
    print(f"\n【리뷰 요약 적재】")
    print(f"  📂 입력: {csv_path}")

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    print(f"  📊 {len(rows):,}건 로드")

    records = []
    skipped = 0

    for row in rows:
        # pk_code 가 직접 있으면 그대로, 없으면 pk_name으로 매핑
        pk_code = _s(row.get("pk_code"))
        if not pk_code:
            pk_name = _s(row.get("pk_name") or row.get("name") or row.get("주차장명"))
            pk_code = name_to_code.get(pk_name) if pk_name else None

        if not pk_code:
            skipped += 1
            continue

        records.append({
            "pk_code":      pk_code,
            "rating":       _f(row.get("rating") or row.get("별점")),
            "review_count": _i(row.get("review_count") or row.get("리뷰건수")),
            "url":          _s(row.get("url") or row.get("URL")),
            "crawled_at":   _dt(row.get("crawled_at")) or datetime.now(),
        })

    if skipped:
        print(f"  ⚠️  pk_code 매핑 실패: {skipped}건 건너뜀")

    if not records:
        print("  ❌ 적재할 데이터 없음")
        return

    sql = """
        INSERT INTO parking_review_summary
            (pk_code, rating, review_count, url, crawled_at)
        VALUES
            (%(pk_code)s, %(rating)s, %(review_count)s, %(url)s, %(crawled_at)s)
        ON DUPLICATE KEY UPDATE
            rating       = VALUES(rating),
            review_count = VALUES(review_count),
            url          = VALUES(url),
            crawled_at   = VALUES(crawled_at)
    """
    batch_execute(conn, sql, records, "parking_review_summary")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main():
    print("=" * 55)
    print("  ⭐ 리뷰 요약 데이터 → MySQL 적재")
    print("=" * 55)

    # ── CSV 파일 탐색 ──
    # 파일명 패턴: review_*.csv 또는 parking_review*.csv
    csv_path = find_latest("review_*.csv") or find_latest("parking_review*.csv")

    if not csv_path:
        print("❌ 리뷰 CSV 파일 없음.")
        print("   data/raw/ 또는 data/processed/ 에 review_*.csv 파일을 넣어주세요.")
        return

    conn = get_connection()
    try:
        name_to_code = get_name_to_code_map(conn)
        print(f"  📋 주차장 매핑 로드: {len(name_to_code):,}개")

        insert_review_summary(conn, csv_path, name_to_code)
        print("\n🎉 리뷰 데이터 적재 완료!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 오류: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()