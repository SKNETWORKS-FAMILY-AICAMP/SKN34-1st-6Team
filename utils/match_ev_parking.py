import csv
import re
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARKING_PATH = ROOT / "data" / "raw" / "parking_raw.csv"
EV_PATHS = [
    ROOT / "data" / "raw" / "ev_charge_yn.csv",
    ROOT / "data" / "raw" / "ev_charge_yn(2).csv",
]
OUTPUT_PATH = ROOT / "data" / "processed" / "parking_ev_matches.csv"

SPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[()\[\],.\-]")
TOKEN_RE = re.compile(r"[\s,()\[\].\-]+")
DISTRICT_RE = re.compile(r"([가-힣]+구)")

COMMON_TOKENS = {
    "서울특별시",
    "서울시",
    "서울",
    "특별시",
    "광역시",
    "주차장",
    "공영주차장",
    "공영",
    "주민센터",
    "센터",
    "앞",
    "건물",
    "구",
    "시",
    "동",
}


def normalize(text: str) -> str:
    if not text:
        return ""
    return PUNCT_RE.sub("", SPACE_RE.sub("", text)).lower()


def tokenize(text: str):
    if not text:
        return []
    return [token for token in TOKEN_RE.split(text) if token and token not in COMMON_TOKENS]


def district(text: str) -> str:
    if not text:
        return ""
    match = DISTRICT_RE.search(text)
    return match.group(1) if match else ""


def similarity(a: str, b: str) -> float:
    na = normalize(a)
    nb = normalize(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def keyword_overlap(a: str, b: str) -> float:
    ta = set(tokenize(a))
    tb = set(tokenize(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def load_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_ev_rows():
    rows = []
    for path in EV_PATHS:
        if path.exists():
            rows.extend(load_rows(path))
    return rows


def dedupe_ev_rows(rows):
    seen = set()
    unique = []
    for row in rows:
        name = row.get("statNm") or row.get("충전소") or ""
        addr = row.get("addr") or row.get("주소") or ""
        key = (normalize(name), normalize(addr))
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def find_best_match(parking_row, ev_rows):
    p_name = parking_row.get("pk_name", "")
    p_addr = parking_row.get("pk_address", "")
    p_lat = parking_row.get("latitude", "")
    p_lng = parking_row.get("longitude", "")
    p_district = district(p_addr)

    best_row = None
    best_score = 0.0
    best_reason = ""

    for ev in ev_rows:
        e_name = ev.get("statNm") or ev.get("충전소") or ""
        e_addr = ev.get("addr") or ev.get("주소") or ""
        e_lat = ev.get("lat") or ev.get("latitude") or ""
        e_lng = ev.get("lng") or ev.get("longitude") or ""
        e_district = district(e_addr)

        name_sim = similarity(p_name, e_name)
        addr_sim = similarity(p_addr, e_addr)
        name_kw = keyword_overlap(p_name, e_name)
        addr_kw = keyword_overlap(p_addr, e_addr)

        # More permissive than the previous pass, but still favors address agreement.
        score = (
            addr_sim * 0.45
            + addr_kw * 0.22
            + name_sim * 0.20
            + name_kw * 0.08
        )

        if p_district and p_district == e_district:
            score += 0.05

        p_norm = normalize(p_name)
        e_norm = normalize(e_name)
        if p_norm and e_norm and (p_norm in e_norm or e_norm in p_norm):
            score += 0.12

        if p_lat and p_lng and e_lat and e_lng:
            try:
                lat_diff = abs(float(p_lat) - float(e_lat))
                lng_diff = abs(float(p_lng) - float(e_lng))
                geo_gap = (lat_diff ** 2 + lng_diff ** 2) ** 0.5
                if geo_gap < 0.01:
                    score += 0.10
                elif geo_gap < 0.03:
                    score += 0.06
                elif geo_gap < 0.05:
                    score += 0.03
            except ValueError:
                pass

        if score > best_score:
            best_score = score
            best_row = ev
            if p_norm and e_norm and (p_norm in e_norm or e_norm in p_norm):
                best_reason = "substring"
            elif addr_sim >= 0.55:
                best_reason = "address_similarity"
            else:
                best_reason = "similarity"

    # Loose threshold to capture more likely matches.
    if best_row and (
        best_score >= 0.50
        or (best_reason == "substring" and best_score >= 0.45)
        or (best_reason == "address_similarity" and best_score >= 0.48)
    ):
        return best_row, round(best_score, 3), best_reason

    return None, 0.0, ""


def find_matches():
    parking_rows = load_rows(PARKING_PATH)
    ev_rows = dedupe_ev_rows(load_ev_rows())

    matches = []
    for parking in parking_rows:
        ev, score, reason = find_best_match(parking, ev_rows)
        if not ev:
            continue

        matches.append(
            {
                "주차장명": parking.get("pk_name", ""),
                "충전소": ev.get("statNm") or ev.get("충전소") or "",
                "매칭점수": score,
                "매칭방식": reason,
                "주차장주소": parking.get("pk_address", ""),
                "충전소주소": ev.get("addr") or ev.get("주소") or "",
                "데이터": "EV충전소",
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "주차장명",
                "충전소",
                "매칭점수",
                "매칭방식",
                "주차장주소",
                "충전소주소",
                "데이터",
            ],
        )
        writer.writeheader()
        writer.writerows(matches)

    return matches


if __name__ == "__main__":
    matches = find_matches()
    print(f"매칭 개수: {len(matches)}")
    for row in matches[:20]:
        print(row)
    print(f"저장 위치: {OUTPUT_PATH}")
