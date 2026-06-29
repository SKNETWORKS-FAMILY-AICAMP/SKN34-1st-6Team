"""
preprocessing/api_preprocess.py
────────────────────────────────
data/raw/parking_raw_*.csv 를 읽어서
난이도 점수 + 혼잡도 시뮬레이션 추가 → data/processed/ 저장

지하철역 데이터 (아래 중 하나를 data/raw/ 에 넣으면 자동 감지):
  - subway_stations.csv   컬럼: 역한글명칭, 호선명칭, 환승역X좌표(경도), 환승역Y좌표(위도)
  - subway_station_*.csv  컬럼: id, station_name, line, latitude, longitude

실행:
  python preprocessing/api_preprocess.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import math
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# 파일 경로 설정
# ─────────────────────────────────────────────
RAW_DIR       = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

# ─────────────────────────────────────────────
# 설정값
# ─────────────────────────────────────────────
SUBWAY_RADIUS_M = 500   # 역세권 반경(m)

# ─────────────────────────────────────────────
# 혼잡도 시간대 패턴
# ─────────────────────────────────────────────
WEEKDAY_PATTERN = {
     0:"여유",  1:"여유",  2:"여유",  3:"여유",  4:"여유",  5:"여유",
     6:"여유",  7:"보통",  8:"혼잡",  9:"혼잡", 10:"보통", 11:"보통",
    12:"보통", 13:"보통", 14:"보통", 15:"보통", 16:"보통", 17:"혼잡",
    18:"혼잡", 19:"혼잡", 20:"보통", 21:"보통", 22:"여유", 23:"여유",
}
WEEKEND_PATTERN = {
     0:"여유",  1:"여유",  2:"여유",  3:"여유",  4:"여유",  5:"여유",
     6:"여유",  7:"여유",  8:"여유",  9:"여유", 10:"보통", 11:"보통",
    12:"혼잡", 13:"혼잡", 14:"혼잡", 15:"혼잡", 16:"보통", 17:"보통",
    18:"보통", 19:"여유", 20:"여유", 21:"여유", 22:"여유", 23:"여유",
}


# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────
def _i(v) -> int:
    try:
        return int(float(v)) if v not in (None, "", "0.0") else 0
    except (TypeError, ValueError):
        return 0

def _f(v):
    try:
        val = float(v)
        return val if val != 0.0 else None
    except (TypeError, ValueError):
        return None

def find_latest_raw() -> Path | None:
    files = sorted(RAW_DIR.glob("parking_raw_*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


# ─────────────────────────────────────────────
# 지하철역 CSV 자동 탐색
# ─────────────────────────────────────────────
def find_subway_csv() -> Path | None:
    """
    data/raw/ 안에서 subway CSV를 자동으로 찾는다.
    우선순위: subway_stations.csv → subway_station_*.csv (최신순)
    """
    # 1순위: 기본 파일명
    fixed = RAW_DIR / "subway_stations.csv"
    if fixed.exists():
        return fixed

    # 2순위: subway_station_*.csv 패턴
    candidates = sorted(
        RAW_DIR.glob("subway_station*.csv"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    if candidates:
        return candidates[0]

    return None


# ─────────────────────────────────────────────
# 지하철역 CSV 로드 (두 가지 형식 자동 감지)
# ─────────────────────────────────────────────
def load_subway_stations() -> list[dict]:
    """
    구 형식: 역한글명칭, 호선명칭, 환승역X좌표(경도), 환승역Y좌표(위도)
    신 형식: id, station_name, line, latitude, longitude
    """
    subway_csv = find_subway_csv()

    if not subway_csv:
        print(f"  ❌ 지하철역 CSV 없음 (data/raw/ 폴더 확인)")
        print(f"     subway_stations.csv 또는 subway_station_*.csv 를 data/raw/ 에 넣어주세요.")
        return []

    print(f"  📄 지하철역 파일: {subway_csv.name}")

    stations = []
    with open(subway_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []

        # 형식 자동 감지
        new_fmt = "station_name" in fields

        for row in reader:
            if new_fmt:
                name = row.get("station_name", "").strip()
                line = row.get("line", "").strip()
                lat  = _f(row.get("latitude"))
                lng  = _f(row.get("longitude"))
            else:
                name = row.get("역한글명칭", "").strip()
                line = row.get("호선명칭", "").strip()
                lng  = _f(row.get("환승역X좌표"))   # X = 경도
                lat  = _f(row.get("환승역Y좌표"))   # Y = 위도

            if name and lat and lng:
                stations.append({"name": name, "line": line, "lat": lat, "lng": lng})

    # 동일 역명 중복 제거 (첫 번째 좌표 사용)
    seen, unique = set(), []
    for s in stations:
        if s["name"] not in seen:
            seen.add(s["name"])
            unique.append(s)

    print(f"  ✅ 지하철역 {len(unique)}개 로드 (원본 {len(stations)}개)")
    return unique


# ─────────────────────────────────────────────
# 거리 계산 (Haversine)
# ─────────────────────────────────────────────
def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6_371_000
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2 +
         math.cos(lat1 * p) * math.cos(lat2 * p) *
         math.sin((lng2 - lng1) * p / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

def nearest_station(lat, lng, stations: list[dict]) -> tuple:
    best_name, best_line, best_dist = "", "", float("inf")
    for s in stations:
        d = haversine(lat, lng, s["lat"], s["lng"])
        if d < best_dist:
            best_dist = d
            best_name = s["name"]
            best_line = s["line"]
    return best_name, best_line, round(best_dist)


# ─────────────────────────────────────────────
# 난이도 점수 계산
# ─────────────────────────────────────────────
def calc_score(row: dict, dist_m) -> dict:
    # 요금 점수 (0~40): 비쌀수록 ↑
    fee = _i(row.get("basic_fee"))
    if fee <= 0:       fee_score = 0
    elif fee <= 500:   fee_score = round(fee / 500 * 10)
    elif fee <= 1000:  fee_score = round(10 + (fee - 500) / 500 * 15)
    elif fee <= 2000:  fee_score = round(25 + (fee - 1000) / 1000 * 10)
    else:              fee_score = 40

    # 면수 점수 (0~30): 적을수록 ↑
    cap = _i(row.get("parking_space"))
    if cap <= 0:       cap_score = 15
    elif cap <= 30:    cap_score = 30
    elif cap <= 100:   cap_score = round(30 - (cap - 30) / 70 * 15)
    elif cap <= 500:   cap_score = round(15 - (cap - 100) / 400 * 10)
    else:              cap_score = 5

    # 역세권 점수 (0~30): 가까울수록 ↑
    d = dist_m if isinstance(dist_m, (int, float)) else 9999
    if d <= SUBWAY_RADIUS_M:    subway_score = 30
    elif d <= 1000:             subway_score = round(30 * (1 - (d - SUBWAY_RADIUS_M) / 500))
    else:                       subway_score = 0

    total = fee_score + cap_score + subway_score
    grade = (
        "D" if total >= 80 else
        "C"     if total >= 55 else
        "B"       if total >= 30 else
        "A"
    )
    return {
        "요금점수":   fee_score,
        "면수점수":   cap_score,
        "역세권점수": subway_score,
        "난이도점수": total,
        "난이도등급": grade,
    }


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🅿️  전처리: 난이도 점수 + 혼잡도 시뮬레이션")
    print("=" * 55 + "\n")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 입력 파일 탐색
    input_csv = find_latest_raw()
    if not input_csv:
        print("❌ data/raw/parking_raw_*.csv 파일이 없습니다.")
        print("   먼저 api/parking_api.py 를 실행해주세요.")
        sys.exit(1)
    print(f"  📂 입력: {input_csv}")

    # 지하철역 로드
    print("\n【지하철역 좌표 로드】")
    stations = load_subway_stations()
    if not stations:
        print("  ⚠️  역세권 점수는 0으로 처리됩니다.\n")
    print()

    # 원본 CSV 읽기
    with open(input_csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        original_fields = reader.fieldnames or []
    print(f"  📊 {len(rows):,}건 로드\n")

    # 출력 필드
    score_fields = [
        "최근접역명", "최근접역호선", "최근접역거리(m)", f"역세권여부({SUBWAY_RADIUS_M}m이내)",
        "요금점수", "면수점수", "역세권점수", "난이도점수", "난이도등급",
    ]
    weekday_fields = [f"평일혼잡_{h:02d}시" for h in range(24)]
    weekend_fields = [f"주말혼잡_{h:02d}시" for h in range(24)]
    out_fields = original_fields + score_fields + weekday_fields + weekend_fields

    output = PROCESSED_DIR / f"parking_scored_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    no_coord = 0

    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
        writer.writeheader()

        for i, row in enumerate(rows, 1):
            lat = _f(row.get("latitude"))
            lng = _f(row.get("longitude"))

            if lat and lng and stations:
                s_name, s_line, s_dist = nearest_station(lat, lng, stations)
                in_radius = "Y" if s_dist <= SUBWAY_RADIUS_M else "N"
            else:
                s_name, s_line, s_dist, in_radius = "", "", "", ""
                no_coord += 1

            scores  = calc_score(row, s_dist)
            weekday = {f"평일혼잡_{h:02d}시": WEEKDAY_PATTERN[h] for h in range(24)}
            weekend = {f"주말혼잡_{h:02d}시": WEEKEND_PATTERN[h] for h in range(24)}

            row.update({
                "최근접역명":                          s_name,
                "최근접역호선":                        s_line,
                "최근접역거리(m)":                     s_dist,
                f"역세권여부({SUBWAY_RADIUS_M}m이내)": in_radius,
                **scores, **weekday, **weekend,
            })
            writer.writerow(row)

            if i % 500 == 0 or i == len(rows):
                pct = i / len(rows) * 100
                bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                print(f"\r  [{bar}] {i:,}/{len(rows):,} ({pct:.0f}%)", end="", flush=True)

    print(f"\n\n✅ 완료!")
    print(f"   저장     : {output}")
    print(f"   전체     : {len(rows):,}건")
    print(f"   좌표 없음: {no_coord:,}건")
    print(f"\n【 추가된 컬럼 】")
    print(f"   역세권 : 최근접역명, 최근접역호선, 최근접역거리(m), 역세권여부")
    print(f"   난이도 : 요금점수(0~40) + 면수점수(0~30) + 역세권점수(0~30) = 난이도점수(0~100)")
    print(f"   등급   : A(<30) / B(30~54) / C(55~79) / D(80+)")
    print(f"   혼잡도 : 평일 24시간 + 주말 24시간 (패턴 기반)")

    return str(output)


if __name__ == "__main__":
    main()