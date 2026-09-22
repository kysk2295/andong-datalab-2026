#!/usr/bin/env python3
"""안동 읍면동별 외지인 방문(BDT_01_01_005_1) 월별 재수집 — 풍산읍 급감 시점 확인용."""
import csv, json, time, urllib.parse, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
       "User-Agent": "Mozilla/5.0", "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do"}
BASE = dict(tabDiv="1", srchAreaDate="1", dispYn="Y", touDivCd="2", sggIntgYnFlag="N", sggIntgYnFlag2="N",
            yearOverGlobal="N", P_GAP="12", adminYn="N", qid="BDT_01_01_005_1", SGG_CD="47170", SGG_NM="경상북도 안동시")
yms = [f"{y}{m:02d}" for y in range(2018, 2027) for m in range(1, 13) if f"{y}{m:02d}" <= "202608"]
def fetch(ym):
    body = {**BASE, "BASE_YR": ym[:4], "BASE_YM1": ym, "BASE_YM2": ym, "P_BASE_YM1": str(int(ym) - 100), "P_BASE_YM2": str(int(ym) - 100)}
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(), headers=HDR), timeout=90).read().decode()
            return ym, (json.loads(r).get("list") or []) if r.strip() else []
        except Exception:
            time.sleep(2 + 2 * i)
    return ym, None
rows, fail = [], []
with ThreadPoolExecutor(6) as ex:
    for ym, L in ex.map(fetch, yms):
        if L is None: fail.append(ym); continue
        rows += [{"BASE_YM": ym, "AREA_NM": r["AREA_NM"], "EMD_CD": r["SGG_CD"], "TOU_NUM": r["TOU_NUM"]} for r in L]
out = pathlib.Path("data/api_region/안동_읍면동별_외지인_월별_BDT_01_01_005_1.csv")
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("rows", len(rows), "fail", fail)
