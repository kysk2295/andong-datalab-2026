#!/usr/bin/env python3
"""빅데이터 메뉴 BDT_* qid 전수 프로브 — 전국 단위로 어떤 데이터가 나오는지 확인."""
import json, urllib.parse, urllib.request, pathlib, sys
from concurrent.futures import ThreadPoolExecutor

SP = pathlib.Path("/private/tmp/claude-501/-Users-koyunseo----------/7823f88e-cc15-4bae-8afa-05a6daf1e579/scratchpad")
API = "https://datalab.visitkorea.or.kr/visualize/getTempleteData.do"
QIDS = json.loads((SP / "bdt_qids.json").read_text(encoding="utf-8"))

def hdr(page):
    return {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest", "User-Agent": "Mozilla/5.0",
            "Referer": f"https://datalab.visitkorea.or.kr/datalab/portal/bda/{page}.do"}

BASE = dict(SGG_CD="", BASE_YM1="202508", BASE_YM2="202607", srchAreaDate="1",
            tabDiv="1", touDivCd="2", sggIntgYnFlag="N")

def probe(args):
    page, qid = args
    body = urllib.parse.urlencode({**BASE, "qid": qid}).encode()
    try:
        raw = urllib.request.urlopen(
            urllib.request.Request(API, data=body, headers=hdr(page)), timeout=90
        ).read().decode("utf-8", "replace")
    except Exception as e:
        return f"{page:20} {qid:26} ERR {e}"
    if not raw.strip():
        return f"{page:20} {qid:26} --0bytes"
    try:
        L = json.loads(raw).get("list") or []
    except Exception:
        return f"{page:20} {qid:26} nonjson"
    keys = list(L[0].keys())[:9] if L and isinstance(L[0], dict) else []
    return f"{page:20} {qid:26} rows={len(L):<5} {keys}"

tasks = [(p, q) for p, qs in QIDS.items() for q in qs]
with ThreadPoolExecutor(max_workers=6) as ex:
    for line in ex.map(probe, tasks):
        print(line, flush=True)
print("DONE", flush=True)
