import csv
import re
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARKING_PATH = ROOT / "data" / "raw" / "parking_raw.csv"
EV_PATH = ROOT / "data" / "raw" / "ev_charge_yn.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "parking_ev_matches.csv"


def normalize_name(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("공영주차장", "주차장")
    text = text.replace("공영", "")
    text = text.replace("주차장", "")
    text = text.replace("주차", "")
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^가-힣a-z0-9]+", "", text)
    return text


def tokenize(text: str):
    return [t for t in re.split(r"[^가-힣a-z0-9]+", text) if t]


def find_matches():
    with PARKING_PATH.open(encoding="utf-8-sig", newline="") as f:
        parking_rows = list(csv.DictReader(f))

    with EV_PATH.open(encoding="utf-8-sig", newline="") as f:
        ev_rows = list(csv.DictReader(f))

    matches = []
    for p in parking_rows:
        p_name = p.get("pk_name", "")
        p_norm = normalize_name(p_name)
        if not p_norm:
            continue

        best_match = None
        best_score = 0.0
        best_reason = ""

        for e in ev_rows:
            e_name = e.get("statNm", "")
            e_norm = normalize_name(e_name)
            if not e_norm:
                continue

            if p_norm in e_norm or e_norm in p_norm:
                score = 1.0
                reason = "substring"
            else:
                tokens1 = set(tokenize(p_norm))
                tokens2 = set(tokenize(e_norm))
                overlap = len(tokens1 & tokens2) / max(len(tokens1 | tokens2), 1)
                seq = difflib.SequenceMatcher(None, p_norm, e_norm).ratio()
                score = max(overlap, seq)
                reason = "similarity"

            if score > best_score:
                best_score = score
                best_match = e
                best_reason = reason

        if best_match and best_score >= 0.55:
            matches.append({
                "주차장명": p_name,
                "충전소": best_match.get("statNm", ""),
                "매칭점수": round(best_score, 3),
                "매칭방식": best_reason,
                "주차장주소": p.get("pk_address", ""),
                "충전소주소": best_match.get("addr", ""),
                "데이터": "EV충전소",
            })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "주차장명", "충전소", "매칭점수", "매칭방식", "주차장주소", "충전소주소", "데이터"
        ])
        writer.writeheader()
        writer.writerows(matches)

    return matches


if __name__ == "__main__":
    matches = find_matches()
    print(f"매칭 건수: {len(matches)}")
    for row in matches[:20]:
        print(row)
    print(f"저장 위치: {OUTPUT_PATH}")
