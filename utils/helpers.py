"""
helpers.py

[역할]
- 프로젝트 전역에서 사용하는 공통 유틸 함수

[기능]
1. 데이터 형변환 함수
2. CSV 파일 탐색
3. 문자열 처리 함수
4. 날짜 관련 함수
"""

from pathlib import Path


# 숫자 변환
def to_int(value):
    """
    문자열 → int 변환
    빈 값이면 0 반환
    """
    try:
        return int(float(value)) if value not in (None, "", "0.0") else 0
    except (TypeError, ValueError):
        return 0


def to_float(value):
    """
    문자열 → float 변환
    빈 값이면 None 반환
    """
    try:
        value = float(value)
        return value if value != 0.0 else None
    except (TypeError, ValueError):
        return None

# CSV 파일 찾기
RAW_DIR = Path("data/raw")


def find_latest_raw():
    """
    data/raw 안의 parking_raw.csv 탐색
    """
    files = sorted(
        RAW_DIR.glob("parking_raw.csv"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    return files[0] if files else None

# 지하철역 CSV 탐색
def find_subway_csv():
    """
    data/raw 폴더에서
    지하철역 CSV를 자동으로 탐색한다.

    탐색 순서
    1. subway_stations.csv
    2. subway_station.csv
    """

    # 기본 파일 확인
    fixed = RAW_DIR / "subway_stations.csv"

    if fixed.exists():
        return fixed

    # 없으면 subway_station.csv 검색
    candidates = sorted(
        RAW_DIR.glob("subway_station.csv"),
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    if candidates:
        return candidates[0]

    return None


# 주소 처리
def extract_district(address):
    """
    주소에서 '구' 추출

    예)
    강서구 가양동 ...
        ↓
    강서구
    """

    if not address:
        return ""

    parts = address.split()

    if len(parts) >= 2:
        return parts[0]

    return ""


def extract_dong(address):
    """
    주소에서 '동' 추출

    예)
    강서구 가양동 ...
        ↓
    가양동
    """

    if not address:
        return ""

    parts = address.split()

    if len(parts) >= 3:
        return parts[1]

    return ""