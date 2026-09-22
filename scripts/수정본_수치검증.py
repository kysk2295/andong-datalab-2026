# -*- coding: utf-8 -*-
"""수정본에 들어가는 모든 수치를 원자료에서 재계산 (2026-09-21).
POI는 반드시 '정확한 이름 일치'로 집계한다 (contains()는 '불국사역폐역' 등을 섞는다)."""
import sys, os, pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 체험프레임_검증 import visits, cards, per_visit

M = list(range(1, 9))
CARD = 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'
EXP = ['문화서비스', '관광유원시설', '기타레저']     # 골프·스키·여행업·레저용품쇼핑 제외

print("="*74); print("[1] 방문당 체험·문화 소비 (외지인 카드 ÷ D1 방문, 1~8월)")
P = {}
for y in (2024, 2026):
    W, d = cards(CARD, y, M)
    P[y] = per_visit(W, visits(y, M), d)
idx = sorted(set(P[2024].index) & set(P[2026].index))
a, b = P[2024].loc[idx, EXP].sum(axis=1), P[2026].loc[idx, EXP].sum(axis=1)
chg = ((b / a - 1) * 100).dropna()
print(f"  대상 시·군            {len(idx)}곳")
print(f"  안동 2024 1~8월       {a['안동시']:.1f}원")
print(f"  안동 2026 1~8월       {b['안동시']:.1f}원")
print(f"  변화율                {chg['안동시']:+.1f}%")
print(f"  전국 중앙 변화율      {chg.median():+.1f}%")
print(f"  안동 감소순위         {int(chg.rank(method='min')['안동시'])}/{len(chg)}")
print(f"  경주 2026 수준        {b['경주시']:.1f}원   → 안동/경주 = {b['안동시']/b['경주시']*100:.1f}%")
print(f"  전국 중앙 수준(2026)  {b.median():.1f}원")
print(f"  안동 수준순위(높은순) {int(b.rank(ascending=False, method='min')['안동시'])}/{len(b)}")

print("\n"+"="*74); print("[2] 관광지 방문↔소비 갭 (철도공사, 2022.4~6, 소비=건수)")
g = pd.read_csv('data/external/철도공사_8대도시/안동_관광지_방문소비갭.csv').set_index('관광지명')
for k in ['안동하회마을', '안동문화의거리', '월영교']:
    r = g.loc[k]
    print(f"  {k:<8} 방문 {r.방문점유율_pct:>5.2f}% / 소비건수 {r.방문객소비건수점유율_pct:>5.2f}% / 배율 {r.소비방문배율:.2f}")

print("\n"+"="*74); print("[3] 역사유적지 검색 비중 (LN_03_01_037, Top100 관광지 내 구성비)")
f = pd.read_csv('data/api_region/관광지검색Top100_기간별_LN_03_01_037.csv')
for per in ['2025_1-8', '2026_1-8']:
    for reg in ['경상북도 안동시', '경상북도 경주시']:
        s = f[(f.PERIOD == per) & (f.Q_SGG_NM == reg)]
        h = s[s.KTO_CATE_NAME_B == '역사유적지'].SRCH_CNT.sum()
        print(f"  {per}  {reg[5:]:<4} {h/s.SRCH_CNT.sum()*100:.1f}%   (역사유적지 {h:,} / Top100합 {s.SRCH_CNT.sum():,})")

print("\n"+"="*74); print("[4] 목적지검색 비중 (POI ÷ 시군 전체 검색) — 이름 정확일치")
den = pd.read_csv('data/bdt/내비게이션/시군구별_검색건수_연도별_BDT_03_01_003_1.csv').groupby(['SGG_NM','_YEAR']).SRCH_CNT.sum()
POI = [('경상북도 안동시','안동시','안동하회마을'), ('경상북도 안동시','안동시','월영교'),
       ('경상북도 안동시','안동시','도산서원'),     ('경상북도 경주시','경주시','불국사'),
       ('경상북도 경주시','경주시','동궁과월지'),   ('경상북도 경주시','경주시','경주월드'),
       ('경상북도 영주시','영주시','부석사')]
for reg, sgg, nm in POI:
    v = {}
    for per, yr in [('2018', 2018), ('2025', 2025)]:
        c = f[(f.PERIOD == per) & (f.Q_SGG_NM == reg) & (f.ITS_BRO_NM == nm)].SRCH_CNT.sum()
        v[yr] = (c, c / den[(sgg, yr)] * 100)
    print(f"  {sgg} {nm:<8} {v[2018][1]:5.2f}% → {v[2025][1]:5.2f}%  ({v[2025][1]/v[2018][1]*100-100:+6.1f}%)"
          f"  | 절대검색 {v[2018][0]:,}→{v[2025][0]:,}")
print(f"  ※ 안동 시군 전체 검색 {den[('안동시',2018)]:,} → {den[('안동시',2025)]:,} ({den[('안동시',2025)]/den[('안동시',2018)]:.2f}배)")
