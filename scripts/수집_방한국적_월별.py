#!/usr/bin/env python3
"""방한 외래객 국적 월별 수집 (데이터랩 TS_01_16_005_New). 시군 단위가 아님."""
import json, csv, time, urllib.parse, urllib.request
from pathlib import Path
from collections import defaultdict

API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/ts/getEntcnyFrgnCust2Form.do",
}
OUT = Path("/Users/koyunseo/한국관광데이터분석/data/api")
OUT.mkdir(parents=True, exist_ok=True)

def call(**params):
    data = urllib.parse.urlencode({"adminYn": "N", **params}).encode()
    req = urllib.request.Request(API, data=data, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", "replace")
    return json.loads(raw)

res = call(
    qid="TS_01_16_005_New",
    srchAreaDate="1",
    BASE_YM1="202101",
    BASE_YM2="202608",
    srchBgngYear="2021",
    srchEndYear="2026",
    srchBgngMm="01",
    srchEndMm="08",
)
lst = res.get("list") or []
print("rows", len(lst), "sample", lst[0] if lst else None)
(OUT / "방한외래관광객_TS_01_16_005_New_월간_2021-202608.json").write_text(
    json.dumps(res, ensure_ascii=False), encoding="utf-8"
)

# flatten to csv
keys = sorted({k for row in lst for k in row})
with (OUT / "방한외래관광객_국적_성별_월별_2021-202608.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(lst)
print("saved csv", len(lst))
