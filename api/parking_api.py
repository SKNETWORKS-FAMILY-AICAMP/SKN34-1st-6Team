"""
parking_api.py

[역할]
- 공공데이터 API를 호출하여 서울시 공영주차장 데이터를 수집

[기능]
1. 공공데이터 API 요청
2. JSON 데이터 수신
3. 데이터 파싱 및 DataFrame 변환
4. raw 데이터 저장 (CSV 또는 DB)

[출력]
- data/raw/parking_api_raw.csv
"""