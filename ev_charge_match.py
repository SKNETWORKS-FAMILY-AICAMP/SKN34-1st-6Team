"""
ev_charge_match.py
──────────────────────────────────────────────
서울시 주차장 원본(parking_raw.csv)에
이미 만들어져 있는 전기차 충전 정보(parking_raw_en_charge.csv)를
"행 순서(위치)"가 아니라 "주소 문자열 + 위도경도"로 매칭해서
EN_CHARGE_YN 컬럼을 다시 붙여주는 스크립트

※ 프로젝트 폴더 안의 기존 파일(ev_api.py, ev_preprocess.py,
   match_ev_parking.py, parking_raw.csv, parking_raw_en_charge.csv 등)은
   전혀 건드리지 않습니다. 이 파일 하나만 프로젝트 루트(config.py와 같은 위치)에
   추가로 두고 실행하면 됩니다.

왜 필요한가
- 지금 있는 preprocessing/ev_preprocess.py 는 두 CSV의 "행 순서가 같다"고
  가정하고 그냥 같은 줄끼리 값을 복사합니다.
- 하지만 parking_raw.csv는 크롤링할 때마다 새로 갱신되기 때문에(행 순서/건수가
  달라질 수 있음, 예: parking_raw_20260701_1736.csv, _1745.csv 처럼 계속 새 파일이
  생김) 행 위치만 믿고 복사하면 다른 주차장의 값이 잘못 들어갈 수 있습니다.
- 그래서 pk_name이 아니라 "주소 문자열"과 "위도/경도"로 실제 같은 주차장인지
  확인한 뒤에 EN_CHARGE_YN 값을 옮겨 붙입니다.

처리 흐름 (요청하신 로직 구조 그대로)
① 전기차 충전소 API 호출          → api/ev_api.py (이미 실행하신 부분)
② EN_CHARGE_YN 정보 저장          → data/raw/parking_raw_en_charge.csv (이미 존재)
③ parking_raw.csv 읽기            → PARKING_RAW_PATH
④ 주소 비교 + 위경도 비교         → normalize_address() / haversine_m()
⑤ EN_CHARGE_YN 생성               → find_charge_value()
⑥ parking_raw_en_charge.csv 저장  → OUTPUT_PATH (새 파일로 저장, 기존 파일 덮어쓰지 않음)

매칭 규칙
- 주소 : 공백/괄호/특수문자 제거 + "서울특별시" 등 공통 접두어 제거 후 "완전일치"
- 좌표 : Haversine 거리 50m 이내면 "일치"로 판단
- 결합 : 주소 일치 OR 좌표 일치 → 매칭 성공 (하나만 맞아도 인정, 재현율 우선)
"""

import os
import re
import math
import pandas as pd


# ─────────────────────────────────────────────
# 경로 설정
# 이 파일을 프로젝트 루트(config.py, README.md와 같은 위치)에 두고 실행한다고 가정합니다.
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ③ 비교 대상이 되는 최신 주차장 원본
PARKING_RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "parking_raw.csv")

# ② 이미 만들어져 있는, EN_CHARGE_YN을 갖고 있는 참조 데이터
CHARGE_REF_PATH = os.path.join(BASE_DIR, "data", "raw", "parking_raw_en_charge.csv")

# ⑥ 매칭 결과 저장 경로 (기존 parking_raw_en_charge.csv를 덮어쓰지 않도록 별도 파일명 사용)
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "raw", "parking_raw_en_charge_matched.csv")

# 좌표 일치로 볼 거리 허용 오차 (m)
COORD_TOLERANCE_M = 300


# ─────────────────────────────────────────────
# ④ 주소 정규화
# ─────────────────────────────────────────────
SPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[()\[\],.\-]")
PREFIX_RE = re.compile(r"^(서울특별시|서울시|서울)\s*")


def normalize_address(addr):
    """
    주소 문자열을 비교 가능한 형태로 정규화한다.

    처리 내용
    1. None / NaN 방어
    2. 앞의 '서울특별시' 등 공통 접두어 제거
    3. 괄호, 쉼표, 마침표, 하이픈 등 특수문자 제거
    4. 공백 전부 제거
    5. 소문자로 통일
    """
    if not isinstance(addr, str) or not addr.strip():
        return ""

    text = PREFIX_RE.sub("", addr.strip())
    text = PUNCT_RE.sub("", text)
    text = SPACE_RE.sub("", text)

    return text.lower()


