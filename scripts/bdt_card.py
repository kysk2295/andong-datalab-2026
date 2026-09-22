#!/usr/bin/env python3
"""한국관광 데이터랩 「빅데이터 > 신용카드」 전수 수집기.

== 2026-09-09 검증으로 확정된 사실 ==

1) 0바이트(empty) 응답의 의미가 두 가지다.
   - 존재하지 않는 qid          -> 항상 0바이트 (예: 'TOTALLY_FAKE_QID_XYZ' 도 0바이트)
   - 서버 레이트리밋에 걸린 상태 -> 유효한 qid 도 0바이트
   따라서 0바이트를 "파라미터 불일치"로 해석하면 안 된다. 반드시 시간을 두고 재확인해야 한다.
   "ok + rows=0" 은 템플릿이 실재하나 그 파라미터로 데이터가 없다는 뜻으로, empty 와 구분된다.

2) tabDiv 는 신용카드 계열에서 결과에 아무 영향이 없다 (1/2/3/4 응답 동일).

3) touDivCd 는 사실상 이진 플래그다. 1 이면 A집합, 1이 아니면(2/3/4) B집합.
   그나마도 _3x 계열에서만 값이 달라지고 _1x/_2x 계열은 touDivCd 와 무관하게 동일하다.

4) 소비주체는 qid 접미사의 앞자리로 인코딩된다 (BDT_02_01_<블록>_<주체><축>).
   _1x = 내국인   (2025-12 전국 관광총소비 18,348,644,781)
   _2x = 외국인   (2025-12 전국 관광총소비  1,484,398,101)
        -> 의료관광(61)/카지노(51) 업종이 이 계열에만 존재한다. 외국인 데이터라는 결정적 근거.
   _3x = 내국인 중 외지인(관광객) 부분집합 (touDivCd=1 -> 13,715,471,769 / !=1 -> 15,775,367,781)
   _5  = 구(舊) 4자리 업종코드 레거시 템플릿. 값이 전부 0 이라 실사용 불가.

5) 기간 제한 없음. BASE_YM1=201801 & BASE_YM2=202608 를 한 번에 조회하면 104개월이 전부 온다.

6) 단위: CNSM_AMT / SPPY_CNSM_AMT 는 천원(1,000원). docs 참조.

== 수집 실패로 확정된 것 ==
BDT_02_01_001_41/_42/_43, BDT_02_01_002_41/_42/_43, BDT_02_01_003_41/_42,
BDT_02_03_001* 등은 서버에 존재하지 않는 qid 다 (외국인/국적별 별도 계열은 없음).
외국인 지출액은 위 4)의 _2x 계열로 제공된다.
"""
import csv
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from bdt_common import fetch  # noqa: E402

ROOT = pathlib.Path("/Users/koyunseo/한국관광데이터분석")
OUT = ROOT / "data" / "bdt" / "신용카드"
PAGE = "getByLocgoCnsmAmt"

YM_START, YM_END = "201801", "202608"
DELAY = 6.0          # 공공 서버 배려: 요청 간 간격(초). 동시 요청은 쓰지 않는다(순차).
COOLDOWN = 420       # 레이트리밋 감지 시 대기(초)

