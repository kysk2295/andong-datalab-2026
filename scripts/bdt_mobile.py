#!/usr/bin/env python3
"""한국관광 데이터랩 「빅데이터 > 이동통신」 전수 수집기 (stdlib only).

사용:
  python3 bdt_mobile.py national   # 전국(SGG_CD='') qid
  python3 bdt_mobile.py big        # BDT_01_01_006 연도별 스트리밍
  python3 bdt_mobile.py sgg        # 시군구 필수 qid (전 시군구 순회)
"""
import sys, os, csv, json, codecs, time, pathlib, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path("/Users/koyunseo/한국관광데이터분석")
OUT = ROOT / "data/bdt/이동통신"
OUT.mkdir(parents=True, exist_ok=True)
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
YM1, YM2 = "201801", "202608"

def _hdr(page):
    return {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0",
            "Referer": f"https://datalab.visitkorea.or.kr/datalab/portal/bda/{page}.do"}

def _body(qid, **p):
    b = {"qid": qid, "SGG_CD": "", "BASE_YM1": YM1, "BASE_YM2": YM2, "srchAreaDate": "1",
         "tabDiv": "1", "touDivCd": "2", "sggIntgYnFlag": "N"}
    b.update({k: str(v) for k, v in p.items()})
    return urllib.parse.urlencode(b).encode()

def open_resp(qid, page="getMetcoAna", timeout=120, **p):
    return urllib.request.urlopen(
        urllib.request.Request(API, data=_body(qid, **p), headers=_hdr(page)), timeout=timeout)

def iter_rows(qid, page="getMetcoAna", timeout=120, **p):
    """응답을 스트리밍하며 list 원소를 하나씩 yield (대용량 대응)."""
    resp = open_resp(qid, page=page, timeout=timeout, **p)
    dec = codecs.getincrementaldecoder("utf-8")("replace")
    jd = json.JSONDecoder()
    buf, started, idx = "", False, 0
    while True:
        chunk = resp.read(1 << 20)
        if chunk:
            buf += dec.decode(chunk)
        elif not chunk:
            buf += dec.decode(b"", True)
        if not started:
            k = buf.find('"list"')
            if k < 0:
                if not chunk: return
                continue
            k = buf.find("[", k)
            if k < 0:
                if not chunk: return
                continue
            buf, idx, started = buf[k + 1:], 0, True
        while True:
            while idx < len(buf) and buf[idx] in " \t\r\n,":
                idx += 1
            if idx < len(buf) and buf[idx] == "]":
                return
            if idx >= len(buf):
                break
            try:
                obj, end = jd.raw_decode(buf, idx)
            except ValueError:
                break
            yield obj
            idx = end
        buf, idx = buf[idx:], 0
        if not chunk:
            return

def fetch_rows(qid, retries=2, **kw):
    for a in range(retries + 1):
        try:
            return list(iter_rows(qid, **kw))
        except Exception as e:
            if a == retries: raise
            time.sleep(2 * (a + 1))

def write_csv(path, rows, cols=None):
    if not rows: return 0
    cols = cols or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow(r)
    return len(rows)

LOG = OUT / "_수집로그.jsonl"
def log(**kw):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")
    print(json.dumps(kw, ensure_ascii=False), flush=True)

# ---------------------------------------------------------------- 전국 qid
NATIONAL = [
    # (qid, 설명, touDivCd별로 나눠야 하는가)
    ("BDT_01_01_001",     "광역시도별_방문자수",              True),
    ("BDT_01_01_001_1",   "출발지역별_방문자수_상세",          True),
    ("BDT_01_01_001_11",  "광역시도별_방문자수_비중",          True),
    ("BDT_01_01_001_4",   "광역시도별_방문자수_월별시계열",     False),
    ("BDT_01_01_002",     "출발지역별_방문자수",              True),
    ("BDT_01_01_002_036", "출발지역별_방문자수_시군구",        True),
    ("BDT_01_01_003_4",   "시도별_방문자유형_월별시계열",       False),
    ("BDT_01_01_004_1",   "시군구별_방문자수",                True),
    ("BDT_01_01_006_1",   "숙박일수별_관광객_숙박자_체류시간",   False),
]
TOU = {"1": "현지인a", "2": "외지인b"}

def run_national():
    jobs = []
    for qid, desc, split in NATIONAL:
        if split:
            for t in ("1", "2"):
                jobs.append((qid, desc, t))
        else:
            jobs.append((qid, desc, None))
    def one(j):
        qid, desc, t = j
        kw = {"BASE_YM1": YM1, "BASE_YM2": YM2, "timeout": 300}
        name = f"{desc}_{qid}"
        if t: kw["touDivCd"] = t; name += f"_{TOU[t]}"
        try:
            rows = fetch_rows(qid, **kw)
        except Exception as e:
            return dict(qid=qid, desc=desc, tou=t, status="ERROR", err=str(e)[:120])
        p = OUT / f"{name}.csv"
        n = write_csv(p, rows)
        return dict(qid=qid, desc=desc, tou=t, status="ok" if n else "empty",
                    rows=n, file=p.name, params=f"SGG_CD=''&BASE_YM1={YM1}&BASE_YM2={YM2}"
                    + (f"&touDivCd={t}" if t else ""))
    with ThreadPoolExecutor(3) as ex:
        for r in ex.map(one, jobs): log(**r)

