#!/usr/bin/env python3
"""풍산읍·용상동 감소 원인 진단용: 안동 읍면동 월별 '현지인'(touDivCd=1) + 예천 읍면 월별 외지인(touDivCd=2)."""
import csv, json, time, urllib.parse, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
       "User-Agent": "Mozilla/5.0", "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do"}
BASE = dict(tabDiv="1", srchAreaDate="1", dispYn="Y", sggIntgYnFlag="N", sggIntgYnFlag2="N", yearOverGlobal="N", P_GAP="12", adminYn="N", qid="BDT_01_01_005_1")
JOBS = {("47170", "경상북도 안동시", "1"): "안동_현지인", ("47900", "경상북도 예천군", "2"): "예천_외지인"}
yms = [f"{y}{m:02d}" for y in range(2018, 2027) for m in range(1, 13) if f"{y}{m:02d}" <= "202608"]
def fetch(job):
    (cd, nm, tou), ym = job
    body = {**BASE, "touDivCd": tou, "SGG_CD": cd, "SGG_NM": nm, "BASE_YR": ym[:4], "BASE_YM1": ym, "BASE_YM2": ym, "P_BASE_YM1": str(int(ym) - 100), "P_BASE_YM2": str(int(ym) - 100)}
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(), headers=HDR), timeout=90).read().decode()
            return job, (json.loads(r).get("list") or []) if r.strip() else []
        except Exception: time.sleep(2 + 2 * i)
    return job, None
rows, fail = [], []
with ThreadPoolExecutor(8) as ex:
    for (k, ym), L in ex.map(fetch, [(k, m) for k in JOBS for m in yms]):
        if L is None: fail.append((JOBS[k], ym)); continue
        rows += [{"구분": JOBS[k], "BASE_YM": ym, "AREA_NM": r["AREA_NM"], "TOU_NUM": r["TOU_NUM"]} for r in L]
out = pathlib.Path("data/api_region/읍면동_월별_진단_현지인_예천.csv")
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("rows", len(rows), "fail", len(fail))
