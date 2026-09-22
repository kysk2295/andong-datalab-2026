#!/usr/bin/env python3
"""데이터랩 지역별(시군구) 지표 벌크 수집 — 내부 API 기반.
한 호출로 2018.01~현재 전 기간 시계열이 반환된다.
결과: data/api_region/<qid>.csv  (long format, SGG_CD/SGG_NM 컬럼 부착)
"""
import csv, json, pathlib, sys, threading, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path("/Users/koyunseo/한국관광데이터분석")
OUT = ROOT / "data" / "api_region"; OUT.mkdir(parents=True, exist_ok=True)
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
HDR = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
       "X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0",
       "Referer": "https://datalab.visitkorea.or.kr/datalab/portal/loc/getAreaDataForm.do"}

# (qid, 설명, 추가파라미터)
QIDS = [
 ("LN_03_01_002", "월별_방문자수_외지인",      {"touDivCd": "2"}),
 ("LN_03_01_002", "월별_방문자수_현지인",      {"touDivCd": "1"}),
 ("LN_02_01_012", "월별_방문자추이",           {}),
 ("LN_04_01_009", "월별_방문자수_전년대비",    {}),
 ("LN_02_01_013", "월별_숙박비율_평균숙박일수",{}),
 ("LN_02_01_011", "숙박유형별_방문자",         {}),
 ("LN_02_01_004", "연령별_방문자1",            {}),
 ("LN_02_01_007", "연령별_방문자2",            {}),
 ("LN_03_03_058", "월별_카드소비",             {}),
 ("LN_03_03_059", "월별_카드소비2",            {}),
 ("LN_03_01_058", "월별_카드소비_상세",        {}),
 ("LN_11_01_010", "월별_결제금액_건수",        {}),
 ("LN_03_01_045", "업종별_소비비중",           {}),
 ("LN_03_01_046", "업종별_소비비중2",          {}),
 ("LN_03_01_065", "검색_중분류별",             {}),
 ("LN_04_01_013", "체류시간_숙박비율",         {}),
 ("LN_04_01_001", "관광진단지수",              {}),
 ("LN_04_01_003", "관광진단지수2",             {}),
 ("LN_03_01_053", "유입지_분포",               {}),
 ("LN_03_01_037", "관광지검색Top100",          {}),
 ("LN_03_01_038", "관광지검색Top100_외국인",   {}),
 ("LN_02_01_005", "요일별_방문",               {}),
]

BASE = dict(tabDiv="1", srchAreaDate="1", dispYn="Y", touDivCd="2",
            sggIntgYnFlag="N", sggIntgYnFlag2="N", yearOverGlobal="N",
            BASE_YR="2018", BASE_YM1="201801", BASE_YM2="202608",
            P_BASE_YM1="201701", P_BASE_YM2="202508", P_GAP="12", adminYn="N")

def fetch(qid, sgg_cd, sgg_nm, extra, tries=2):
    body = {**BASE, **extra, "qid": qid, "SGG_CD": sgg_cd, "SGG_NM": sgg_nm}
    data = urllib.parse.urlencode(body).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(API, data=data, headers=HDR)
            raw = urllib.request.urlopen(req, timeout=150).read().decode("utf-8", "replace")
            if not raw.strip():
                return []
            return json.loads(raw).get("list") or []
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(2 * (i + 1))

def main():
    regions = []
    codes = json.loads((ROOT / "data" / "region_codes.json").read_text(encoding="utf-8"))
    for sido_cd, v in codes.items():
        for s in v["sgg"]:
            regions.append((s["cd"], f'{v["name"]} {s["nm"]}'))
    print(f"시군구 {len(regions)}개 × 지표 {len(QIDS)}개 = {len(regions)*len(QIDS)} 호출", flush=True)

    for qid, label, extra in QIDS:
        path = OUT / f"{label}_{qid}.csv"
        if path.exists():
            print(f"skip {path.name}", flush=True); continue
        rows, fields, lock = [], [], threading.Lock()
        fail = 0

        def work(r):
            nonlocal fail
            cd, nm = r
            res = fetch(qid, cd, nm, extra)
            if res is None:
                with lock: fail += 1
                return
            with lock:
                for x in res:
                    if not isinstance(x, dict):
                        continue
                    for k in x:
                        if k not in fields: fields.append(k)
                    rows.append({"SGG_CD": cd, "SGG_NM": nm, **x})

        with ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(work, regions))

        if rows:
            with path.open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=["SGG_CD", "SGG_NM"] + fields)
                w.writeheader(); w.writerows(rows)
        print(f"{label:28} {qid}  rows={len(rows):<8} fail={fail}  -> {path.name}", flush=True)

if __name__ == "__main__":
    main()
