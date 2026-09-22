#!/usr/bin/env python3
"""안동·영주·경주·전주 월별 외지인 유입지 분포(LN_03_01_053) 2019.01~2026.08 — 개통 전후 월별 수도권·부울경 비중."""
import csv, json, time, urllib.parse, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
       "User-Agent": "Mozilla/5.0", "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do"}
BASE = dict(tabDiv="1", srchAreaDate="1", dispYn="Y", touDivCd="2", sggIntgYnFlag="N", sggIntgYnFlag2="N", yearOverGlobal="N", P_GAP="12", adminYn="N", qid="LN_03_01_053")
SGG = {"47170": "경상북도 안동시", "47210": "경상북도 영주시", "47130": "경상북도 경주시", "52111": "전북특별자치도 전주시 완산구"}
yms = [f"{y}{m:02d}" for y in range(2019, 2027) for m in range(1, 13) if f"{y}{m:02d}" <= "202608"]
REG = {"수도권": {"서울특별시", "경기도", "인천광역시"}, "부울경": {"부산광역시", "울산광역시", "경상남도"}, "대구": {"대구광역시"}, "경북": {"경상북도"}}
def fetch(job):
    cd, ym = job
    body = {**BASE, "SGG_CD": cd, "SGG_NM": SGG[cd], "BASE_YR": ym[:4], "BASE_YM1": ym, "BASE_YM2": ym, "P_BASE_YM1": str(int(ym) - 100), "P_BASE_YM2": str(int(ym) - 100)}
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(), headers=HDR), timeout=90).read().decode()
            L = (json.loads(r).get("list") or []) if r.strip() else []
            tot = sum(x["DTL_TOU_NUM"] or 0 for x in L)
            if not tot: return None
            return {"SGG_CD": cd, "BASE_YM": ym, **{k: round(sum(x["DTL_TOU_NUM"] or 0 for x in L if x["DPTR_REGN_NM"] in S) / tot * 100, 2) for k, S in REG.items()}}
        except Exception:
            time.sleep(2 + 2 * i)
with ThreadPoolExecutor(8) as ex: rows = [x for x in ex.map(fetch, [(c, m) for c in SGG for m in yms]) if x]
out = pathlib.Path("data/api_region/유입권역비중_월별_4개도시_LN_03_01_053.csv")
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("rows", len(rows))
