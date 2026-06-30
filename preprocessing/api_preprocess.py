"""
api_preprocess.py

[역할]
- 공공데이터 API 데이터를 전처리하여 분석용 CSV 생성

[기능]
1. parking_raw.csv 로드
2. 지하철역 CSV 자동 탐색
3. 최근접 지하철역 계산
4. 난이도 점수 계산
5. 평일/주말 혼잡도 생성
6. 전처리 CSV 저장

[입력]
- data/raw/parking_raw.csv
- data/raw/subway_stations.csv
- data/raw/subway_station.csv

[출력]
- data/processed/parking_scored_*.csv

[실행]
python preprocessing/api_preprocess.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import math
from datetime import datetime
from pathlib import Path

# 점수 계산 함수
from utils.scoring import (
    calc_score,
    WEEKDAY_PATTERN,
    WEEKEND_PATTERN,
    SUBWAY_RADIUS_M
)

# 공통 유틸 함수 import
from utils.helpers import (
    to_int,
    to_float,
    find_latest_raw,
    find_subway_csv
)

# ─────────────────────────────────────────────
# 파일 경로 설정
# ─────────────────────────────────────────────
RAW_DIR       = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


# ─────────────────────────────────────────────
# 지하철역 csv 로드
# ─────────────────────────────────────────────
def load_subway_stations():
    """
    지하철역 CSV를 읽어
    역명, 호선, 위도, 경도 정보를 리스트로 저장한다.

    지원 형식
    1. 공공데이터 형식
    2. 전처리 형식
    """

    subway_csv = find_subway_csv()

    if not subway_csv:
        print("❌ 지하철역 CSV가 존재하지 않습니다.")
        return []

    print(f"📄 지하철역 파일 : {subway_csv.name}")

    stations = []

    with open(subway_csv, encoding="utf-8-sig") as file:

        reader = csv.DictReader(file)

        fields = reader.fieldnames or []

        # 컬럼명으로 파일 형식 구분
        new_format = "station_name" in fields

        for row in reader:

            # -----------------------------
            # 전처리된 CSV 형식
            # -----------------------------
            if new_format:

                name = row.get("station_name", "").strip()
                line = row.get("line", "").strip()

                lat = to_float(row.get("latitude"))
                lng = to_float(row.get("longitude"))

            # -----------------------------
            # 공공데이터 원본 형식
            # -----------------------------
            else:

                name = row.get("역한글명칭", "").strip()
                line = row.get("호선명칭", "").strip()

                # X좌표 = 경도
                lng = to_float(row.get("환승역X좌표"))

                # Y좌표 = 위도
                lat = to_float(row.get("환승역Y좌표"))

            # 좌표가 존재하는 데이터만 저장
            if name and lat and lng:

                stations.append({
                    "name": name,
                    "line": line,
                    "lat": lat,
                    "lng": lng
                })

    # -----------------------------
    # 동일한 역명 제거
    # -----------------------------

    unique = []
    seen = set()

    for station in stations:

        if station["name"] not in seen:

            seen.add(station["name"])
            unique.append(station)

    print(f"✅ 지하철역 {len(unique)}개 로드")

    return unique


# ─────────────────────────────────────────────
# 거리 계산 (Haversine)
# ─────────────────────────────────────────────
def haversine(lat1, lng1, lat2, lng2):
    """
    두 위도/경도 좌표 사이의 거리를 계산한다.

    반환값
    - 거리(m)
    """

    R = 6_371_000  # 지구 반지름(m)
    p = math.pi / 180 # 각도 라디안 설정
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p)
        * math.cos(lat2 * p)
        * math.sin((lng2 - lng1) * p / 2) ** 2
    ) #Haversine 공식

    #두 좌표 사이 거리 반환
    return 2 * R * math.asin(math.sqrt(a))

# 가장 가까운 지하철역 탐색
def nearest_station(lat, lng, stations):
    """
    모든 지하철역과의 거리를 비교하여
    가장 가까운 역을 반환한다.
    """

    best_name = ""               # 가장 가까운 역명
    best_line = ""               # 가장 가까운 호선
    best_distance = float("inf") # 가장 짧은 거리

    # 모든 지하철역과 거리 비교
    for station in stations:

        distance = haversine(
            lat,
            lng,
            station["lat"],
            station["lng"]
        )

        # 현재 역이 더 가까우면 정보 갱신
        if distance < best_distance:
            best_distance = distance
            best_name = station["name"]
            best_line = station["line"]

    # 최근접 역 정보 반환
    return (
        best_name,
        best_line,
        round(best_distance)
    )




# Main
def main():

    #프로그램 시작 안내
    print("=" * 55)
    print("🅿️ 주차장 데이터 전처리 시작")
    print("=" * 55)

    # 저장 폴더 생성(없으면 자동생성)
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 가장 최신 주차장 원본 CSV 탐색
    input_csv = find_latest_raw()

    # 원본 파일이 없으면 프로그램 종료
    if not input_csv:

        print("❌ parking_raw.csv 파일이 없습니다.")
        sys.exit()

    print(f"\n📂 입력 파일 : {input_csv}")


    # 지하철역 데이터 로드
    print("\n【지하철역 데이터 로드】")

    stations = load_subway_stations()

    #지하철 데이터가 없으면 역세권 점수는 0점처리
    if not stations:

        print("⚠️ 역세권 점수는 0점으로 처리됩니다.")

   
    # 원본 CSV 읽기
    with open(input_csv, encoding="utf-8-sig") as file:

        reader = csv.DictReader(file)

        rows = list(reader)

        original_fields = reader.fieldnames or []

    print(f"\n📊 총 {len(rows):,}건 로드")

    # 새로 추가될 컬럼 정의
    # 난이도 및 역세권 정보
    score_fields = [

        "최근접역명",
        "최근접역호선",
        "최근접역거리(m)",
        f"역세권여부({SUBWAY_RADIUS_M}m이내)",

        "요금점수",
        "면수점수",
        "역세권점수",
        "난이도점수",
        "난이도등급"
    ]

    # 평일 시간대별 혼잡도 컬럼 생성
    weekday_fields = [
        f"평일혼잡_{hour:02d}시"
        for hour in range(24)
    ]

    # 주말 시간대별 혼잡도 컬럼 생성
    weekend_fields = [
        f"주말혼잡_{hour:02d}시"
        for hour in range(24)
    ]

    # 최종 csv 컬럼 구성
    out_fields = (
        original_fields
        + score_fields
        + weekday_fields
        + weekend_fields
    )
    # 지정할 파일명 생성
    output = (
        PROCESSED_DIR
        / f"parking_scored_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    )

    no_coord = 0

    # 전처리 결과 CSV 저장
    with open(output, "w", newline="", encoding="utf-8-sig") as file:

        # CSV 작성 객체 생성
        writer = csv.DictWriter(
            file,
            fieldnames=out_fields,
            extrasaction="ignore"
        )

        # 헤더 작성
        writer.writeheader()


        # 주차장 데이터 전처리
        for index, row in enumerate(rows, start=1):

            # 위도/경도 가져오기
            lat = to_float(row.get("latitude"))
            lng = to_float(row.get("longitude"))

            # 최근접 지하철역 계산
            if lat and lng and stations:

                # 가장 가까운 역 찾기
                station_name, station_line, station_distance = nearest_station(
                    lat,
                    lng,
                    stations
                )

                # 역세권 여부 판단
                in_radius = (
                    "Y"
                    if station_distance <= SUBWAY_RADIUS_M
                    else "N"
                )

            # 좌표가 없는 경우
            else:

                station_name = ""
                station_line = ""
                station_distance = None
                in_radius = ""

                no_coord += 1

           
            # 난이도 점수 계산
            scores = calc_score(
                fee=to_int(row.get("basic_fee")),
                parking_space=to_int(row.get("parking_space")),
                distance=station_distance
            )

           
            # 평일 혼잡도 생성
            weekday = {
                f"평일혼잡_{hour:02d}시": WEEKDAY_PATTERN[hour]
                for hour in range(24)
            }

        
            # 주말 혼잡도 생성
            
            weekend = {
                f"주말혼잡_{hour:02d}시": WEEKEND_PATTERN[hour]
                for hour in range(24)
            }

            # 계산 결과를 현재 행에 추가
            row.update({

                "최근접역명": station_name,
                "최근접역호선": station_line,
                "최근접역거리(m)": station_distance,
                f"역세권여부({SUBWAY_RADIUS_M}m이내)": in_radius,

                **scores,
                **weekday,
                **weekend
            })

            # CSV에 저장
            writer.writerow(row)

            # 진행률 출력
            if index % 500 == 0 or index == len(rows):

                percent = index / len(rows) * 100

                bar = (
                    "█" * int(percent / 5)
                    + "░" * (20 - int(percent / 5))
                )

                print(
                    f"\r[{bar}] {index:,}/{len(rows):,} ({percent:.0f}%)",
                    end="",
                    flush=True
                )

    
    # 전처리 완료
    print("\n\n✅ 전처리 완료")

    print(f"저장 파일 : {output}")
    print(f"전체 데이터 : {len(rows):,}건")
    print(f"좌표 없음 : {no_coord:,}건")

    print("\n【추가된 컬럼】")
    print("최근접역명")
    print("최근접역호선")
    print("최근접역거리(m)")
    print("역세권여부")
    print("요금점수")
    print("면수점수")
    print("역세권점수")
    print("난이도점수")
    print("난이도등급")
    print("평일혼잡_00시 ~ 평일혼잡_23시")
    print("주말혼잡_00시 ~ 주말혼잡_23시")

    return str(output)

# 프로그램 실행
if __name__ == "__main__":
    main()