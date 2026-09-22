#!/usr/bin/env python3
"""2차: 읍면동별 외지인 방문(BDT_01_01_005_1), 관광지 검색 Top100(LN_03_01_037)을 연도별로 재수집."""
import csv, json, time, urllib.parse, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
       "User-Agent": "Mozilla/5.0", "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do"}
BASE = dict(tabDiv="1", srchAreaDate="1", dispYn="Y", touDivCd="2", sggIntgYnFlag="N", sggIntgYnFlag2="N",
            yearOverGlobal="N", P_GAP="12", adminYn="N")
SGG = {"47170": "경상북도 안동시", "47130": "경상북도 경주시", "47210": "경상북도 영주시", "52130": "전북특별자치도 군산시",
       "52111": "전북특별자치도 전주시 완산구", "47111": "경상북도 포항시 남구", "47113": "경상북도 포항시 북구"}
PER = {str(y): (f"{y}01", f"{y}12") for y in range(2018, 2026)} | {f"{y}_1-8": (f"{y}01", f"{y}08") for y in (2024, 2025, 2026)}
QIDS = {"BDT_01_01_005_1": ["47170", "47130", "47210"], "LN_03_01_037": list(SGG)}
def fetch(job):
    qid, cd, per = job; a, b = PER[per]
    body = {**BASE, "qid": qid, "SGG_CD": cd, "SGG_NM": SGG[cd], "BASE_YR": a[:4], "BASE_YM1": a, "BASE_YM2": b,
            "P_BASE_YM1": str(int(a) - 100), "P_BASE_YM2": str(int(b) - 100)}
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(), headers=HDR), timeout=90).read().decode()
            return job, (json.loads(r).get("list") or []) if r.strip() else []
        except Exception:
            time.sleep(2 + 2 * i)
    return job, None
for qid, cds in QIDS.items():
    jobs = [(qid, c, p) for c in cds for p in PER]
    rows, fail = [], []
    with ThreadPoolExecutor(6) as ex:
        for (q, cd, per), L in ex.map(fetch, jobs):
            if L is None: fail.append((cd, per)); continue
            rows += [{"Q_SGG_CD": cd, "Q_SGG_NM": SGG[cd], "PERIOD": per, **r} for r in L]
    keys = list(dict.fromkeys(k for r in rows for k in r))
    out = pathlib.Path(f"data/api_region/{'읍면동별_외지인' if qid.startswith('BDT') else '관광지검색Top100'}_기간별_{qid}.csv")
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print(qid, "rows", len(rows), "fail", fail)
