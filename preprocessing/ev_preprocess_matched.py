"""
ev_preprocess_matched.py
──────────────────────────────────────────────
preprocessing/ev_preprocess.py 의 입력 파일만
"행 순서 기반" 파일 대신 "주소/좌표 매칭 기반" 파일로 바꾼 버전

기존 ev_preprocess.py는 건드리지 않았고, 이 파일 하나만 별도로 추가한 것입니다.

무엇이 다른가 (ev_preprocess.py 대비)
- CHARGE_RAW_PATH : data/raw/parking_raw_en_charge.csv (기존, 행 순서 가정)
                    → data/raw/parking_raw_en_charge_matched.csv (신규, ev_charge_match.py의 결과)
- OUTPUT_PATH      : data/processed/parking_raw_updated.csv (기존)
                    → data/processed/parking_raw_updated_matched.csv (신규, 기존 결과 파일을 덮어쓰지 않도록 파일명 분리)
- 나머지 로직(EV_CHARGE_YN 생성 규칙, 저장 방식 등)은 ev_preprocess.py와 완전히 동일합니다.

처리 과정
1. parking_raw_en_charge_matched.csv 의 EN_CHARGE_YN 컬럼을 읽는다.
   (이 파일은 ev_charge_match.py가 주소/좌표 매칭으로 만든 결과)
2. EN_CHARGE_YN 값이 존재하면 'Y', 없으면 'N'으로 변환한다.
3. 변환한 결과를 parking_raw.csv의 마지막 컬럼(EV_CHARGE_YN)으로 추가한다.
4. 전처리된 데이터를 parking_raw_updated_matched.csv로 저장한다.

실행 순서
1) ev_charge_match.py 실행 → data/raw/parking_raw_en_charge_matched.csv 생성
2) 이 파일(ev_preprocess_matched.py) 실행 → data/processed/parking_raw_updated_matched.csv 생성

입력 파일
- data/raw/parking_raw.csv
- data/raw/parking_raw_en_charge_matched.csv

출력 파일
- data/processed/parking_raw_updated_matched.csv
"""

import os
import pandas as pd


# 프로젝트 루트 경로
# ev_preprocess.py와 같은 위치(preprocessing/ 폴더)에 둔다는 가정으로
# 상위 폴더(parents)를 프로젝트 루트로 계산합니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# 입력 파일(raw)
RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "parking_raw.csv")
CHARGE_RAW_PATH = os.path.join(
    BASE_DIR, "data", "raw", "parking_raw_en_charge_matched.csv"
)


# 출력 파일(processed)
OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "parking_raw_updated_matched.csv"
)


def preprocess_ev_charging_status(parking_raw_path, charge_info_path, output_path):
    """
    주차장 기본 데이터와 (주소/좌표 매칭된) 전기차 충전 정보를 이용하여
    EV_CHARGE_YN 컬럼을 생성하는 함수
    """

    try:

        # 1. CSV 파일 읽기
        df_raw = pd.read_csv(parking_raw_path)
        df_charge = pd.read_csv(charge_info_path)

        # 2. EV_CHARGE_YN 생성
        # EN_CHARGE_YN 값이 있으면 Y
        # 없으면 N
        df_raw["EV_CHARGE_YN"] = df_charge["EN_CHARGE_YN"].apply(
            lambda x: "Y" if pd.notna(x) and str(x).strip() != "" else "N"
        )

        # 3. processed 폴더 생성
        # (없으면 자동 생성)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 4. CSV 저장
        df_raw.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig"
        )

        print("=" * 50)
        print("전처리 완료! (주소/좌표 매칭 버전)")
        print(f"저장 위치 : {output_path}")
        print("=" * 50)

    except Exception as e:
        print("=" * 50)
        print("전처리 중 오류 발생")
        print(e)
        print("=" * 50)


if __name__ == "__main__":

    preprocess_ev_charging_status(
        RAW_PATH,
        CHARGE_RAW_PATH,
        OUTPUT_PATH
    )
