"""
database/insert_api.py
───────────────────────
data/processed/parking_scored_*.csv → DB 3개 테이블 적재

순서:
  1. subway_station  지하철역 좌표
  2. parking         기본정보 + 실시간 현황
  3. parking_score   난이도 점수 + 혼잡도

실행:
  python database/insert_api.py
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
from datetime import datetime
from pathlib import Path
from utils.db import get_connection

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

    # scored CSV 의 최근접역명/호선에서 고유 역 목록 추출
    seen, stations = set(), []

    # subway_stations.csv 가 있으면 좌표 포함해서 적재
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

    # 좌표 없는 역도 일단 적재 (subway_stations.csv 없는 경우)
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
def insert_parking(conn, rows: list[dict]):
    print("\n【2】 parking 테이블 적재")

    records = []
    for row in rows:
        pk_code = _s(row.get("pk_code"))
        if not pk_code or pk_code == "nan":
            # pk_code가 숫자형으로 저장된 경우 (1013181.0 → "1013181")
            raw = row.get("pk_code", "")
            try:
                pk_code = str(int(float(raw)))
            except (TypeError, ValueError):
                continue
        if not pk_code:
            continue

        records.append({
            "pk_code":          pk_code,
            "pk_name":          _s(row.get("pk_name")),
            "pk_address":       _s(row.get("pk_address")),
            "phone":            _s(row.get("phone")),
            "pk_type_cd":       _s(row.get("pk_type_cd")),
            "pk_type_nm":       _s(row.get("pk_type_nm")),
            "oper_se":          _s(row.get("oper_se")),
            "oper_se_nm":       _s(row.get("oper_se_nm")),
            "fee_type":         _s(row.get("fee_type")),
            "parking_space":    _i(row.get("parking_space")),
            "basic_fee":        _f(row.get("basic_fee")),
            "basic_time":       _f(row.get("basic_time")),
            "extra_fee":        _f(row.get("extra_fee")),
            "extra_time":       _f(row.get("extra_time")),
            "daily_max_fee":    _f(row.get("daily_max_fee")),
            "monthly_fee":      _f(row.get("monthly_fee")),
            "weekday_start":    _s(row.get("weekday_start")),
            "weekday_end":      _s(row.get("weekday_end")),
            "weekend_start":    _s(row.get("weekend_start")),
            "weekend_end":      _s(row.get("weekend_end")),
            "holi_start":       _s(row.get("holi_start")),
            "holi_end":         _s(row.get("holi_end")),
            "latitude":         _f(row.get("latitude")),
            "longitude":        _f(row.get("longitude")),
            "coord_src":        _s(row.get("coord_src")),
            # 실시간 현황
            "prk_stts_yn":      _i(row.get("PRK_STTS_YN")),
            "prk_stts_nm":      _s(row.get("PRK_STTS_NM")),
            "now_prk_vhcl_cnt": _i(row.get("NOW_PRK_VHCL_CNT")),
            "now_prk_updt_tm":  _dt(row.get("NOW_PRK_VHCL_UPDT_TM")),
            "pay_yn":           _s(row.get("PAY_YN")),
            "nght_pay_yn":      _s(row.get("NGHT_PAY_YN")),
            "prd_amt":          _f(row.get("PRD_AMT")),
            "day_max_crg":      _f(row.get("DAY_MAX_CRG")),
            "sat_chgd_free_se": _s(row.get("SAT_CHGD_FREE_SE")),
            "lhldy_chgd_free":  _s(row.get("LHLDY_CHGD_FREE_SE")),
            "shrn_pklt_yn":     _s(row.get("SHRN_PKLT_YN")),
            "shrn_pklt_url":    _s(row.get("SHRN_PKLT_MNG_URL")),
            "collected_at":     _dt(row.get("collected_at")),
        })

    sql = """
        INSERT INTO parking (
            pk_code, pk_name, pk_address, phone, pk_type_cd, pk_type_nm,
            oper_se, oper_se_nm, fee_type, parking_space,
            basic_fee, basic_time, extra_fee, extra_time, daily_max_fee, monthly_fee,
            weekday_start, weekday_end, weekend_start, weekend_end, holi_start, holi_end,
            latitude, longitude, coord_src,
            prk_stts_yn, prk_stts_nm, now_prk_vhcl_cnt, now_prk_updt_tm,
            pay_yn, nght_pay_yn, prd_amt, day_max_crg,
            sat_chgd_free_se, lhldy_chgd_free, shrn_pklt_yn, shrn_pklt_url,
            collected_at
        ) VALUES (
            %(pk_code)s, %(pk_name)s, %(pk_address)s, %(phone)s,
            %(pk_type_cd)s, %(pk_type_nm)s, %(oper_se)s, %(oper_se_nm)s,
            %(fee_type)s, %(parking_space)s,
            %(basic_fee)s, %(basic_time)s, %(extra_fee)s, %(extra_time)s,
            %(daily_max_fee)s, %(monthly_fee)s,
            %(weekday_start)s, %(weekday_end)s, %(weekend_start)s, %(weekend_end)s,
            %(holi_start)s, %(holi_end)s,
            %(latitude)s, %(longitude)s, %(coord_src)s,
            %(prk_stts_yn)s, %(prk_stts_nm)s, %(now_prk_vhcl_cnt)s, %(now_prk_updt_tm)s,
            %(pay_yn)s, %(nght_pay_yn)s, %(prd_amt)s, %(day_max_crg)s,
            %(sat_chgd_free_se)s, %(lhldy_chgd_free)s, %(shrn_pklt_yn)s, %(shrn_pklt_url)s,
            %(collected_at)s
        )
        ON DUPLICATE KEY UPDATE
            pk_name=VALUES(pk_name), pk_address=VALUES(pk_address),
            phone=VALUES(phone), parking_space=VALUES(parking_space),
            basic_fee=VALUES(basic_fee), extra_fee=VALUES(extra_fee),
            daily_max_fee=VALUES(daily_max_fee), monthly_fee=VALUES(monthly_fee),
            latitude=VALUES(latitude), longitude=VALUES(longitude),
            prk_stts_yn=VALUES(prk_stts_yn), now_prk_vhcl_cnt=VALUES(now_prk_vhcl_cnt),
            now_prk_updt_tm=VALUES(now_prk_updt_tm), collected_at=VALUES(collected_at)
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

        # 혼잡도 구간별 집계 (구간 내 최고값)
        # 우선순위: 혼잡 > 보통 > 여유
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

    # 동적 컬럼 목록
    cols = list(records[0].keys())
    col_str  = ", ".join(f"`{c}`" for c in cols)
    val_str  = ", ".join(f"%({c})s" for c in cols)
    upd_str  = ", ".join(
        f"`{c}`=VALUES(`{c}`)" for c in cols if c != "pk_code"
    )
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

    # scored CSV 우선, 없으면 raw CSV
    csv_path = find_latest("data/processed/parking_scored_*.csv")
    if not csv_path:
        csv_path = find_latest("data/raw/parking_raw_*.csv")
    if not csv_path or not Path(str(csv_path)).exists():
        print("❌ CSV 파일 없음. 먼저 api/parking_api.py → preprocessing/api_preprocess.py 실행")
        sys.exit(1)
    print(f"\n📂 입력: {csv_path}")

    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print(f"📊 {len(rows):,}건 로드")

    conn = get_connection()
    try:
        station_map = insert_subway(conn, rows)
        insert_parking(conn, rows)
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