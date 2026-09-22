# -*- coding: utf-8 -*-
"""교수님 대시보드 「문제」 화면용 시·군 × 업종 방문당 소비 표(2026-09-23)

선택한 시·군을 안동과 업종별로 비교할 수 있게, 146개 시·군의 업종별 외지인 방문당 소비(2024·2026년 1~8월)를 만든다.
규칙: 카드 = 외지인 touDiv1, 방문 = D1(BDT_01_01_006) 시간대 합, 시·군만, 이름 중복 제외(교수브리핑_수치.py와 같은 로더).
출력: 보고서/교수님_대시보드/data/시군_업종.csv (시군, 업종, 2024, 2026)
"""
import sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 체험프레임_검증 import visits, cards, per_visit

CARD = 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'
M = list(range(1, 9))
P = {}
for y in (2024, 2026):
    W, d = cards(CARD, y, M)
    P[y] = per_visit(W, visits(y, M), d)
idx = sorted(set(P[2024].index) & set(P[2026].index))
up = pd.read_csv('보고서/교수님_대시보드/data/안동_업종.csv')          # 대시보드에 쓰는 업종 12개(안동 소비 순)
rows = []
for s in idx:
    for u in up['업종']:
        rows.append({'시군': s, '업종': u, '2024': float(P[2024].loc[s].get(u, 0)), '2026': float(P[2026].loc[s].get(u, 0))})
out = pd.DataFrame(rows)
a = out[out['시군'] == '안동시'].set_index('업종')
chk = up.set_index('업종')
assert ((a['2024'] - chk['2024']).abs() < 1e-6).all() and ((a['2026'] - chk['2026']).abs() < 1e-6).all(), '안동 값 불일치'
out.to_csv('보고서/교수님_대시보드/data/시군_업종.csv', index=False, encoding='utf-8-sig')
print(len(idx), '시군 ×', len(up), '업종 → 안동 값 일치')
