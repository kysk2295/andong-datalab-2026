# -*- coding: utf-8 -*-
"""안동역 승하차(이음·새마을·무궁화, 2024.1~2026.8) 월별 표 → long CSV.

원본 표 구조(시트 = 열차종류):
  6행 = 월(2024년 01월 …, 병합), 7행 = 구분(평일/주말/공휴일/명절대수송, 병합), 8행 = 요일
  9~32행  = 승차 시간대 00-01 … 23-24
  38~61행 = 하차 시간대
값은 '그 달의 해당 요일 전체 합'이다(예: 2024-01 평일 월 = 1월의 모든 월요일 합). 일평균 아님.
0은 그 시간대에 정차 열차가 없다는 뜻일 수 있어 결측과 구분되지 않는다.
"""
import re
import pandas as pd

SRC = "data/팀원취합/안동역 승하차 인원 자료(이음, 새마을, 무궁화 2024.1.1.~2026.8.31.).xlsx"
OUT = "data/external/팀원취합_정제/안동역_승하차_월별_열차종류별_long.csv"

BLOCKS = {"승차": range(8, 32), "하차": range(37, 61)}  # 0-based 행 인덱스
rows = []

for sheet in ["KTX-이음", "새마을", "무궁화"]:
    raw = pd.read_excel(SRC, sheet_name=sheet, header=None)
    month = raw.iloc[5].ffill()      # 6행
    daytype = raw.iloc[6]            # 7행
    weekday = raw.iloc[7]            # 8행

    # 구분은 월 블록 안에서만 ffill (월 경계를 넘기지 않게)
    dt, cur, cur_month = {}, None, None
    for c in range(3, raw.shape[1]):
        m = month.iat[c]
        if m != cur_month:
            cur_month, cur = m, None
        if pd.notna(daytype.iat[c]):
            cur = daytype.iat[c]
        dt[c] = cur

    for kind, rng in BLOCKS.items():
        for r in rng:
            slot = raw.iat[r, 2]
            if not isinstance(slot, str) or not re.match(r"\d\d-\d\d", slot):
                continue
            for c in range(3, raw.shape[1]):
                m, w, v = month.iat[c], weekday.iat[c], raw.iat[r, c]
                if pd.isna(m) or pd.isna(w) or pd.isna(v):
                    continue
                ym = re.match(r"(\d{4})년\s*(\d{2})월", str(m))
                rows.append({
                    "열차종류": sheet, "승하차": kind,
                    "연월": f"{ym.group(1)}-{ym.group(2)}" if ym else str(m),
                    "구분": dt[c], "요일": w, "시간대": slot, "인원": int(v),
                })

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"{OUT}  {len(df):,}행")
print(df.groupby(["열차종류", "승하차"])["인원"].sum().to_string())
print("연월:", df['연월'].min(), "~", df['연월'].max(), "/ 구분:", sorted(df['구분'].dropna().unique()))