# ─────────────────────────────────────────────
# ④ 위도/경도 비교 (Haversine)
# ─────────────────────────────────────────────
def haversine_m(lat1, lng1, lat2, lng2):
    """두 좌표 사이의 거리를 미터(m) 단위로 반환한다."""
    R = 6_371_000  # 지구 반지름(m)
    p = math.pi / 180

    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p)
        * math.sin((lng2 - lng1) * p / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


# ─────────────────────────────────────────────
# 매칭용 참조 데이터 준비
# ─────────────────────────────────────────────
def build_charge_lookup(df_charge):
    """
    EN_CHARGE_YN 값이 실제로 채워진 행만 골라
    1) (정규화 주소 → EN_CHARGE_YN 값) 딕셔너리
    2) (위도, 경도, EN_CHARGE_YN 값) 리스트
    를 만든다.
    """
    charged = df_charge[
        df_charge["EN_CHARGE_YN"].notna()
        & (df_charge["EN_CHARGE_YN"].astype(str).str.strip() != "")
    ].copy()

    charged["addr_norm"] = charged["pk_address"].apply(normalize_address)

    # 주소 → EN_CHARGE_YN 값
    addr_lookup = dict(
        zip(charged["addr_norm"], charged["EN_CHARGE_YN"])
    )
    addr_lookup.pop("", None)  # 빈 주소는 매칭에서 제외

    # 좌표 비교용 리스트 [(lat, lng, value), ...]
    coord_lookup = [
        (row.latitude, row.longitude, row.EN_CHARGE_YN)
        for row in charged.itertuples()
        if pd.notna(row.latitude) and pd.notna(row.longitude)
    ]

    return addr_lookup, coord_lookup


def find_charge_value_by_coord(lat, lng, coord_lookup):
    """
    좌표 기준으로 COORD_TOLERANCE_M 이내에서 가장 가까운
    참조 행의 EN_CHARGE_YN 값을 반환한다. 없으면 빈 문자열.
    """
    if pd.isna(lat) or pd.isna(lng):
        return ""

    best_value = ""
    best_dist = float("inf")

    for ref_lat, ref_lng, value in coord_lookup:
        dist = haversine_m(lat, lng, ref_lat, ref_lng)
        if dist <= COORD_TOLERANCE_M and dist < best_dist:
            best_dist = dist
            best_value = value

    return best_value


# ─────────────────────────────────────────────
# 메인 매칭 로직
# ─────────────────────────────────────────────
def match_ev_charge_status(parking_raw_path, charge_ref_path, output_path):
    """
    parking_raw.csv 각 행에 대해 주소/좌표 매칭으로
    EN_CHARGE_YN 값을 다시 부여하고 CSV로 저장한다.
    """
    print("=" * 55)
    print("🔌 주소/좌표 기반 EN_CHARGE_YN 매칭 시작")
    print("=" * 55)

    df_parking = pd.read_csv(parking_raw_path)
    df_charge = pd.read_csv(charge_ref_path)

    print(f"📂 대상 주차장 데이터   : {len(df_parking):,}건  ({parking_raw_path})")
    print(f"📂 충전 정보 참조 데이터 : {len(df_charge):,}건  ({charge_ref_path})")

    addr_lookup, coord_lookup = build_charge_lookup(df_charge)
    print(f"⚡ EN_CHARGE_YN 값이 있는 참조 행 : {len(addr_lookup):,}건 (주소 기준)")

    matched_addr = 0
    matched_coord = 0
    results = []

    for row in df_parking.itertuples():
        addr_norm = normalize_address(row.pk_address)

        # 1) 주소 완전 일치 우선 확인
        if addr_norm and addr_norm in addr_lookup:
            value = addr_lookup[addr_norm]
            matched_addr += 1

        # 2) 주소로 못 찾으면 좌표(50m 이내)로 확인
        else:
            value = find_charge_value_by_coord(
                row.latitude, row.longitude, coord_lookup
            )
            if value:
                matched_coord += 1
            else:
                value = ""

        results.append(value)

    df_parking["EN_CHARGE_YN"] = results

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_parking.to_csv(output_path, index=False, encoding="utf-8-sig")

    unmatched = len(df_parking) - matched_addr - matched_coord

    print("-" * 55)
    print(f"✅ 주소 일치로 매칭            : {matched_addr:,}건")
    print(f"✅ 좌표({COORD_TOLERANCE_M}m 이내) 일치로 매칭 : {matched_coord:,}건")
    print(f"⛔ 매칭 실패(EN_CHARGE_YN 빈값) : {unmatched:,}건")
    print(f"💾 저장 위치 : {output_path}")
    print("=" * 55)

    return df_parking


if __name__ == "__main__":
    match_ev_charge_status(
        PARKING_RAW_PATH,
        CHARGE_REF_PATH,
        OUTPUT_PATH
    )
