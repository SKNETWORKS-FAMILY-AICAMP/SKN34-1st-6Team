"""
ev_preprocess.py
──────────────────────────────────────────────
주차장 데이터에 전기차 충전 가능 여부 컬럼(EV_CHARGE_YN)을 추가하는 전처리 모듈

처리 과정
1. parking_raw_en_charge.csv의 EN_CHARGE_YN 컬럼을 읽는다.
2. EN_CHARGE_YN 값이 존재하면 'Y', 없으면 'N'으로 변환한다.
3. 변환한 결과를 parking_raw.csv의 마지막 컬럼(EV_CHARGE_YN)으로 추가한다.
4. 전처리된 데이터를 parking_raw_updated.csv로 저장한다.

입력 파일
- data/raw/parking_raw.csv
- data/raw/parking_raw_en_charge.csv

출력 파일
- data/processed/parking_raw_updated.csv
"""

import os
import pandas as pd


# 프로젝트 루트 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# 입력 파일(raw)
RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "parking_raw.csv")
CHARGE_RAW_PATH = os.path.join(BASE_DIR, "data", "raw", "parking_raw_en_charge.csv")


# 출력 파일(processed)
OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "parking_raw_updated.csv"
)


def preprocess_ev_charging_status(parking_raw_path, charge_info_path, output_path):
    """
    주차장 기본 데이터와 전기차 충전 정보를 이용하여
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
        print("전처리 완료!")
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