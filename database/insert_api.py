"""
CSV 전처리 결과 → MySQL 테이블 적재

사용 파일
  data/processed/parking_scored.csv
    → subway_station 테이블
      (지하철역 좌표)

    → parking 테이블
      (주차장 기본정보)

    → parking_score 테이블
      (난이도 점수 + 역세권 + 혼잡도)

  data/processed/parking_raw_updated_matched.csv (있으면 우선)
  data/processed/parking_raw_updated.csv (없으면 대신 사용)
    → parking 테이블의 ev_charge_yn 컬럼
      (pk_code 기준으로 매칭해서 채워 넣음)
      

적재 순서
  1. subway_station
  2. parking
  3. parking_score

실행
  python database/insert_api.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv()

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

PROCESSED_DIR = Path("data/processed")
RAW_DIR       = Path("data/raw")
SUBWAY_CSV    = RAW_DIR / "subway_stations.csv"
BATCH         = 500


# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────
def _s(v) -> str | None:
    if v is None or str(v).strip() in ("", "nan", "None"):
        return None
    return str(v).strip()

def _i(v) -> int | None:
    try:
        return int(float(v)) if v not in (None, "", "nan") else None
    except (TypeError, ValueError):
        return None

def _f(v) -> float | None:
    try:
        val = float(v)
        return val if val != 0.0 else None
    except (TypeError, ValueError):
        return None

def _dt(v) -> datetime | None:
    if not v or str(v).strip() in ("", "nan"):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(v).strip()[:19], fmt)
        except ValueError:
            continue
    return None

def find_latest(pattern: str) -> Path | None:
    files = sorted(Path(".").glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        files = sorted(PROCESSED_DIR.glob(pattern.split("/")[-1]),
                       key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None

def load_ev_charge_map() -> dict[str, str]:
    """
    pk_code → EV_CHARGE_YN(Y/N) 매핑을 만든다.

    우선순위
      1. data/processed/parking_raw_updated_matched.csv
         (ev_charge_match.py + ev_preprocess_matched.py 결과, 주소/좌표 매칭 기반)
      2. data/processed/parking_raw_updated.csv
         (기존 ev_preprocess.py 결과, 행 순서 기반)

    두 파일 다 없으면 빈 dict 반환 → parking 테이블은 전부 기본값 'N'으로 적재됨.
    """
    ev_path = PROCESSED_DIR / "parking_raw_updated_matched.csv"
    if not ev_path.exists():
        ev_path = PROCESSED_DIR / "parking_raw_updated.csv"
    if not ev_path.exists():
        print("  ⚠️  EV 충전 정보 파일 없음 → ev_charge_yn은 전부 'N'으로 적재됩니다.")
        return {}

    print(f"  🔌 EV 충전 정보 입력: {ev_path}")

    ev_map: dict[str, str] = {}
    with open(ev_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pk_code = _s(row.get("pk_code"))
            if not pk_code:
                continue
            value = _s(row.get("EV_CHARGE_YN"))
            ev_map[pk_code] = "Y" if value == "Y" else "N"

    return ev_map

def batch_insert(conn, sql: str, records: list, label: str):
    total = len(records)
    with conn.cursor() as cur:
        for i in range(0, total, BATCH):
            cur.executemany(sql, records[i : i + BATCH])
            conn.commit()
            done = min(i + BATCH, total)
            print(f"\r  [{label}] {done:,}/{total:,}", end="", flush=True)
    print(f"\r  ✅ {label}: {total:,}건 완료          ")


# ─────────────────────────────────────────────
# 1. subway_station
# ─────────────────────────────────────────────
def insert_subway(conn, rows: list[dict]) -> dict[str, int]:
    """지하철역 적재 → {역명: id} 반환"""
    print("\n【1】 subway_station 적재")

    seen, stations = set(), []

    coord_map: dict[str, tuple] = {}
    if SUBWAY_CSV.exists():
        with open(SUBWAY_CSV, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                name = r.get("역한글명칭", "").strip()
                lat  = _f(r.get("환승역Y좌표"))
                lng  = _f(r.get("환승역X좌표"))
                line = r.get("호선명칭", "").strip()
                if name and lat and lng:
                    coord_map[name] = (lat, lng, line)

    for row in rows:
        name = _s(row.get("최근접역명"))
        line = _s(row.get("최근접역호선"))
        if not name or name in seen:
            continue
        seen.add(name)
        lat, lng, _line = coord_map.get(name, (None, None, line))
        stations.append({
            "station_name": name,
            "line":         line or _line,
            "latitude":     lat,
            "longitude":    lng,
        })

    if not stations:
        print("  ⚠️  CSV에 최근접역명 없음 → 건너뜀")
        return {}

    no_coord = sum(1 for s in stations if not s["latitude"])
    if no_coord:
        print(f"  ⚠️  좌표 없는 역 {no_coord}개 → 역명/호선만 적재")

    sql = """
        INSERT IGNORE INTO subway_station (station_name, line, latitude, longitude)
        VALUES (%(station_name)s, %(line)s, %(latitude)s, %(longitude)s)
    """
    batch_insert(conn, sql, stations, "subway_station")

    with conn.cursor() as cur:
        cur.execute("SELECT id, station_name FROM subway_station")
        return {row[1]: row[0] for row in cur.fetchall()}


# ─────────────────────────────────────────────
# 2. parking
# ─────────────────────────────────────────────
def insert_parking(conn, rows: list[dict], ev_map: dict[str, str] | None = None):
    print("\n【2】 parking 테이블 적재")

    ev_map = ev_map or {}

    records = []
    for row in rows:
        pk_code = _s(row.get("pk_code"))
        if pk_code in (None, "", "nan", "NaN"):
            raw = row.get("pk_code", "")
            try:
                pk_code = str(int(float(raw)))
            except (TypeError, ValueError):
                continue
        if not pk_code:
            continue

        records.append({
            "pk_code":       pk_code,
            "pk_name":       _s(row.get("pk_name")),
            "pk_address":    _s(row.get("pk_address")),
            "phone":         _s(row.get("phone")),
            "pk_type_cd":    _s(row.get("pk_type_cd")),
            "pk_type_nm":    _s(row.get("pk_type_nm")),
            "oper_se":       _s(row.get("oper_se")),
            "oper_se_nm":    _s(row.get("oper_se_nm")),
            "fee_type":      _s(row.get("fee_type")),
            "parking_space": _i(row.get("parking_space")),
            "basic_fee":     _f(row.get("basic_fee")),
            "basic_time":    _f(row.get("basic_time")),
            "extra_fee":     _f(row.get("extra_fee")),
            "extra_time":    _f(row.get("extra_time")),
            "daily_max_fee": _f(row.get("daily_max_fee")),
            "monthly_fee":   _f(row.get("monthly_fee")),
            "weekday_start": _s(row.get("weekday_start")),
            "weekday_end":   _s(row.get("weekday_end")),
            "weekend_start": _s(row.get("weekend_start")),
            "weekend_end":   _s(row.get("weekend_end")),
            "holi_start":    _s(row.get("holi_start")),
            "holi_end":      _s(row.get("holi_end")),
            "latitude":      _f(row.get("latitude")),
            "longitude":     _f(row.get("longitude")),
            "coord_src":     _s(row.get("coord_src")),
            "collected_at":  _dt(row.get("collected_at")),
            "ev_charge_yn":  ev_map.get(pk_code, "N"),
        })

    matched = sum(1 for r in records if r["ev_charge_yn"] == "Y")
    print(f"  🔌 ev_charge_yn = 'Y'로 적재될 건수: {matched:,}/{len(records):,}")

    sql = """
        INSERT INTO parking (
            pk_code, pk_name, pk_address, phone, pk_type_cd, pk_type_nm,
            oper_se, oper_se_nm, fee_type, parking_space,
            basic_fee, basic_time, extra_fee, extra_time, daily_max_fee, monthly_fee,
            weekday_start, weekday_end, weekend_start, weekend_end, holi_start, holi_end,
            latitude, longitude, coord_src, collected_at, ev_charge_yn
        ) VALUES (
            %(pk_code)s, %(pk_name)s, %(pk_address)s, %(phone)s,
            %(pk_type_cd)s, %(pk_type_nm)s, %(oper_se)s, %(oper_se_nm)s,
            %(fee_type)s, %(parking_space)s,
            %(basic_fee)s, %(basic_time)s, %(extra_fee)s, %(extra_time)s,
            %(daily_max_fee)s, %(monthly_fee)s,
            %(weekday_start)s, %(weekday_end)s, %(weekend_start)s, %(weekend_end)s,
            %(holi_start)s, %(holi_end)s,
            %(latitude)s, %(longitude)s, %(coord_src)s, %(collected_at)s, %(ev_charge_yn)s
        )
        ON DUPLICATE KEY UPDATE
            pk_name=VALUES(pk_name), pk_address=VALUES(pk_address),
            phone=VALUES(phone), parking_space=VALUES(parking_space),
            basic_fee=VALUES(basic_fee), extra_fee=VALUES(extra_fee),
            daily_max_fee=VALUES(daily_max_fee), monthly_fee=VALUES(monthly_fee),
            latitude=VALUES(latitude), longitude=VALUES(longitude),
            collected_at=VALUES(collected_at), ev_charge_yn=VALUES(ev_charge_yn)
    """
    batch_insert(conn, sql, records, "parking")


# ─────────────────────────────────────────────
# 3. parking_score
# ─────────────────────────────────────────────
def insert_score(conn, rows: list[dict], station_map: dict[str, int]):
    print("\n【3】 parking_score 적재")

    records = []
    for row in rows:
        pk_code = _s(row.get("pk_code"))
        if not pk_code:
            try:
                pk_code = str(int(float(row.get("pk_code", ""))))
            except (TypeError, ValueError):
                continue
        if not pk_code:
            continue

        PRIORITY = {"혼잡": 2, "보통": 1, "여유": 0}

        def peak(hours, prefix):
            vals = [row.get(f"{prefix}_{h:02d}시", "") for h in hours]
            vals = [v for v in vals if v and str(v) not in ("", "nan")]
            if not vals:
                return None
            return max(vals, key=lambda v: PRIORITY.get(v, -1))

        SEGMENTS = {
            "dawn":      range(0,  6),
            "morning":   range(6,  10),
            "forenoon":  range(10, 13),
            "afternoon": range(13, 17),
            "evening":   range(17, 20),
            "night":     range(20, 24),
        }
        cong = {}
        for seg, hours in SEGMENTS.items():
            cong[f"wd_{seg}"] = peak(hours, "평일혼잡")
            cong[f"we_{seg}"] = peak(hours, "주말혼잡")

        s_name = _s(row.get("최근접역명"))
        records.append({
            "pk_code":              pk_code,
            "nearest_station_id":   station_map.get(s_name) if s_name else None,
            "nearest_station_name": s_name,
            "nearest_station_line": _s(row.get("최근접역호선")),
            "nearest_station_m":    _i(row.get("최근접역거리(m)")),
            "in_subway_radius":     _s(row.get("역세권여부(500m이내)")),
            "fee_score":            _i(row.get("요금점수")),
            "capacity_score":       _i(row.get("면수점수")),
            "subway_score":         _i(row.get("역세권점수")),
            "difficulty_score":     _i(row.get("난이도점수")),
            "difficulty_grade":     _s(row.get("난이도등급") or row.get("difficulty_grade")),
            **cong,
        })

    if not records:
        print("  ⚠️  적재할 score 데이터 없음 → 건너뜀")
        return

    cols = list(records[0].keys())
    col_str = ", ".join(f"`{c}`" for c in cols)
    val_str = ", ".join(f"%({c})s" for c in cols)
    upd_str = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in cols if c != "pk_code")
    sql = f"""
        INSERT INTO parking_score ({col_str})
        VALUES ({val_str})
        ON DUPLICATE KEY UPDATE {upd_str}
    """
    batch_insert(conn, sql, records, "parking_score")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🅿️  주차장 데이터 → MySQL 적재")
    print("=" * 55)

    csv_path = find_latest("data/processed/parking_scored.csv")
    if not csv_path:
        csv_path = find_latest("data/raw/parking_raw.csv")
    if not csv_path or not Path(str(csv_path)).exists():
        print("❌ CSV 파일 없음. 먼저 api/parking_api.py → preprocessing/api_preprocess.py 실행")
        sys.exit(1)
    print(f"\n📂 입력: {csv_path}")

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print(f"📊 {len(rows):,}건 로드")

    ev_map = load_ev_charge_map()

    conn = get_connection()
    try:
        station_map = insert_subway(conn, rows)
        insert_parking(conn, rows, ev_map)
        insert_score(conn, rows, station_map)
        print(f"\n🎉 전체 적재 완료!")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 오류: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()