"""
ev_preprocess.py
────────────────────────────
전기차 충전소 데이터 + 주차장 데이터 결합하여

EV_CHARGE_YN (Y/N) 생성하는 전처리 모듈

핵심 로직:
→ 주차장 이름과 EV 충전소 이름 "문자열 매칭"
"""



"""
ev_preprocess.py
──────────────────────────────────────────────
주차장 데이터에 전기차 충전 가능 여부 컬럼(EV_CHARGE_YN)을 추가하는 전처리 모듈

처리 과정
1. parking_raw_en_charge.csv의 EN_CHARGE_YN 컬럼을 읽는다.
2. EN_CHARGE_YN 값이 존재하면 'Y', 없으면 'N'으로 변환한다.
3. 변환한 결과를 parking_raw.csv의 마지막 컬럼(EV_CHARGE_YN)으로 추가한다.
4. 전처리된 데이터를 ev_charge_parking.csv로 저장한다.

입력 파일
- parking_raw.csv
- parking_raw_en_charge.csv

출력 파일
- parking_raw_updated.csv
"""


import pandas as pd
import os

def preprocess_ev_charging_status(parking_raw_path, charge_info_path, output_path):
    """
    주차장 기본 데이터와 전기차 충전소 매칭 데이터를 합쳐 
    EV_CHARGE_YN 컬럼을 생성하고 저장하는 함수
    """
    try:
        # 1. 파일 읽기
        # 사용자님께서 언급하신 대로 인코딩 문제를 방지하기 위해 utf-8-sig 또는 cp949를 고려합니다.
        df_raw = pd.read_csv(parking_raw_path)
        df_charge = pd.read_csv(charge_info_path)

        # 2. EN_CHARGE_YN 값 변환 로직 (데이터 존재 시 'Y', 없으면 'N')
        # parking_raw_en_charge.csv의 'EN_CHARGE_YN' 컬럼 사용 [1, 2]
        # 값이 비어있지 않고(notna), 공백이 아닌 경우 'Y'로 변환합니다.
        ev_status = df_charge['EN_CHARGE_YN'].apply(
            lambda x: 'Y' if pd.notna(x) and str(x).strip() != '' else 'N'
        )

        # 3. 변환된 결과를 parking_raw.csv의 마지막 컬럼으로 추가
        # 컬럼명은 팀에서 정의한 'EV_CHARGE_YN'으로 설정합니다 [3]
        df_raw['EV_CHARGE_YN'] = ev_status

        # 4. 전처리된 데이터를 파일로 저장
        # 한글 깨짐 방지를 위해 encoding='utf-8-sig'를 권장합니다.
        df_raw.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"전처리 완료: {output_path} 저장됨")

    except Exception as e:
        print(f"전처리 중 오류 발생: {e}")

if __name__ == "__main__":
    # 파일 경로 설정 (팀의 폴더 구조 기준) [4, 5]
    RAW_PATH = 'data/parking_raw.csv'
    CHARGE_RAW_PATH = 'data/parking_raw_en_charge.csv'
    OUTPUT_PATH = 'data/parking_raw_updated.csv'

    # 전처리 함수 실행
    preprocess_ev_charging_status(RAW_PATH, CHARGE_RAW_PATH, OUTPUT_PATH)