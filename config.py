"""
config.py

[역할]
- 프로젝트 설정 관리

[내용]
1. DB 정보
2. API 정보
3. 파일 경로 설정
"""



import os
from dotenv import load_dotenv

load_dotenv()

# DB 설정
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_NAME     = os.getenv("DB_NAME",     "parking_project")

# API 키
SEOUL_GENERAL_KEY  = os.getenv("SEOUL_GENERAL_KEY",  "72516446437475743637496b67704b")
SEOUL_REALTIME_KEY = os.getenv("SEOUL_REALTIME_KEY", "46436d7a437475743930706e537766")
KAKAO_API_KEY      = os.getenv("KAKAO_API_KEY",      "c617fa7bb67cea8eac02dd400b99ea81")