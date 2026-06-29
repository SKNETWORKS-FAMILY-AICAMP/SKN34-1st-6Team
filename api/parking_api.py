"""
공영주차장 수집 → data/raw/ 에 CSV 저장

[수집 구조]
  공영주차장 키 GetParkInfo → 기본정보 + 요금 
  → CSV 저장 

실행:
  python api/parking_api.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv
import time
import requests
from datetime import datetime
from pathlib import Path

from config import SEOUL_GENERAL_KEY, KAKAO_API_KEY

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
RAW_DIR   = Path("data/raw")
PAGE_SIZE = 1000
API_DELAY = 0.1

# 출력 컬럼
FIELDNAMES = [
    "pk_name", "pk_address", "pk_code", "pk_type_cd", "pk_type_nm",
    "oper_se", "oper_se_nm", "phone",
    "weekday_start", "weekday_end", "weekend_start", "weekend_end",
    "holi_start", "holi_end",
    "parking_space", "fee_type",
    "basic_fee", "basic_time", "extra_fee", "extra_time",
    "daily_max_fee", "monthly_fee",
    "latitude", "longitude",
    "coord_src",
    "collected_at",
]


# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────
def _i(v) -> int:
    try:
        return int(float(v)) if v not in (None, "", "0.0") else 0
    except (TypeError, ValueError):
        return 0

def _f(v):
    try:
        val = float(v)
        return val if val != 0.0 else None
    except (TypeError, ValueError):
        return None

def _s(v) -> str:
    return str(v).strip() if v not in (None, "") else ""


# ─────────────────────────────────────────────
# 카카오 지오코딩
# ─────────────────────────────────────────────
def kakao_geocode(address: str) -> tuple:
    if not address or not KAKAO_API_KEY:
        return None, None
    try:
        r = requests.get(
            "https://dapi.kakao.com/v2/local/search/address.json",
            headers={"Authorization": f"KakaoAK {KAKAO_API_KEY}"},
            params={"query": address, "analyze_type": "similar"},
            timeout=5,
        )
        if r.status_code == 401:
            print("  ⚠️  카카오 API 키 인증 실패")
            return None, None
        docs = r.json().get("documents", [])
        if docs:
            return float(docs[0]["y"]), float(docs[0]["x"])
    except Exception:
        pass
    return None, None


# ─────────────────────────────────────────────
# API 페이징 수집
# ─────────────────────────────────────────────
def paged_fetch(service: str, api_key: str) -> list[dict]:
    all_rows, start = [], 1
    while True:
        end = start + PAGE_SIZE - 1
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/{service}/{start}/{end}/"
        print(f"  📥 {start}~{end} ...", end=" ", flush=True)
        try:
            data = requests.get(url, timeout=15).json()
            if service not in data:
                print(f"❌ {data.get('RESULT', {}).get('MESSAGE', data)}")
                break
            rows = data[service]["row"]
            print(f"✅ {len(rows)}건")
            all_rows.extend(rows)
            if len(rows) < PAGE_SIZE:
                break
            start = end + 1
            time.sleep(API_DELAY)
        except Exception as e:
            print(f"❌ {e}")
            break
    return all_rows


# ─────────────────────────────────────────────
# 일반키 기본정보 정규화
# ─────────────────────────────────────────────
def normalize_general(row: dict) -> dict:
    addr  = row.get("ADDR", "")
    jibun = row.get("ADDR_JIBUN", "")
    lat   = _f(row.get("LAT"))
    lng   = _f(row.get("LOT"))
    coord_src = "서울API" if lat else ""

    if not lat:
        lat, lng = kakao_geocode(addr or jibun)
        coord_src = "카카오" if lat else ""
        time.sleep(API_DELAY)

    return {
        "pk_name":       _s(row.get("PKLT_NM")),
        "pk_address":    addr or jibun,
        "pk_code":       _s(row.get("PKLT_CD")),
        "pk_type_cd":    _s(row.get("PKLT_KND")),
        "pk_type_nm":    _s(row.get("PKLT_KND_NM")),
        "oper_se":       _s(row.get("OPER_SE")),
        "oper_se_nm":    _s(row.get("OPER_SE_NM")),
        "phone":         _s(row.get("TELNO")),
        "weekday_start": _s(row.get("WD_OPER_BGNG_TM")),
        "weekday_end":   _s(row.get("WD_OPER_END_TM")),
        "weekend_start": _s(row.get("WE_OPER_BGNG_TM")),
        "weekend_end":   _s(row.get("WE_OPER_END_TM")),
        "holi_start":    _s(row.get("LHLDY_BGNG")),
        "holi_end":      _s(row.get("LHLDY")),
        "parking_space": _i(row.get("TPKCT")),
        "fee_type":      _s(row.get("CHGD_FREE_NM")),
        "basic_fee":     _f(row.get("PRK_CRG")) or "",
        "basic_time":    _f(row.get("PRK_HM")) or "",
        "extra_fee":     _f(row.get("ADD_CRG")) or "",
        "extra_time":    _f(row.get("ADD_UNIT_TM_MNT")) or "",
        "daily_max_fee": _f(row.get("DLY_MAX_CRG")) or "",
        "monthly_fee":   _f(row.get("MNTL_CMUT_CRG")) or "",
        "latitude":      lat or "",
        "longitude":     lng or "",
        "coord_src":     coord_src,
        "collected_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ─────────────────────────────────────────────
# 주소 기반 중복 제거
# ─────────────────────────────────────────────
def dedup(records: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in records:
        key = r.get("pk_address", "").strip().lower()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(r)
    return out


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  🅿️  공영주차장 API 수집")
    print("=" * 55 + "\n")

    if not SEOUL_GENERAL_KEY or SEOUL_GENERAL_KEY == "여기에_서울_일반_인증키":
        print("❌ SEOUL_GENERAL_KEY 를 .env 에 입력해주세요.")
        sys.exit(1)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output = RAW_DIR / f"parking_raw_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    # ── 1단계: 기본정보 수집 ──
    print("【1】 일반키 → 기본정보 수집 (GetParkInfo)")
    general_rows = paged_fetch("GetParkInfo", SEOUL_GENERAL_KEY)
    print(f"  → {len(general_rows):,}건\n")

    print("  정규화 + 카카오 지오코딩 보완 중...")
    records = []
    for i, row in enumerate(general_rows, 1):
        records.append(normalize_general(row))
        if i % 300 == 0:
            print(f"  {i:,}/{len(general_rows):,}...", end="\r")
    print(f"  ✅ {len(records):,}건 정규화 완료")

    before = len(records)
    records = dedup(records)
    print(f"  주소 중복 제거: {before:,} → {len(records):,}건\n")

    # ── 2단계: CSV 저장 ──
    print("【2】 CSV 저장 중...")
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore", restval="")
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    print(f"💾 저장 완료 → {output}  ({len(records):,}건)")
    return str(output)


if __name__ == "__main__":
    main()