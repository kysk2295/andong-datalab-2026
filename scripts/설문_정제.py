"""안동관광 온라인 설문(구글폼 응답 시트 PDF) → 정제 CSV.

PDF는 긴 셀 글자가 옆 칸과 겹쳐 그려져 텍스트 추출이 섞인다.
글자를 그리는 순서(스트림 순서)는 셀 단위라, 그 순서대로 이어 붙이고
x 좌표가 뒤로 가거나 3pt 넘게 벌어지면 새 셀로 끊은 뒤 시작 x로 열을 정한다.

실행: .venv_pdf/bin/python scripts/설문_정제.py [PDF 경로]
"""
import sys
import re
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/설문/안동관광온라인설문조사_응답_20260924.pdf"
OUT = ROOT / "data/설문/안동관광온라인설문_응답_정제.csv"

TS = re.compile(r"\d{4}\. \d{1,2}\. \d{1,2} 오[전후] \d{1,2}:\d{2}:\d{2}")

# 열 왼쪽 경계(pt, 두 쪽 동일)와 짧은 열 이름
BOUNDS = [50.2, 79.7, 131.4, 172.6, 219.4, 277.9, 336.4, 394.9, 440.9, 499.4, 557.9, 616.4, 674.8, 733.3]
COLS = [
    "응답시각",
    "Q1_3년내_방문",          # 최근 3년 이내 여행·관광 목적으로 안동 방문
    "Q2_주_이동수단",          # 안동 여행 때 주로 이용한 이동 수단
    "Q3_대중교통_불편",        # 시내버스 이용 시 버스가 일찍 끝나거나 불편한 점
    "Q4_이동불편_포기한곳",    # 이동이 불편해 가고 싶었지만 포기한 곳(중복)
    "Q5_원도심_식사후_이동",   # 원도심 식사 뒤 주로 어디로 이동
    "Q6_영수증_체험쿠폰_의향", # 원도심 식당 영수증 인증 → 체험 할인 쿠폰이면 체험 이용
    "Q7_가장좋은_혜택",        # 체험활동을 바로 이용하게 만드는 가장 좋은 혜택
    "Q8_야간택시셔틀_의향",    # 18:30~21:00 원도심→월영교 야간 할인 택시/셔틀 이용
    "Q9_월영교_밤_식당편의",   # 밤 20시 이후 월영교 주변 식당·편의시설 충분했나
    "Q10_야간팝업포차_의향",   # 21~23시 월영교 야간 팝업 포차/푸드트럭 방문
    "Q11_유료체험_망설임",     # 탈춤축제·체험장 유료 공연/체험이 망설여지는 이유
    "Q12_영수증_축제혜택_의향", # 식당 영수증 → 축제 우선 입장권/할인 쿠폰이면 축제+식사
    "Q13_귀가_교통_시간대",    # 귀가 기차/버스 시간대
]


def col_of(x):
    i = max(j for j, b in enumerate(BOUNDS) if x >= b - 0.5)
    return i


def parse_page(page):
    # 한글·숫자 글꼴의 top이 0.3pt쯤 달라 반올림하면 한 줄이 쪼개진다 → 2pt 안이면 같은 줄
    tops = sorted({c["top"] for c in page.chars})
    anchor, key = {}, None
    for t in tops:
        if key is None or t - key > 2:
            key = t
        anchor[t] = key
    rows = {}
    for c in page.chars:  # 스트림 순서 유지
        rows.setdefault(anchor[c["top"]], []).append(c)
    out = []
    for top in sorted(rows):
        chars = rows[top]
        if top < 58:  # 머리 줄
            continue
        cells, cur, start, prev = {}, "", None, None
        for c in chars:  # 스트림 순서 유지
            if prev is None or c["x0"] < prev - 0.5 or c["x0"] - prev > 3:
                if cur:
                    cells[col_of(start)] = cells.get(col_of(start), "") + cur
                cur, start = "", c["x0"]
            cur += c["text"]
            prev = c["x1"]
        if cur:
            cells[col_of(start)] = cells.get(col_of(start), "") + cur
        # 응답시각은 오른쪽 정렬이라 긴 값은 옆 칸(Q1)과 붙어 한 셀로 읽힌다 → 형식으로 잘라 Q1에 돌려준다
        m = TS.match(cells.get(0, ""))
        if m:
            rest = cells[0][m.end():]
            cells[0] = m.group(0)
            if rest:
                cells[1] = rest + cells.get(1, "")
            out.append([cells.get(i, "").strip() for i in range(len(COLS))])
    return out


def main():
    rows = []
    with pdfplumber.open(SRC) as pdf:
        for page in pdf.pages:
            rows += parse_page(page)
    df = pd.DataFrame(rows, columns=COLS)
    df.insert(0, "응답번호", range(1, len(df) + 1))
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"{len(df)}행 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
