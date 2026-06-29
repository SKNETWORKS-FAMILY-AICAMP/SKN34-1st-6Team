"""
api/parking_api.py
──────────────────
공영주차장 수집 → data/raw/ 에 CSV 저장

[수집 구조]
  일반키  GetParkingInfo → 기본정보 + 요금 (전체)
  실시간키 GetParkingInfo → 실시간 현황 (123개, NOW_PRK_VHCL_CNT 등)
  두 결과를 pk_code 기준으로 조인 → 하나의 CSV

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

from config import SEOUL_GENERAL_KEY, SEOUL_REALTIME_KEY, KAKAO_API_KEY

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
RAW_DIR   = Path("data/raw")
PAGE_SIZE = 1000
API_DELAY = 0.1

# 출력 컬럼
FIELDNAMES = [
    # 기본정보 (일반키 기반, 한글 매핑)
    "pk_name", "pk_address", "pk_code", "pk_type_cd", "pk_type_nm",
    "oper_se", "oper_se_nm", "phone",
    "weekday_start", "weekday_end", "weekend_start", "weekend_end",
    "holi_start", "holi_end",
    "parking_space", "fee_type",
    "basic_fee", "basic_time", "extra_fee", "extra_time",
    "daily_max_fee", "monthly_fee",
    "latitude", "longitude",
    "coord_src",
    # 실시간 현황 (실시간키 기반 원본 컬럼)
    "PRK_STTS_YN", "PRK_STTS_NM",
    "NOW_PRK_VHCL_CNT", "NOW_PRK_VHCL_UPDT_TM",
    "PAY_YN", "PAY_YN_NM",
    "NGHT_PAY_YN", "NGHT_PAY_YN_NM",
    "LHLDY_OPER_BGNG_TM", "LHLDY_OPER_END_TM",
    "LHLDY_CHGD_FREE_SE", "LHLDY_CHGD_FREE_SE_NAME",
    "PRD_AMT",
    "STRT_PKLT_MNG_NO",
    "BSC_PRK_CRG", "BSC_PRK_HR",
    "ADD_PRK_CRG", "ADD_PRK_HR",
    "BUS_BSC_PRK_CRG", "BUS_BSC_PRK_HR",
    "BUS_ADD_PRK_HR", "BUS_ADD_PRK_CRG",
    "DAY_MAX_CRG",
    "SHRN_PKLT_MNG_NM", "SHRN_PKLT_MNG_URL",
    "SHRN_PKLT_YN", "SHRN_PKLT_ETC",
    # 메타
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
    lng   = _f(row.get("LOT"))   # GetParkInfo 경도 컬럼명은 LOT
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
# 실시간키 현황 정규화
# ─────────────────────────────────────────────
REALTIME_FIELDS = [
    "PRK_STTS_YN", "PRK_STTS_NM",
    "NOW_PRK_VHCL_CNT", "NOW_PRK_VHCL_UPDT_TM",
    "PAY_YN", "PAY_YN_NM",
    "NGHT_PAY_YN", "NGHT_PAY_YN_NM",
    "LHLDY_OPER_BGNG_TM", "LHLDY_OPER_END_TM",
    "LHLDY_CHGD_FREE_SE", "LHLDY_CHGD_FREE_SE_NAME",
    "PRD_AMT", "STRT_PKLT_MNG_NO",
    "BSC_PRK_CRG", "BSC_PRK_HR",
    "ADD_PRK_CRG", "ADD_PRK_HR",
    "BUS_BSC_PRK_CRG", "BUS_BSC_PRK_HR",
    "BUS_ADD_PRK_HR", "BUS_ADD_PRK_CRG",
    "DAY_MAX_CRG",
    "SHRN_PKLT_MNG_NM", "SHRN_PKLT_MNG_URL",
    "SHRN_PKLT_YN", "SHRN_PKLT_ETC",
]

def normalize_realtime(row: dict) -> dict:
    """
    PRK_STTS_YN = 1 → 20분 이내 실시간 데이터 존재 → 값 채움
    PRK_STTS_YN = 0 → 미연계 → NOW_PRK_VHCL_CNT 등 실시간 컬럼 None
    PRK_STTS_YN = 2 → 20~120분 이내 (정보수집중) → None
    PRK_STTS_YN = 3 → 120분~2일 (통신점검중) → None
    """
    stts_yn = _s(row.get("PRK_STTS_YN"))
    has_realtime = stts_yn == "1"   # 20분 이내 연계 데이터만 신뢰

    result = {}
    for f in REALTIME_FIELDS:
        raw = _s(row.get(f))
        # 실시간 현황 컬럼은 연계 상태일 때만 값 부여, 아니면 None
        if f in ("NOW_PRK_VHCL_CNT", "NOW_PRK_VHCL_UPDT_TM"):
            result[f] = raw if has_realtime and raw else None
        else:
            result[f] = raw if raw else None
    return result

def empty_realtime() -> dict:
    return {f: None for f in REALTIME_FIELDS}


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

    # ── 1단계: 일반키로 기본정보 수집 ──
    print("【1】 일반키 → 기본정보 수집 (GetParkInfo 2,204건)")
    general_rows = paged_fetch("GetParkInfo", SEOUL_GENERAL_KEY)
    print(f"  → {len(general_rows):,}건\n")

    print("  정규화 + 카카오 지오코딩 보완 중...")
    records = []
    for i, row in enumerate(general_rows, 1):
        records.append(normalize_general(row))
        if i % 300 == 0:
            print(f"  {i:,}/{len(general_rows):,}...", end="\r")
    print(f"  ✅ {len(records):,}건 정규화 완료")

    # 중복 제거
    before = len(records)
    records = dedup(records)
    print(f"  주소 중복 제거: {before:,} → {len(records):,}건\n")

    # pk_code → 기본정보 맵
    base_map = {r["pk_code"]: r for r in records if r["pk_code"]}

    # ── 2단계: 실시간키로 현황 수집 후 조인 ──
    realtime_map: dict[str, dict] = {}
    realtime_ok = (
        SEOUL_REALTIME_KEY and
        SEOUL_REALTIME_KEY != "여기에_서울_실시간_인증키"
    )

    if realtime_ok:
        print("【2】 실시간키 → 현황 수집 (GetParkingInfo)")
        rt_rows = paged_fetch("GetParkingInfo", SEOUL_REALTIME_KEY)
        print(f"  → {len(rt_rows):,}건")
        for row in rt_rows:
            code = _s(row.get("PKLT_CD"))
            if code:
                realtime_map[code] = normalize_realtime(row)
        matched = sum(1 for r in records if r["pk_code"] in realtime_map)
        print(f"  실시간 매칭: {matched}건\n")
    else:
        print("【2】 실시간키 없음 → 실시간 컬럼 빈값으로 저장\n")

    # ── 3단계: CSV 저장 ──
    print("【3】 CSV 저장 중...")
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore",
                                restval="")
        writer.writeheader()
        for r in records:
            rt = realtime_map.get(r["pk_code"], empty_realtime())
            merged = {**r, **rt}
            # None → 빈 문자열로 변환 (CSV 저장용, DB insert 시 None 처리는 insert_api.py에서)
            row_out = {k: ("" if v is None else v) for k, v in merged.items()}
            writer.writerow(row_out)

    # 실시간 연계 통계 출력
    has_rt  = sum(1 for r in records if realtime_map.get(r["pk_code"], {}).get("NOW_PRK_VHCL_CNT") is not None)
    no_rt   = len(records) - has_rt
    print(f"  ✅ 실시간 현황 있음: {has_rt}건  |  미연계(NULL): {no_rt}건")

    print(f"💾 저장 완료 → {output}  ({len(records):,}건)")
    return str(output)


if __name__ == "__main__":
    main()