# -*- coding: utf-8 -*-
"""하위 진단점수 3종의 출처와 값을 확인·재현한다.

기획서(v7)의 값은 업종 **대분류**(LN_03_01_045, 전 기간 합산) 기준이다.
1장 소비 구성의 값은 신용카드 **중분류**(BDT_02_01_003_35, 2026.1~8) 기준으로
포함 범위가 달라 값이 크게 다르다. 둘을 함께 출력해 혼동을 막는다.
"""
import pandas as pd

CITIES = ['안동시', '공주시', '부여군', '문경시', '남원시', '충주시', '강화군']

# ── ① 대분류 기준 (기획서 27.9 / 9.9의 출처) ─────────────────────────────
EXP_MACRO = ['레저스포츠', '문화관광', '역사관광', '자연관광', '체험관광']
d = pd.read_csv('data/api_region/업종별_소비비중_LN_03_01_045.csv')
d['시군'] = d.SGG_NM.str.split().str[-1]
mac = d[d.시군.isin(CITIES)].pivot_table(index='시군', columns='CD_NM', values='CD_RAT').reindex(CITIES)
macro = pd.DataFrame({'체험': mac[EXP_MACRO].sum(axis=1), '숙박': mac['숙박']}).round(2)

# ── ② 중분류 기준 (1장 소비 구성) ────────────────────────────────────────
EXP_MID  = ['관광유원시설', '문화서비스', '기타레저', '여행업']
STAY_MID = ['호텔', '콘도', '기타숙박', '캠핑장/펜션']
c = pd.read_csv('data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv')
c = c[(c.BASE_DATE.astype(str).str[:4] == '2026') & (c.SGG_NM.isin(CITIES))]
tot = c[c.KTO_TOB_MCLS_NM == '관광총소비'].groupby('SGG_NM').CNSM_AMT.sum()
mid = pd.DataFrame({
    '체험': c[c.KTO_TOB_MCLS_NM.isin(EXP_MID)].groupby('SGG_NM').CNSM_AMT.sum() / tot * 100,
    '숙박': c[c.KTO_TOB_MCLS_NM.isin(STAY_MID)].groupby('SGG_NM').CNSM_AMT.sum() / tot * 100,
}).reindex(CITIES).round(2)

# ── ③ 야간 (이동통신 21~24시) ────────────────────────────────────────────
m = pd.read_csv('data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_2025.csv')
m = m[m['C:방문자유형별'].str.contains('외지인', na=False) & m['R:기초단체'].isin(CITIES) & m['C:시간대'].notna()]
night = (m[m['C:시간대'] == '21~24시'].groupby('R:기초단체')['V:방문자 수'].sum()
         / m.groupby('R:기초단체')['V:방문자 수'].sum() * 100).reindex(CITIES).round(2)

def gap(series, label):
    comp = series.drop('안동시')
    q = comp.quantile(0.75)
    print(f'  {label}: 안동 {series["안동시"]:.2f} / 상위25% {q:.2f} / 격차 {series["안동시"]-q:+.2f}%p / 중앙값 {comp.median():.2f}')

print('=== ① 업종 대분류 (LN_03_01_045, 전 기간) — 기획서 수치의 출처 ===')
print(macro.to_string()); gap(macro['체험'], '체험'); gap(macro['숙박'], '숙박')
print('\n=== ② 업종 중분류 (BDT_02_01_003_35, 2026.1~8) — 1장 소비 구성 ===')
print(mid.to_string()); gap(mid['체험'], '체험'); gap(mid['숙박'], '숙박')
print('\n=== ③ 야간 21~24시 방문 비중 (2025) ===')
print(night.to_string()); gap(night, '야간')

pd.concat([macro.add_suffix('_대분류'), mid.add_suffix('_중분류'),
           night.rename('야간')], axis=1).to_csv('조사/15_진단점수_재계산.csv', encoding='utf-8-sig')
print('\n저장: 조사/15_진단점수_재계산.csv')