# qid -> (설명, touDivCd, 연도분할여부)
DATASETS = [
    # ---- 전국 요약 시계열 (BDT_02_01_001_x5) ----
    ("BDT_02_01_001_15", "전국_업종중분류_월별_내국인지출액",            "2", False),
    ("BDT_02_01_001_25", "전국_업종중분류_월별_외국인지출액",            "2", False),
    ("BDT_02_01_001_35", "전국_업종중분류_월별_외지인지출액_touDiv2",    "2", False),
    ("BDT_02_01_001_35", "전국_업종중분류_월별_외지인지출액_touDiv1",    "1", False),
    # ---- 시도별 (BDT_02_01_002_*) ----
    ("BDT_02_01_002_35_1", "시도별_업종중분류_월별_외지인지출액_대용량",  "2", True),
    ("BDT_02_01_002_35",   "시도별_업종중분류_월별_외지인지출액",        "2", True),
    ("BDT_02_01_002_25",   "시도별_업종중분류_월별_외국인지출액",        "2", True),
    # ---- 시군구별 (BDT_02_01_003_*) ----
    ("BDT_02_01_003_35", "시군구별_업종중분류_월별_외지인지출액",        "2", True),
    ("BDT_02_01_003_25", "시군구별_업종중분류_월별_외국인지출액",        "2", True),
    # ---- 지역별 요약 블록 (AREA_NM / 증감률) ----
    ("BDT_02_01_001_1",  "지역별_관광지출액_내국인",                    "2", False),
    ("BDT_02_01_001_21", "지역별_관광지출액_외국인",                    "2", False),
    ("BDT_02_01_001_31", "지역별_관광지출액_외지인",                    "2", False),
    # ---- 출발지역 블록 (TOU_NUM 스키마: 소비액이 아니라 방문객수) ----
    ("BDT_02_01_001_2",  "출발지역별_업종블록_내국인",                  "2", False),
    ("BDT_02_01_001_22", "출발지역별_업종블록_외국인",                  "2", False),
    ("BDT_02_01_001_32", "출발지역별_업종블록_외지인",                  "2", False),
    ("BDT_02_01_001_3",  "출발지역별_시군구블록_내국인",                "2", False),
    ("BDT_02_01_001_23", "출발지역별_시군구블록_외국인",                "2", False),
    ("BDT_02_01_001_33", "출발지역별_시군구블록_외지인",                "2", False),
]


def write_csv(path, rows):
    if not rows:
        return 0
    cols, seen = [], set()
    for r in rows:
        for k in r:
            if k not in seen:
                seen.add(k)
                cols.append(k)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def get(qid, tou, ym1, ym2):
    """0바이트가 오면 레이트리밋일 수 있으므로 쿨다운 후 1회 재확인한다."""
    s, r = fetch(qid, page=PAGE, BASE_YM1=ym1, BASE_YM2=ym2, touDivCd=tou)
    if s == "empty":
        print(f"    empty -> 쿨다운 {COOLDOWN}s 후 재확인", flush=True)
        time.sleep(COOLDOWN)
        s, r = fetch(qid, page=PAGE, BASE_YM1=ym1, BASE_YM2=ym2, touDivCd=tou)
    return s, r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = []
    for qid, desc, tou, yearly in DATASETS:
        fn = f"{desc}_{qid}.csv"
        print(f"[{qid}] {desc} touDivCd={tou} yearly={yearly}", flush=True)
        rows, statuses = [], []
        if yearly:
            for y in range(2018, 2027):
                a, b = f"{y}01", f"{y}12" if y < 2026 else "202608"
                s, r = get(qid, tou, a, b)
                statuses.append(f"{y}:{s}:{len(r or [])}")
                print(f"    {y} -> {s} rows={len(r or [])}", flush=True)
                if r:
                    rows.extend(r)
                time.sleep(DELAY)
        else:
            s, r = get(qid, tou, YM_START, YM_END)
            statuses.append(f"{s}:{len(r or [])}")
            print(f"    full -> {s} rows={len(r or [])}", flush=True)
            rows = r or []
            time.sleep(DELAY)

        n = write_csv(OUT / fn, rows) if rows else 0
        yms = sorted({str(x.get("BASE_DATE")) for x in rows if x.get("BASE_DATE")})
        rec = dict(qid=qid, desc=desc, touDivCd=tou, rows=n, file=fn if n else "",
                   period=f"{yms[0]}~{yms[-1]}" if yms else "", detail=statuses)
        meta.append(rec)
        print(f"    => {n} rows -> {fn}\n", flush=True)
        (OUT / "_수집메타.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DONE", sum(m["rows"] for m in meta))


if __name__ == "__main__":
    main()
