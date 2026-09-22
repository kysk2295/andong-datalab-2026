#!/usr/bin/env python3
"""전국 시군구 × (2019, 2022, 2023, 2025) 외지인 유입지 분포(LN_03_01_053) — 수도권·부울경 비중 변화 산점도용."""
import csv, json, time, urllib.parse, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
       "User-Agent": "Mozilla/5.0", "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do"}
BASE = dict(tabDiv="1", srchAreaDate="1", dispYn="Y", touDivCd="2", sggIntgYnFlag="N", sggIntgYnFlag2="N", yearOverGlobal="N", P_GAP="12", adminYn="N", qid="LN_03_01_053")
codes = json.loads(pathlib.Path("data/region_codes.json").read_text(encoding="utf-8"))
regs = [(s["cd"], f'{v["name"]} {s["nm"]}') for v in codes.values() for s in v["sgg"]]
PER = {"2019": ("201901", "201912"), "2022": ("202201", "202212"), "2023": ("202301", "202312"), "2025": ("202501", "202512")}
MET = {"서울특별시", "경기도", "인천광역시"}; BUG = {"부산광역시", "울산광역시", "경상남도"}; DG = {"대구광역시", "경상북도"}
def fetch(job):
    (cd, nm), per = job; a, b = PER[per]
    body = {**BASE, "SGG_CD": cd, "SGG_NM": nm, "BASE_YR": a[:4], "BASE_YM1": a, "BASE_YM2": b, "P_BASE_YM1": str(int(a) - 100), "P_BASE_YM2": str(int(b) - 100)}
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(), headers=HDR), timeout=90).read().decode()
            L = (json.loads(r).get("list") or []) if r.strip() else []
            tot = sum(x["DTL_TOU_NUM"] or 0 for x in L)
            if not tot: return None
            f = lambda S: sum(x["DTL_TOU_NUM"] or 0 for x in L if x["DPTR_REGN_NM"] in S) / tot * 100
            return {"SGG_CD": cd, "SGG_NM": nm, "PERIOD": per, "수도권": round(f(MET), 2), "부울경": round(f(BUG), 2), "대구경북": round(f(DG), 2), "합계": tot}
        except Exception:
            time.sleep(2 + 2 * i)
    return None
jobs = [(r, p) for r in regs for p in PER]
with ThreadPoolExecutor(8) as ex: rows = [x for x in ex.map(fetch, jobs) if x]
out = pathlib.Path("data/api_region/유입권역비중_전국_연도별_LN_03_01_053.csv")
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("rows", len(rows), "of", len(jobs))
