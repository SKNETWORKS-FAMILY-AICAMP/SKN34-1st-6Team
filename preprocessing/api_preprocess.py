"""
api_preprocess.py

[역할]
- API로 수집된 주차장 데이터 전처리

[기능]
1. 컬럼 정리 및 rename
2. 결측치 처리
3. 데이터 타입 변환
4. 주소/구 분리

[입력]
- data/raw/parking_api_raw.csv

[출력]
- data/processed/parking_api_clean.csv
"""