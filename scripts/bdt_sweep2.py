#!/usr/bin/env python3
import sys, json, itertools, pathlib
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/Users/koyunseo/한국관광데이터분석/scripts")
from bdt_common import fetch
OUT = pathlib.Path("/private/tmp/claude-501/-Users-koyunseo----------/7823f88e-cc15-4bae-8afa-05a6daf1e579/scratchpad")

MISS = """BDT_SKT_FRG_02_01_001 BDT_01_01_005_4 BDT_01_01_005_12 BDT_01_01_004_12
BDT_01_01_0012 BDT_01_01_001_12 BDT_01_01_0022 BDT_01_01_004_3_12
BDT_01_01_004_32 BDT_01_01_004_3_13 BDT_01_01_004_3_14 BDT_01_01_0032_1
BDT_01_01_0032 BDT_01_01_0032_2 BDT_01_01_0032_4 BDT_01_01_005_42
BDT_01_01_004_42 BDT_01_01_001_42 BDT_01_01_003_42 BDT_01_01_005_22""".split()
REGN = ["BDT_01_03_001","BDT_01_03_003","BDT_01_03_001_1","BDT_01_03_003_1","BDT_01_03_004_1"]

T=[]
def add(q,page,**p): T.append((q,page,p))
for q in MISS:
    for sgg in ["11110","11","26110",""]:
        add(q,"getMetcoAna",SGG_CD=sgg,srchAreaDate=1,BASE_YM1="202408",BASE_YM2="202507",tabDiv=1,touDivCd=1)
        add(q,"getMetcoAna",SGG_CD=sgg,srchAreaDate=4,BASE_YM1="2023",BASE_YM2="2024",tabDiv=1,touDivCd=1)
        add(q,"getMetcoAna",SGG_CD=sgg,srchAreaDate=5,BASE_YM1="20250801",BASE_YM2="20250831",tabDiv=1,touDivCd=1)
    add(q,"getMetcoAna",SGG_CD="11110",srchAreaDate=1,BASE_YM1="202408",BASE_YM2="202507",tabDiv=3,touDivCd=2)
for q in REGN:
    for page in ["getByRegnAna","getMetcoAna"]:
        for sgg in ["11110","11",""]:
            for extra in [{}, {"SGG_CD2":"26110"}, {"CMPR_SGG_CD":"26110"}, {"SGG_CD_LIST":"11110,26110"}]:
                add(q,page,SGG_CD=sgg,srchAreaDate=1,BASE_YM1="202408",BASE_YM2="202507",tabDiv=1,touDivCd=1,**extra)

def run(t):
    q,page,p = t
    st, rows = fetch(q, page=page, **p)
    return q,page,p,st,rows
print(f"total {len(T)}", flush=True)
hits={}
with ThreadPoolExecutor(max_workers=3) as ex:
    for q,page,p,st,rows in ex.map(run,T):
        if st=="ok" and rows:
            k=list(rows[0].keys()) if isinstance(rows[0],dict) else []
            print(f"HIT {q} page={page} {p} rows={len(rows)} {k[:8]}",flush=True)
            hits.setdefault(q,[]).append({"page":page,**p,"rows":len(rows),"keys":k})
        elif not st.startswith(("empty","ok")):
            print(f"    {q} {page} {st}",flush=True)
(OUT/"sweep2_hits.json").write_text(json.dumps(hits,ensure_ascii=False,indent=1),encoding="utf-8")
print("HITQIDS",sorted(hits),flush=True); print("DONE",flush=True)
