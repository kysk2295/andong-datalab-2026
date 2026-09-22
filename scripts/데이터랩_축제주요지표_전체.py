#!/usr/bin/env python3
"""데이터랩 문화관광축제 86개 주요지표(FE_01_01_003_01: 외부/현지인 유입·내비검색·관광소비·축제지 집중률, 축제기간 vs 비축제기간)
2024·2025 → data/축제_전체/. 연도별 1회 호출, 1.5s 간격."""
import csv, json, time, pathlib, re, urllib.parse, urllib.request, http.cookiejar
H = "https://datalab.visitkorea.or.kr"; OUT = pathlib.Path(__file__).resolve().parents[1] / "data/축제_전체"
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
UA = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}; ref = "/datalab/portal/fes/getFesDataForm.do"
page = op.open(urllib.request.Request(H + ref, headers=UA), timeout=60).read().decode("utf-8", "replace")
ids = sorted(set(re.findall(r"KCTF\d{4}", page)))
h = {**UA, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Referer": H + ref, "Origin": H}
rows = []
for fid in ids:
    for y in ["2024", "2025"]:
        p = dict(qid="FE_01_01_003_01", FSTV_ID=fid, BASE_YY1=y, BASE_YY2=y, BASE_YM1="2018", BASE_YM2="2025", querySpace="FesDao", ALL_YN="Y")
        for a in range(3):
            try:
                raw = op.open(urllib.request.Request(H + "/visualize/getTempleteData.do", data=urllib.parse.urlencode(p).encode(), headers=h), timeout=150).read().decode("utf-8", "replace")
                rows += [{"조회연도": y, **r} for r in (json.loads(raw).get("list") or [])] if raw.strip() else []; break
            except Exception as e: print("retry", fid, y, e, flush=True); time.sleep(5 * (a + 1))
        time.sleep(1.5)
cols = list(dict.fromkeys(k for r in rows for k in r))
with (OUT / "주요지표_집중률_FE_01_01_003_01.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
print("주요지표:", len(rows), "행 DONE", flush=True)
