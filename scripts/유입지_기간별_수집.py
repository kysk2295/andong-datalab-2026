#!/usr/bin/env python3
"""LN_03_01_053(외지인 유입지 분포)을 기간별로 재호출 — 교통 호재 전후 출발지 구성 변화 확인용."""
import csv, json, time, urllib.parse, urllib.request, pathlib
from concurrent.futures import ThreadPoolExecutor
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest",
       "User-Agent": "Mozilla/5.0", "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do"}
BASE = dict(tabDiv="1", srchAreaDate="1", dispYn="Y", touDivCd="2", sggIntgYnFlag="N", sggIntgYnFlag2="N",
            yearOverGlobal="N", P_GAP="12", adminYn="N")
SGG = {"47170": "경상북도 안동시", "47130": "경상북도 경주시", "47111": "경상북도 포항시 남구", "47113": "경상북도 포항시 북구",
       "52111": "전북특별자치도 전주시 완산구", "52113": "전북특별자치도 전주시 덕진구", "52130": "전북특별자치도 군산시",
       "47210": "경상북도 영주시", "43150": "충청북도 제천시", "43800": "충청북도 단양군", "47230": "경상북도 영천시"}
PER = {str(y): (f"{y}01", f"{y}12") for y in range(2018, 2026)}
PER |= {f"{y}_1-8": (f"{y}01", f"{y}08") for y in (2024, 2025, 2026)}
def fetch(job):
    cd, per = job; a, b = PER[per]
    body = {**BASE, "qid": "LN_03_01_053", "SGG_CD": cd, "SGG_NM": SGG[cd], "BASE_YR": a[:4], "BASE_YM1": a, "BASE_YM2": b,
            "P_BASE_YM1": str(int(a) - 100), "P_BASE_YM2": str(int(b) - 100)}
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(), headers=HDR), timeout=90).read().decode()
            return cd, per, (json.loads(r).get("list") or []) if r.strip() else []
        except Exception:
            time.sleep(2 + 2 * i)
    return cd, per, None
jobs = [(c, p) for c in SGG for p in PER]
out = pathlib.Path("data/api_region/유입지_기간별_LN_03_01_053.csv")
rows, fail = [], []
with ThreadPoolExecutor(6) as ex:
    for cd, per, L in ex.map(fetch, jobs):
        if L is None: fail.append((cd, per)); continue
        for r in L: rows.append({"SGG_CD": cd, "SGG_NM": SGG[cd], "PERIOD": per, **r})
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("rows", len(rows), "fail", fail)
