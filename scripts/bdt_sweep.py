#!/usr/bin/env python3
"""미활성 qid 파라미터 스윕."""
import sys, json, itertools, pathlib
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/Users/koyunseo/한국관광데이터분석/scripts")
from bdt_common import fetch

OUT = pathlib.Path("/private/tmp/claude-501/-Users-koyunseo----------/7823f88e-cc15-4bae-8afa-05a6daf1e579/scratchpad")

SKT = ["BDT_SKT_FRG_01_01_001","BDT_SKT_FRG_01_01_002","BDT_SKT_FRG_01_01_003","BDT_SKT_FRG_02_01_001"]
MISC = """BDT_01_01_005_1 BDT_01_01_004_3_5 BDT_01_01_004_3_6 BDT_01_01_004_3_7
BDT_01_01_005_4 BDT_01_01_004_4 BDT_01_01_005_12 BDT_01_01_004_12
BDT_01_01_0012 BDT_01_01_001_12 BDT_01_01_0022 BDT_01_01_004_3_12
BDT_01_01_004_32 BDT_01_01_004_3_13 BDT_01_01_004_3_14 BDT_01_01_0032_1
BDT_01_01_0032 BDT_01_01_0032_2 BDT_01_01_0032_4 BDT_01_01_005_42
BDT_01_01_004_42 BDT_01_01_001_42 BDT_01_01_003_42 BDT_01_01_005_22""".split()
REGN = ["BDT_01_03_001","BDT_01_03_003","BDT_01_03_001_1","BDT_01_03_003_1","BDT_01_03_004_1"]

def combos(qid, page):
    out = []
    tds = [1,2,3,4]
    tous = [1,2,3] if "FRG" in qid else [1,2]
    for tab, tou in itertools.product(tds, tous):
        out.append(dict(page=page, tabDiv=tab, touDivCd=tou, srchAreaDate=1,
                        BASE_YM1="202408", BASE_YM2="202507", SGG_CD=""))
    for tab, tou in itertools.product([1,2], tous):
        out.append(dict(page=page, tabDiv=tab, touDivCd=tou, srchAreaDate=4,
                        BASE_YM1="2023", BASE_YM2="2024", SGG_CD=""))
        out.append(dict(page=page, tabDiv=tab, touDivCd=tou, srchAreaDate=1,
                        BASE_YM1="202408", BASE_YM2="202507", SGG_CD="11110"))
    return out

TASKS = []
for q in SKT + MISC:
    for c in combos(q, "getMetcoAna"):
        TASKS.append((q, c))
for q in REGN:
    for c in combos(q, "getByRegnAna"):
        TASKS.append((q, c))

hits = {}
def run(t):
    qid, c = t
    p = dict(c); page = p.pop("page")
    st, rows = fetch(qid, page=page, timeout=120, **p)
    return qid, page, p, st, len(rows), (list(rows[0].keys()) if rows and isinstance(rows[0], dict) else [])

print(f"total {len(TASKS)} requests", flush=True)
with ThreadPoolExecutor(max_workers=3) as ex:
    for qid, page, p, st, n, keys in ex.map(run, TASKS):
        if st == "ok" and n > 0:
            print(f"HIT {qid} page={page} {p} rows={n} {keys[:8]}", flush=True)
            hits.setdefault(qid, []).append({"page": page, **p, "rows": n, "keys": keys})
        elif st.startswith("err") or st == "nonjson" or st.startswith("nolist"):
            print(f"    {qid} {p.get('tabDiv')}/{p.get('touDivCd')}/{p.get('srchAreaDate')} -> {st}", flush=True)
(OUT / "sweep_hits.json").write_text(json.dumps(hits, ensure_ascii=False, indent=1), encoding="utf-8")
print("HITQIDS", sorted(hits), flush=True)
print("DONE", flush=True)
