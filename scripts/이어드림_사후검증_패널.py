# -*- coding: utf-8 -*-
"""⑥ 사후 검증계획서용 시군 월별 패널 — 방문당 체험·문화 소비 (2026-09-23)

분자: 외지인 카드 소비(touDiv1) 문화서비스 + 관광유원시설 + 기타레저 (골프장·스키장·여행업·레저용품쇼핑 제외, 문제 1 정의 D1과 같음)
분모: 외지인 방문 연인원 D1(BDT_01_01_006, 시간대 합) — 월별로 다시 집계
기간: 2019-01 ~ 2026-08 (카드 2024-09~12 없음)
출력: data/external/사후검증_패널/시군_월별_체험문화_방문.csv
"""
import os, pandas as pd

OUT = 'data/external/사후검증_패널'
os.makedirs(OUT, exist_ok=True)
EXP = ['문화서비스', '관광유원시설', '기타레저']

# ── 분모: D1 월별 외지인 방문(연도 파일별 청크 집계, 캐시) ─────────────────────
vis_path = f'{OUT}/D1_시군_월별_외지인방문.csv'
if not os.path.exists(vis_path):
    parts = []
    for y in range(2019, 2027):
        f = f'data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{y}.csv'
        for ch in pd.read_csv(f, chunksize=3_000_000, usecols=['R:기초단체', 'R:기준연월', 'C:방문자유형별', 'C:시간대', 'V:방문자 수']):
            ch = ch[(ch['C:방문자유형별'] == '외지인(b)') & ch['C:시간대'].notna()]
            parts.append(ch.groupby(['R:기초단체', 'R:기준연월'])['V:방문자 수'].sum())
        print('D1', y, flush=True)
    vis = pd.concat(parts).groupby(level=[0, 1]).sum().rename('방문').reset_index()
    vis.columns = ['시군', '연월', '방문']
    vis.to_csv(vis_path, index=False, encoding='utf-8-sig')
vis = pd.read_csv(vis_path)

# ── 분자: 외지인 카드 체험·문화 월별 ─────────────────────────────────────
cards = []
for f in ('시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv',
          '시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv',
          '시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'):
    c = pd.read_csv(f'data/bdt/신용카드/{f}').drop_duplicates()
    cards.append(c)
c = pd.concat(cards).drop_duplicates(['BASE_DATE', 'SGG_NM', 'KTO_TOB_MCLS_NM'])
# 같은 이름이 여러 광역에 있는 시군구(고성군·동구 등)는 한 달에 관광총소비 행이 2개 이상 → 제외
n = c[c.KTO_TOB_MCLS_NM == '관광총소비'].groupby(['SGG_NM', 'BASE_DATE']).size()
dup = set(n[n > 1].index.get_level_values(0))
c = c[~c.SGG_NM.isin(dup)]
ex = c[c.KTO_TOB_MCLS_NM.isin(EXP)].groupby(['SGG_NM', 'BASE_DATE']).CNSM_AMT.sum() * 1000
ex2 = c[c.KTO_TOB_MCLS_NM.isin(['문화서비스', '기타레저'])].groupby(['SGG_NM', 'BASE_DATE']).CNSM_AMT.sum() * 1000
tot = c[c.KTO_TOB_MCLS_NM == '관광총소비'].groupby(['SGG_NM', 'BASE_DATE']).CNSM_AMT.sum() * 1000
cd = pd.DataFrame({'체험문화': ex, '체험문화_유원제외': ex2, '관광총소비': tot}).fillna(0).reset_index()
cd.columns = ['시군', '연월', '체험문화', '체험문화_유원제외', '관광총소비']

pan = cd.merge(vis, on=['시군', '연월'], how='inner')
pan = pan[~pan['시군'].isin(dup)]
pan.to_csv(f'{OUT}/시군_월별_체험문화_방문.csv', index=False, encoding='utf-8-sig')
print('패널', pan.shape, pan['시군'].nunique(), '시군', pan['연월'].min(), '~', pan['연월'].max(), '중복 제외', len(dup))
a = pan[pan['시군'] == '안동시'].set_index('연월')
a24 = a.loc[202401:202408]; a26 = a.loc[202601:202608]
print('검산 안동 1~8월 방문당 체험·문화', round(a24['체험문화'].sum() / a24['방문'].sum(), 2), '→', round(a26['체험문화'].sum() / a26['방문'].sum(), 2))
