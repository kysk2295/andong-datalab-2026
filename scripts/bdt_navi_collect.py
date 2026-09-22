"""내비게이션 계열 유효 qid 전수 수집."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdt_navi import fetch, save_csv, pmap, OUT

YEARS = list(range(2018, 2027))
FULL = ("201801", "202608")

# (qid, 설명, page, extra params)
JOBS = [
    ("BDT_03_01_003_1", "시군구별_검색건수", "getDomInqCnt", {}),
    ("BDT_03_01_001_1", "시도별_검색건수", "getDomInqCnt", {}),
    ("BDT_03_01_001_2", "출발지유형별_검색건수", "getDomInqCnt", {}),
    ("BDT_03_01_001_3", "출발지시군구별_검색건수", "getDomInqCnt", {}),
    ("BDT_03_01_002_3", "출발지x목적지중분류_검색건수", "getDomInqCnt", {}),
    ("BDT_03_01_001_4", "시도x중분류_월별시계열", "getDomInqCnt", {}),
]

def run_full():
    out = []
    for qid, desc, page, extra in JOBS:
        st, rows, body = fetch(qid, page=page, BASE_YM1=FULL[0], BASE_YM2=FULL[1], **extra)
        fn = f"{desc}_전체기간_{qid}.csv"
        n = save_csv(rows, os.path.join(OUT, fn)) if st == "ok" else 0
        out.append((qid, desc, st, n, fn, f"{FULL[0]}~{FULL[1]}", body))
        print(qid, desc, st, n, flush=True)
    return out

def run_yearly():
    tasks = [(q, d, p, e, y) for q, d, p, e in JOBS for y in YEARS]
    def one(t):
        q, d, p, e, y = t
        ym1, ym2 = f"{y}01", (f"{y}08" if y == 2026 else f"{y}12")
        st, rows, _ = fetch(q, page=p, BASE_YM1=ym1, BASE_YM2=ym2, **e)
        for r in rows:
            r["_YEAR"] = y
        return (q, d, y, st, rows)
    res = pmap(one, tasks, workers=1)
    out = []
    for q, d, p, e in JOBS:
        allrows, oks, fails = [], [], []
        for rq, rd, y, st, rows in res:
            if rq != q: continue
            (oks if st == "ok" else fails).append(y)
            allrows.extend(rows)
        fn = f"{d}_연도별_{q}.csv"
        n = save_csv(allrows, os.path.join(OUT, fn))
        out.append((q, d, "ok" if oks else "fail", n, fn,
                    f"{min(oks)}~{max(oks)}" if oks else "-", fails))
        print(q, d, "yearly rows", n, "fail", fails, flush=True)
    return out

if __name__ == "__main__":
    r1 = run_full()
    r2 = run_yearly()
    json.dump({"full": [list(map(str, x)) for x in r1],
               "yearly": [list(map(str, x)) for x in r2]},
              open(os.path.join(OUT, "_collect_log.json"), "w"), ensure_ascii=False, indent=1)
