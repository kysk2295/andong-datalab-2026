#!/usr/bin/env python3
"""데이터랩 테마별 분석: 문화관광축제(안동탈춤축제 KCTF0041) + 야간관광(시도 단위, 안동 동네 포함) → data/datalab_추가/
세션 쿠키 필요(KSESSIONID). 0.8s 간격 단일 스레드."""
import csv, json, time, pathlib, urllib.parse, urllib.request, http.cookiejar
H = "https://datalab.visitkorea.or.kr"; OUT = pathlib.Path(__file__).resolve().parents[1] / "data/datalab_추가"
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
UA = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
def tq(ref, **p):
    h = {**UA, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Referer": H + ref, "Origin": H}
    for a in range(3):
        try:
            raw = op.open(urllib.request.Request(H + "/visualize/getTempleteData.do", data=urllib.parse.urlencode(p).encode(), headers=h), timeout=150).read().decode("utf-8", "replace")
            return json.loads(raw).get("list") or [] if raw.strip() else []
        except Exception: time.sleep(5 * (a + 1))
    return None
def save(name, rows):
    if not rows: print(f"{name}: 0행", flush=True); return
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"{name}: {len(rows)}행", flush=True)

# ---- 문화관광축제: 안동탈춤축제, 제공 연도 전부
ref = "/datalab/portal/fes/getFesDataForm.do"; op.open(urllib.request.Request(H + ref, headers=UA), timeout=60).read()
FE = {"FE_01_01_003_01": "주요지표", "FE_01_01_004_00": "목적지검색순위", "FE_01_01_002": "방문자거주지",
      "FE_01_01_005_01": "연도별방문자", "FE_01_01_006": "성연령_내국인", "FE_01_01_007": "관광소비", "FE_01_01_008": "업종별소비"}
for q, lab in FE.items():
    if (OUT / f"축제_안동탈춤_{lab}_{q}.csv").exists(): continue
    rows = []
    for y in ["2018", "2019", "2022", "2023", "2024", "2025"]:
        res = tq(ref, qid=q, FSTV_ID="KCTF0041", BASE_YY1=y, BASE_YY2=y, BASE_YM1="2018", BASE_YM2="2025", querySpace="FesDao", ALL_YN="Y"); time.sleep(0.8)
        rows += [{"조회연도": y, **r} for r in (res or [])]
    save(f"축제_안동탈춤_{lab}_{q}", rows)

# ---- 야간관광: 시도 단위(경북 47 + 비교 시도 충남44·전북52·충북43 + 전국 00), 기간 3창
ref = "/datalab/portal/theme/getNightTourSearch.do"; op.open(urllib.request.Request(H + ref, headers=UA), timeout=60).read()
NT = ["BY_TH_NIGHT_TOUR_001_001", "BY_TH_NIGHT_TOUR_001_002", "BY_TH_NIGHT_TOUR_001_004", "BY_TH_NIGHT_TOUR_001_005", "BY_TH_NIGHT_TOUR_001_009",
      "BY_TH_NIGHT_TOUR_002_001", "BY_TH_NIGHT_TOUR_002_002", "BY_TH_NIGHT_TOUR_002_004", "BY_TH_NIGHT_TOUR_002_005", "BY_TH_NIGHT_TOUR_002_009",
      "BY_TH_NIGHT_TOUR_002_011", "BY_TH_NIGHT_TOUR_002_012", "BY_TH_NIGHT_TOUR_002_013", "BY_TH_NIGHT_TOUR_002_014",
      "BY_TH_NIGHT_TOUR_003_001", "BY_TH_NIGHT_TOUR_003_002", "BY_TH_NIGHT_TOUR_003_003", "BY_TH_NIGHT_TOUR_003_004", "BY_TH_NIGHT_TOUR_003_005", "BY_TH_NIGHT_TOUR_003_006"]
WIN = {"2024_1-8": ("202401", "202408"), "2026_1-8": ("202601", "202608"), "2025": ("202501", "202512")}
t = tq(ref, qid="BY_TH_NIGHT_TOUR_001_001", sggCd="47170", SGG_CD="47170", SIDO_CD="47", BASE_YM1="202501", BASE_YM2="202512", BASE_YR="2025", tabDiv="1", touDivCd="1", srchAreaDate="1")
print("시군(47170) 직접 조회:", len(t or []), (t or [""])[0], flush=True); time.sleep(0.8)
for q in NT:
    if (OUT / f"야간관광_{q}.csv").exists(): continue
    rows = []
    for sd in ["47", "44", "52", "43", "00"]:
        for wn, (y1, y2) in WIN.items():
            tab = q.split("_")[3][2]  # 001→1, 002→2, 003→3
            res = tq(ref, qid=q, sggCd=sd, SGG_CD=sd, SIDO_CD=sd, BASE_YM1=y1, BASE_YM2=y2, BASE_YR=y1[:4], tabDiv=tab, touDivCd="1", srchAreaDate="1"); time.sleep(0.8)
            rows += [{"조회_시도": sd, "조회기간": wn, **r} for r in (res or [])]
    save(f"야간관광_{q}", rows)
print("DONE", flush=True)
