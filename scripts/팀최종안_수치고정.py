# -*- coding: utf-8 -*-
"""팀 최종안(「문제점 및 아이디어 정리」) 체험·문화 수치 고정판 (2026-09-20).

목적: 정의가 흔들려 값이 바뀌는 일을 끝낸다.
      흔들릴 수 있는 축(업종조합 x 모수 x 기준연도)을 전부 펼쳐 한 표로 출력한다.

고정 규칙 (프로젝트 CLAUDE.md 6장)
  - 카드 = 외지인 touDiv1, 파일 ..._touDiv1_2024-2026_1-8월_...csv (2024/2025/2026 모두 1~8월만 수록)
  - 방문 연인원 = D1 (BDT_01_01_006 시간대 교차표, 외지인(b)), 같은 1~8월
  - 시·군만, 이름 중복 시군구 제외  → 공통 146곳
출력: 보고서/팀최종안_수치고정_20260920.csv
"""
import sys, os, hashlib, pandas as pd, numpy as np
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 체험프레임_검증 import visits, cards, per_visit, SIM15

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
M = list(range(1, 9))
CARD = 'data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()[:8]

print(f"# 입력 지문  카드={md5(CARD)}")

# 업종 조합 4가지 — 이름에 포함 업종을 그대로 박아둔다
DEFS = {
 'D1_문화+유원+기타레저':              ['문화서비스','관광유원시설','기타레저'],
 'D2_D1+여행업':                       ['문화서비스','관광유원시설','기타레저','여행업'],
 'D3_D1+레저용품쇼핑':                 ['문화서비스','관광유원시설','기타레저','레저용품쇼핑'],
 'D4_레저체험전체(골프포함)':          ['문화서비스','관광유원시설','기타레저','골프장','스키장','여행업'],
}

P, V = {}, {}
for y in (2024, 2025, 2026):
    V[y] = visits(y, M)
    W, d = cards(CARD, y, M)
    P[y] = per_visit(W, V[y], d)

idx = sorted(set(P[2024].index) & set(P[2025].index) & set(P[2026].index))
for y in P: P[y] = P[y].loc[idx]
print(f"# 공통 시·군 {len(idx)}곳 (2024·2025·2026 1~8월 모두 존재)")

big = V[2026][V[2026] >= 5_000_000].index          # 방문 500만+ 시군
peer = [c for c in SIM15 + ['안동시'] if c in idx]  # 유사15곳+안동
POOLS = {'전국시군(146)': idx, '방문500만+': [c for c in idx if c in big], '유사15+안동': peer}

rows = []
for dname, cols in DEFS.items():
    cols = [c for c in cols if c in P[2024].columns]
    lv = {y: P[y][cols].sum(axis=1) for y in P}
    for base in (2024, 2025):
        chg = ((lv[2026] / lv[base] - 1) * 100).replace([np.inf, -np.inf], np.nan).dropna()
        for pname, pool in POOLS.items():
            s = chg[chg.index.isin(pool)]
            if '안동시' not in s.index: continue
            rows.append(dict(
                정의=dname, 기준연도=base, 모수=pname, 모수N=len(s),
                안동_기준=round(lv[base]['안동시'], 1), 안동_2026=round(lv[2026]['안동시'], 1),
                안동_변화율=round(chg['안동시'], 1),
                감소순위=int(s.rank(method='min')['안동시']),
                감소순위_백분위=round(s.rank(method='min')['안동시'] / len(s) * 100, 1),
                중앙값_변화율=round(s.median(), 1),
                경주_2026=round(lv[2026].get('경주시', np.nan), 1),
            ))

out = pd.DataFrame(rows)
out.to_csv('보고서/팀최종안_수치고정_20260920.csv', index=False)
pd.set_option('display.width', 200, 'display.max_columns', 30)
print(out.to_string(index=False))

print("\n# 전주시 존재 여부:", '전주시' in idx, "| 전주 관련 인덱스:",
      [c for c in idx if '전주' in c] or "없음(완산구/덕진구로 분리)")
print("# 안동 2026 1~8월 방문 연인원(D1, 외지인):", f"{V[2026]['안동시']:,.0f}")