# ------------------------------------------------ BDT_01_01_006 (대용량)
def run_big():
    qid, desc = "BDT_01_01_006", "방문자수_성별연령요일시간대_교차표"
    years = [(f"{y}01", f"{y}12") for y in range(2018, 2026)] + [("202601", "202608")]
    cols = ["R:기초단체", "R:광역단체", "R:기준연월", "C:방문자유형별", "C:성별",
            "C:연령별", "C:요일", "C:시간대", "V:방문자 수"]
    for a, b in years:
        p = OUT / f"{desc}_{qid}_{a[:4]}.csv"
        if p.exists() and p.stat().st_size > 10_000_000:
            log(qid=qid, year=a[:4], status="skip(exists)", file=p.name); continue
        t0, n, mode, errs = time.time(), 0, "year", []
        def stream_into(w, y1, y2):
            c = 0
            for row in iter_rows(qid, BASE_YM1=y1, BASE_YM2=y2, timeout=1200):
                w.writerow(row); c += 1
            return c
        ok = False
        for attempt in range(3):
            n = 0
            try:
                with open(p, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
                    w.writeheader()
                    n = stream_into(w, a, b)
                if n: ok = True; break
            except Exception as e:
                errs.append(str(e)[:100])
            time.sleep(20 * (attempt + 1))
        if not ok:
            # 연 단위 실패 -> 월 단위로 쪼개 이어붙이기
            mode, n = "month-fallback", 0
            months = [f"{a[:4]}{m:02d}" for m in range(int(a[4:]), int(b[4:]) + 1)]
            with open(p, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                for mm in months:
                    for attempt in range(3):
                        try:
                            n += stream_into(w, mm, mm); break
                        except Exception as e:
                            errs.append(f"{mm}:{str(e)[:60]}")
                            time.sleep(20 * (attempt + 1))
                    else:
                        errs.append(f"{mm}:GAVE_UP")
        log(qid=qid, desc=desc, year=a[:4], status="ok" if n else "empty", rows=n,
            file=p.name, secs=round(time.time() - t0), mode=mode, errs=errs[:4],
            params=f"SGG_CD=''&BASE_YM1={a}&BASE_YM2={b}&touDivCd=2")

# ------------------------------------------------------- 시군구 필수 qid
SGG_QIDS = [
    ("BDT_SKT_FRG_01_01_001", "외국인방문자_시도별_SKT",        False),
    ("BDT_SKT_FRG_01_01_002", "외국인방문자_출발지역별_SKT",     False),
    ("BDT_SKT_FRG_01_01_003", "외국인방문자_월별시계열_SKT",     False),
    ("BDT_01_01_005_1",       "시군구_주변지역_방문자수",        True),
    ("BDT_01_01_004_3_5",     "시군구_출발지역별_방문자수_상세",  True),
    ("BDT_01_01_004_3_6",     "시군구_출발지역별_방문자수_집계",  True),
    ("BDT_01_01_004_3_7",     "시군구_출발광역시도별_방문자수",   True),
    ("BDT_01_01_004_4",       "시군구_방문자수_월별시계열",       False),
]

def sgg_list():
    d = json.loads((ROOT / "data/region_codes.json").read_text(encoding="utf-8"))
    out = []
    for sido, v in d.items():
        for s in v["sgg"]:
            out.append((sido, v["name"], s["cd"], s["nm"]))
    return out

def run_sgg():
    regions = sgg_list()
    print(f"시군구 {len(regions)}개", flush=True)
    for qid, desc, split in SGG_QIDS:
        for t in (("1", "2") if split else (None,)):
            name = f"{desc}_{qid}" + (f"_{TOU[t]}" if t else "")
            p = OUT / f"{name}.csv"
            if p.exists() and p.stat().st_size > 1000:
                log(qid=qid, status="skip(exists)", file=p.name); continue
            def one(reg):
                sido_cd, sido_nm, cd, nm = reg
                kw = dict(SGG_CD=cd, BASE_YM1=YM1, BASE_YM2=YM2, timeout=600)
                if t: kw["touDivCd"] = t
                try:
                    rows = fetch_rows(qid, **kw)
                except Exception as e:
                    return (reg, None, str(e)[:80])
                for r in rows:
                    r["_조회_시도"] = sido_nm; r["_조회_시군구"] = nm; r["_조회_SGG_CD"] = cd
                return (reg, rows, None)
            allrows, errs, t0 = [], [], time.time()
            with ThreadPoolExecutor(int(os.environ.get("SGG_WORKERS","3"))) as ex:
                for reg, rows, err in ex.map(one, regions):
                    if err: errs.append(f"{reg[3]}:{err}")
                    else: allrows.extend(rows)
            cols = (["_조회_시도", "_조회_시군구", "_조회_SGG_CD"]
                    + [k for k in allrows[0].keys() if not k.startswith("_조회_")]) if allrows else None
            n = write_csv(p, allrows, cols)
            log(qid=qid, desc=desc, tou=t, status="ok" if n else "empty", rows=n,
                file=p.name, regions=len(regions), errors=len(errs), secs=round(time.time() - t0),
                params=f"SGG_CD=<시군구 250개 순회>&BASE_YM1={YM1}&BASE_YM2={YM2}"
                + (f"&touDivCd={t}" if t else ""),
                err_sample=errs[:3])

if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "national"
    {"national": run_national, "big": run_big, "sgg": run_sgg}[m]()
    print("DONE " + m, flush=True)
