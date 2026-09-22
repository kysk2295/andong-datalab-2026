#!/usr/bin/env python3
"""한국관광 데이터랩 내부 API 수집기.
POST /visualize/getTempleteData.do  (qid 기반)
"""
import json, time, urllib.parse, urllib.request, pathlib, sys

API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
OUT = pathlib.Path("/Users/koyunseo/한국관광데이터분석/data/api")
OUT.mkdir(parents=True, exist_ok=True)

HDR = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0",
}

def call(qid, referer, **params):
    body = {"qid": qid, "adminYn": "N", **params}
    data = urllib.parse.urlencode(body).encode()
    req = urllib.request.Request(API, data=data, headers={**HDR, "Referer": referer})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", "replace")
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw[:2000]}

def save(name, obj):
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(obj.get("list", [])) if isinstance(obj, dict) else 0
    print(f"  saved {p.name}  rows={n}")
    return n

# 페이지별 qid 목록 (HTML에서 추출)
PAGES = {
 "방한외래관광객":      ("ts/getEntcnyFrgnCust2Form", [f"TS_01_16_{i:03d}" for i in range(1,11)]),
 "국민해외관광객":      ("ts/getDtrmcNatiCust2Form", [f"TS_01_17_{i:03d}" for i in range(1,9)]),
 "관광수지":            ("ts/getKorTursmBalcForm",   [f"TS_01_03_{i:03d}" for i in range(1,5)]),
 "세계관광통계":        ("ts/getWldTursmStatsForm",  [f"TS_01_08_{i:03d}" for i in range(1,3)]),
 "크루즈통계":          ("ts/getNewCrusStatsForm",   [f"TS_01_04_{i:03d}" for i in range(1,13)]+[f"TS_01_05_{i:03d}" for i in range(1,9)]),
 "국민여행조사":        ("ts/getDomTourExmn",        [f"TS_03_01_{i:03d}" for i in [1,2,3,4,5,6,10,11,12]]),
 "외래관광객조사":      ("ts/getOseaTourExmn",       [f"TS_03_02_{i:03d}" for i in list(range(1,9))+list(range(11,18))]),
}

# 조회 단위: 4=연간, 1=월간
RANGES = [
    ("연간", dict(srchAreaDate="4", BASE_YM1="1995", BASE_YM2="2026",
                  srchBgngYear="1995", srchEndYear="2026", srchBgngMm="01", srchEndMm="12")),
    ("월간", dict(srchAreaDate="1", BASE_YM1="199501", BASE_YM2="202612",
                  srchBgngYear="1995", srchEndYear="2026", srchBgngMm="01", srchEndMm="12")),
]

def main(only=None):
    total = 0
    for page, (path, qids) in PAGES.items():
        if only and only not in page:
            continue
        ref = f"https://datalab.visitkorea.or.kr/datalab/portal/{path}.do"
        print(f"\n### {page}  ({len(qids)} qid)")
        for qid in qids:
            for label, prm in RANGES:
                try:
                    res = call(qid, ref, **prm)
                except Exception as e:
                    print(f"  {qid} {label}: ERR {e}"); continue
                if not res:
                    print(f"  {qid} {label}: empty response"); continue
                rows = res.get("list") if isinstance(res, dict) else None
                if not rows:
                    print(f"  {qid} {label}: no rows"); continue
                total += save(f"{page}_{qid}_{label}", res)
                time.sleep(0.3)
    print(f"\n총 {total} rows")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
