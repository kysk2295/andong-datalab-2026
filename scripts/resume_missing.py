#!/usr/bin/env python3
"""차단 해제를 기다렸다가 미확보 항목만 저속으로 수집한다.
- 동시 요청 1개, 요청 간 2.5초 간격 (재차단 방지)
- 5분마다 연결 확인, 살아나면 즉시 수집 시작
"""
import csv, json, pathlib, time, urllib.parse, urllib.request

ROOT = pathlib.Path("/Users/koyunseo/한국관광데이터분석")
OUT  = ROOT / "data" / "missing"; OUT.mkdir(parents=True, exist_ok=True)
LOG  = OUT / "_수집로그.txt"
API  = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"

def log(m):
    line = f"{time.strftime('%H:%M:%S')} {m}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f: f.write(line + "\n")

def hdr(page):
    return {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0",
            "Referer": f"https://datalab.visitkorea.or.kr/datalab/portal/{page}"}

def call(qid, page, **p):
    body = urllib.parse.urlencode({"qid": qid, **p}).encode()
    req  = urllib.request.Request(API, data=body, headers=hdr(page))
    raw  = urllib.request.urlopen(req, timeout=100).read().decode("utf-8", "replace")
    time.sleep(2.5)                       # 저속 유지
    if not raw.strip(): return None
    try: return json.loads(raw).get("list") or []
    except json.JSONDecodeError: return None

def alive():
    try:
        urllib.request.urlopen(urllib.request.Request(
            "https://datalab.visitkorea.or.kr/datalab/portal/main/getMainForm.do",
            headers={"User-Agent": "Mozilla/5.0"}), timeout=25).read(500)
        return True
    except Exception:
        return False

# 접속 확인 (호출 전 이미 확인됨)
if not alive():
    log("접속 불가. 종료."); raise SystemExit(1)
log("접속 확인 — 수집 시작")

SIDO = {"11":"서울","26":"부산","27":"대구","28":"인천","29":"광주","30":"대전","31":"울산",
        "36":"세종","41":"경기","43":"충북","44":"충남","46":"전남","47":"경북","48":"경남",
        "50":"제주","51":"강원","52":"전북"}
BASE = dict(BASE_YM1="201801", BASE_YM2="202608", srchAreaDate="1", tabDiv="1",
            touDivCd="2", sggIntgYnFlag="N", dispYn="Y", yearOverGlobal="N",
            sggIntgYnFlag2="N", BASE_YR="2018", P_BASE_YM1="201701",
            P_BASE_YM2="202508", P_GAP="12")

def save(name, rows):
    if not rows: return 0
    fields = []
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    p = OUT / f"{name}.csv"
    with p.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    log(f"  저장 {p.name}  rows={len(rows)}")
    return len(rows)

# ── 1) 관광지 검색순위 Top100 : 파라미터 조합 탐색
log("[1] 검색순위 Top100 파라미터 탐색")
found = None
for qid in ["BDT_03_04_002", "BDT_03_04_003"]:
    for sgg in ["", "11", "11110"]:
        for sad, y1, y2 in [("1","202501","202512"), ("4","2025","2025"), ("1","202508","202607")]:
            for tab in ["1","2","3"]:
                try:
                    r = call(qid, "bda/getTourVisitCnt.do", **{**BASE, "SGG_CD": sgg,
                             "BASE_YM1": y1, "BASE_YM2": y2, "srchAreaDate": sad, "tabDiv": tab})
                except Exception as e:
                    log(f"  {qid} sgg={sgg} sad={sad} tab={tab} ERR {e}"); continue
                if r:
                    log(f"  ★ {qid} 작동: SGG_CD={sgg} srchAreaDate={sad} tabDiv={tab} rows={len(r)}")
                    found = (qid, sgg, sad, y1, y2, tab); break
            if found: break
        if found: break
    if found: break

if found:
    qid, _, sad, y1, y2, tab = found
    allrows = []
    for cd, nm in [("", "전국")] + list(SIDO.items()):
        try:
            r = call(qid, "bda/getTourVisitCnt.do", **{**BASE, "SGG_CD": cd,
                     "BASE_YM1": y1, "BASE_YM2": y2, "srchAreaDate": sad, "tabDiv": tab})
        except Exception as e:
            log(f"  {nm} ERR {e}"); continue
        for x in (r or []):
            if isinstance(x, dict): allrows.append({"지역": nm, **x})
        log(f"  {nm}: {len(r or [])}행")
    save(f"관광지검색순위Top100_{qid}", allrows)
else:
    log("  검색순위 Top100 활성화 실패 — 모든 조합에서 빈 응답")

# ── 2) 비교 화면 qid (빈 배열 반환 원인 재확인)
log("[2] 비교 화면 qid 재시도")
for qid, page in [("BDT_01_03_001","bda/getByRegnAna.do"), ("BDT_01_03_003","bda/getByRegnAna.do"),
                  ("BDT_01_03_004_1","bda/getByRegnAna.do"), ("BDT_02_03_001","bda/getByRegnCmpr.do"),
                  ("BDT_02_03_001_1","bda/getByRegnCmpr.do"), ("BDT_SKT_FRG_02_01_001","bda/getByRegnAna.do")]:
    for extra in [{"SGG_CD":"11110"}, {"SGG_CD":"11110,26290"}, {"SGG_CD":"11110","CMPR_SGG_CD":"26290"},
                  {"SGG_CD":"11110","areaCds":"11110,26290"}]:
        try:
            r = call(qid, page, **{**BASE, **extra})
        except Exception as e:
            log(f"  {qid} ERR {e}"); continue
        if r:
            log(f"  ★ {qid} 작동: {extra} rows={len(r)}")
            save(f"비교화면_{qid}", [x for x in r if isinstance(x, dict)]); break
    else:
        log(f"  {qid}: 모든 조합 실패")

# ── 3) LN 잔여 3종 (271개 시군구)
log("[3] LN 잔여 지표 (검색Top100 2종 + 요일별)")
codes = json.loads((ROOT/"data"/"region_codes.json").read_text(encoding="utf-8"))
regions = [(s["cd"], f'{v["name"]} {s["nm"]}') for v in codes.values() for s in v["sgg"]]
for qid, label in [("LN_03_01_037","관광지검색Top100"), ("LN_03_01_038","관광지검색Top100_외국인"),
                   ("LN_02_01_005","요일별_방문")]:
    rows, fail = [], 0
    for cd, nm in regions:
        try:
            r = call(qid, "loc/getAreaDataForm.do", **{**BASE, "SGG_CD": cd, "SGG_NM": nm})
        except Exception:
            fail += 1; continue
        for x in (r or []):
            if isinstance(x, dict): rows.append({"SGG_CD": cd, "SGG_NM": nm, **x})
    log(f"  {label} {qid}: rows={len(rows)} fail={fail}")
    save(f"{label}_{qid}", rows)

log("전체 완료")
