"""
ev_api.py
────────────────────────────
전기차 충전소 공공데이터 API를 호출하여
충전소 정보를 수집하는 모듈

역할:
1. EV 충전소 API 요청
2. JSON → DataFrame 변환
3. 필요한 컬럼만 정리
4. raw 데이터 저장 (선택)
"""

import csv
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from config import EN_CHARGE_YN_KEY

# API 주소
URL = "https://apis.data.go.kr/B552584/EvCharger/getChargerInfo"


def get_charger_info(page=1, rows=100):
    """
    전기차 충전소 정보 조회

    Args:
        page (int): 페이지 번호
        rows (int): 조회 건수

    Returns:
        dict: API 응답(JSON)
    """

    params = {
        "serviceKey": EN_CHARGE_YN_KEY,
        "pageNo": page,
        "numOfRows": rows,
        "dataType": "JSON",
    }

    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        response = session.get(f"{URL}?{urlencode(params)}", timeout=30)
    except requests.exceptions.Timeout:
        print("API 요청 시간 초과: 공공 API 서버 응답이 늦습니다.")
        return None
    except requests.exceptions.RequestException as exc:
        print(f"API 요청 예외: {exc}")
        return None

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError as exc:
            print(f"API 응답 JSON 파싱 실패: {exc}")
            print(response.text[:500])
            return None

    print(f"API 요청 실패 : {response.status_code}")
    print(response.text[:500])
    return None


def save_to_csv(data, output_path=None):
    """API 응답 데이터를 CSV로 저장합니다."""
    if not data:
        print("저장할 데이터가 없습니다.")
        return None

    items = None
    if isinstance(data, dict):
        items = data.get("items", {}).get("item", [])
        if not items:
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    if not items:
        print("수집된 충전소 데이터가 없습니다.")
        return None

    if isinstance(items, dict):
        items = [items]

    output_path = Path(output_path or ROOT / "data" / "raw" / "ev_charger.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "statNm", "statId", "chgerId", "addr", "lat", "lng", "busiNm", "stat",
        "useTime", "parkingFree", "output", "method", "kind", "kindDetail"
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            row = {field: item.get(field, "") for field in fieldnames}
            writer.writerow(row)

    print(f"CSV 저장 완료: {output_path}")
    return output_path


if __name__ == "__main__":
    data = get_charger_info()

    if data:
        save_to_csv(data)
