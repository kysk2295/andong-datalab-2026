#!/usr/bin/env python3
"""데이터랩 '지역별 관광 현황' 미수집 지표(LN_*) → data/datalab_추가/  (9/14 탐색으로 안동 응답 확인된 qid만)
천천히(0.8s 간격, 단일 스레드) 호출 — 과거 대량 호출로 차단된 이력 있음."""
import csv, json, time, pathlib, urllib.parse, urllib.request, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from datalab_region_bulk import BASE, API, HDR
ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / "data/datalab_추가"; OUT.mkdir(exist_ok=True)
codes = json.loads((ROOT / "data/region_codes.json").read_text(encoding="utf-8"))
NAME = {s["cd"]: f'{v["name"]} {s["nm"]}' for v in codes.values() for s in v["sgg"]}
ANDONG = "47170"; CMP = ["47130", "44150", "44760", "47280", "52190", "43130"]  # 경주 공주 부여 문경 남원 충주
SERIES = {  # 월별 시계열 → 전 기간 1회
 "LN_03_012_001_001": "주요관광지_월별방문자_전체", "LN_03_012_001_002": "주요관광지_월별방문자_내국인",
 "LN_03_012_001_003": "주요관광지_월별방문자_외국인", "LN_02_01_011_001": "순방문자_숙박비율_월별",
 "LN_03_01_052": "숙박일수분포_월별", "LN_03_03_058_01": "지역화폐_관광소비_월별", "LN_02_01_013_01": "숙박비율_평균숙박일_월별"}
AGG = {  # 기간 합산형 → 창(window)별
 "LN_03_01_011": "유입_출발지x업종유형", "LN_03_01_012": "유출_목적지x업종유형", "LN_03_01_043": "중심관광지",
 "LN_03_01_042": "중심x연관관광지", "LN_03_01_036": "관심관광지_현지인", "LN_03_01_038": "관심관광지_외지인",
 "LN_03_01_039": "맛집검색_현지인", "LN_03_01_040": "맛집검색_외지인", "LN_03_01_041": "중심맛집",
 "LN_03_01_004": "목적지유형별_검색", "LN_04_01_010": "유입지역_비율", "LN_04_01_008": "방문자_거주지분포",
 "LN_03_010_003": "거리별_방문자", "LN_03_01_055": "성연령x업종_소비", "LN_03_01_056": "업종대분류_소비",
 "LN_04_01_006": "업종별_소비_내국인", "LN_04_01_006_001": "업종별_소비_외지인", "LN_03_01_067": "목적지유형_검색분포",
 "LN_03_01_030": "유사지역_관광진단", "LN_03_01_031": "유사지역_내비유형", "LN_03_01_071": "유사지역_성연령",
 "LN_03_01_073": "유사지역_소비업종", "LN_03_01_075": "유사지역_기타", "LN_04_00_001": "관광유형_분류", "LN_03_01_015": "관광진단_세부"}
WIN = {"2024_1-8": ("202401", "202408"), "2026_1-8": ("202601", "202608"), "2025": ("202501", "202512")}
CMP_AGG = ["LN_03_01_011", "LN_03_01_012", "LN_03_01_043", "LN_03_01_042", "LN_04_01_006_001", "LN_03_01_004"]
FORECAST = {"LN_04_01_011": "향후30일_집중률예측", "LN_02_01_005": "요일별_집중률예측"}
LOG = OUT / "_수집로그.tsv"

def call(qid, cd, y1, y2):
    body = {**BASE, "qid": qid, "SGG_CD": cd, "SGG_NM": NAME[cd], "SIDO_CD": cd[:2], "BASE_YM1": y1, "BASE_YM2": y2}
    for a in range(3):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(body).encode(), headers=HDR), timeout=150).read().decode("utf-8", "replace")
            return json.loads(raw).get("list") or [] if raw.strip() else []
        except Exception as e:
            err = str(e)[:60]; time.sleep(5 * (a + 1))
    return None

def save(name, rows):
    if not rows: return
    cols = []
    for r in rows:
        for k in r:
            if k not in cols: cols.append(k)
    with (OUT / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

def job(qid, label, cds, wins):
    for wn, (y1, y2) in wins.items():
        name = f"{label}_{qid}" + (f"_{wn}" if wn else "")
        if (OUT / f"{name}.csv").exists(): continue
        rows, fail = [], 0
        for cd in cds:
            res = call(qid, cd, y1, y2); time.sleep(0.8)
            if res is None: fail += 1; continue
            rows += [{"조회_SGG_CD": cd, "조회_지역": NAME[cd], "조회기간": f"{y1}-{y2}", **r} for r in res if isinstance(r, dict)]
        save(name, rows)
        line = f"{name}\t{len(rows)}\tfail={fail}"; print(line, flush=True)
        with LOG.open("a", encoding="utf-8") as f: f.write(line + "\n")

for q, l in SERIES.items(): job(q, l, [ANDONG] + CMP, {"": ("201801", "202608")})
for q, l in AGG.items(): job(q, l, [ANDONG] + (CMP if q in CMP_AGG else []), WIN)
for q, l in FORECAST.items(): job(q, l, [ANDONG], {"": ("202608", "202608")})
print("DONE", flush=True)
