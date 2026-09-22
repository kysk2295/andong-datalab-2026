#!/usr/bin/env python3
"""데이터랩 문화관광축제 전체(86개) — 축제 목록(기간·지역) + 연도별 방문자(FE_01_01_005_01, 1회 호출=전 연도)
+ 관광소비(FE_01_01_007) → data/축제_전체/. 1.5s 간격 단일 스레드 (대량 재수집 금지 규칙)."""
import csv, json, time, pathlib, urllib.parse, urllib.request, http.cookiejar, re
H = "https://datalab.visitkorea.or.kr"; OUT = pathlib.Path(__file__).resolve().parents[1] / "data/축제_전체"
cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
UA = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}; ref = "/datalab/portal/fes/getFesDataForm.do"
page = op.open(urllib.request.Request(H + ref, headers=UA), timeout=60).read().decode("utf-8", "replace")
def post_json(path, body):
    h = {**UA, "Content-Type": "application/json", "Referer": H + ref, "Origin": H}
    return json.loads(op.open(urllib.request.Request(H + path, data=json.dumps(body).encode(), headers=h), timeout=120).read().decode())
def tq(**p):
    h = {**UA, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "Referer": H + ref, "Origin": H}
    for a in range(3):
        try:
            raw = op.open(urllib.request.Request(H + "/visualize/getTempleteData.do", data=urllib.parse.urlencode(p).encode(), headers=h), timeout=150).read().decode("utf-8", "replace")
            return json.loads(raw).get("list") or [] if raw.strip() else []
        except Exception as e: print("retry", p.get("FSTV_ID"), e, flush=True); time.sleep(5 * (a + 1))
    return None
def save(name, rows):
    if not rows: print(f"{name}: 0행", flush=True); return
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"{name}: {len(rows)}행", flush=True)
# 1) 축제 목록
lst = []
for i in range(1, 20):
    try: d = post_json("/datalab/portal/fes/getFesList.do", {"sidoAreaSel": "", "sggAreaSel": "", "fesNm": "", "currentIndex": i, "recordCountPerPage": 50, "pageSize": 10})
    except Exception as e: print("list err", e, flush=True); break
    items = d.get("list") or []
    if not items: break
    lst += items; time.sleep(1.5)
    if len(items) < 50: break
save("축제목록_getFesList", lst)
ids = sorted({r["FSTV_ID"] for r in lst if "FSTV_ID" in r} | set(re.findall(r"KCTF\d{4}", page)))
print("축제 ID", len(ids), flush=True)
# 2) 연도별 방문자 + 관광소비 (전 연도 한 번에)
for q, lab in [("FE_01_01_005_01", "연도별방문자"), ("FE_01_01_007", "관광소비")]:
    if (OUT / f"{lab}_{q}.csv").exists(): continue
    rows = []
    for fid in ids:
        res = tq(qid=q, FSTV_ID=fid, BASE_YY1="2018", BASE_YY2="2025", BASE_YM1="2018", BASE_YM2="2025", querySpace="FesDao", ALL_YN="Y"); time.sleep(1.5)
        rows += res or []
    save(f"{lab}_{q}", rows)
print("DONE", flush=True)
