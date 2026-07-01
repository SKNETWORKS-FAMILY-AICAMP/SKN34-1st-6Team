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
4. 전처리된 데이터를 parking_raw_updated.csv로 저장한다.

입력 파일
- parking_raw.csv
- parking_raw_en_charge.csv

출력 파일
- parking_raw_updated.csv
"""