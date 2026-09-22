# -*- coding: utf-8 -*-
"""이어드림 3단계 기대효과 — 1단계: 파라미터 추정 (2026-09-22)

2단계 추정–시뮬레이션의 앞 단계. 시뮬레이션에 넣을 파라미터를 보유 데이터로 추정하고, 불확실성은 부트스트랩 표본으로 남긴다.

  A. 혜택업체 이용률        주민증 가맹 26곳 이용 표시값 ÷ 소재 동 외지인 방문 → 업체 1곳이 소재 동 방문 1만 회당 월 몇 건
                            (카테고리별 경험분포 + 음이항 GLM 교차검증 + R1 합계 재현)
  B. 자연 완주율 c          철도공사 연관규칙(문화의거리→월영교) 역산 × 월영교 야간 검색 비중
  C. 야간 행사 효과         월영야행(월영교 야간 행사) 개최일 × 강남동/안동 외지인 소비 비중, 연·월 고정효과 회귀
  D. 가격·객단가            체험 가격 목록, 문화관광축제 56개 외지인 방문당 소비(경험분포)
  E. 월영교 소비 배율 환산   철도공사 2022 소비건수·방문으로 배율 0.40의 분자·분모 복원

출력: 보고서/성과도출_20260922/파라미터추정.json · 파라미터_부트스트랩.csv
"""
import json, re, numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

rng = np.random.default_rng(20260922)
D = '보고서/성과도출_20260922'
Q = json.load(open('보고서/교수브리핑_20260922/수치.json'))
R = {}

# ═════════ A. 혜택업체 이용률 ════════════════════════════════════════
bz = pd.read_excel('조사/02_디지털관광주민증_운영지자체.xlsx', sheet_name='안동_혜택업체27')
bz = bz[bz['공식분류'].notna() & (bz['혜택업체명'] != '행 수')].copy()
bz['이용'] = pd.to_numeric(bz['목록 이용표시(utztCnt)'], errors='coerce')
dong = pd.DataFrame(Q['혜택배치_대조']).set_index('혜택가맹점명')['행정동']
bz['행정동'] = bz['혜택업체명'].map(dong)
bz = bz[bz['이용'].notna()].copy()                                     # 코레일 철도여행(표시 없음) 제외 → 26곳

emd = pd.read_csv('data/api_region/안동_읍면동별_외지인_월별_BDT_01_01_005_1.csv')
per = emd[(emd.BASE_YM >= 202406) & (emd.BASE_YM <= 202608)]
dv = per.groupby('AREA_NM').TOU_NUM.sum() / per.BASE_YM.nunique()      # 가맹 기간 동안 동별 월평균 외지인 방문
MON = (pd.Timestamp('2026-09-21') - pd.Timestamp('2024-06-01')).days / 30.44   # 27.7개월(가맹 시작일은 업체별로 모름 → 전원 2024-06 가정)
bz['동월방문'] = bz['행정동'].map(dv)
bz['월이용'] = bz['이용'] / MON
bz['이용률_1만'] = bz['월이용'] / (bz['동월방문'] / 1e4)               # 소재 동 월방문 1만 회당 월 이용 건수
bz['분류'] = bz['공식분류'].replace({'관람': '관람'})
R['A_업체'] = bz[['혜택업체명', '분류', '행정동', '이용', '월이용', '동월방문', '이용률_1만']].round(4).to_dict('records')
R['A_가맹개월'] = MON

cat = bz.groupby('분류')['이용률_1만'].agg(['count', 'median', 'mean', 'min', 'max'])
R['A_분류별'] = cat.round(4).to_dict('index')

# 음이항 GLM: log E[이용] = log(월수) + β0 + β1·log(동월방문) + 분류 — 동 방문이 이용을 설명하는지, 분류 차이가 얼마인지
bz['l방문'] = np.log(bz['동월방문'])
glm = smf.glm('이용 ~ l방문 + C(분류, Treatment("식음료"))', data=bz,
              family=sm.families.NegativeBinomial(alpha=1.0), offset=np.log(np.full(len(bz), MON))).fit()
R['A_GLM'] = {'계수': glm.params.round(4).to_dict(), 'p값': glm.pvalues.round(4).to_dict(), 'n': int(glm.nobs)}
# 교차검증(LOO): 같은 분류 나머지 업체의 이용률 중앙값 × 자기 동 방문으로 자기 이용을 예측 → 로그 오차
err = []
for i, row in bz.iterrows():
    rest = bz[(bz['분류'] == row['분류']) & (bz.index != i)]
    if len(rest) == 0:
        continue
    pred = rest['이용률_1만'].median() * row['동월방문'] / 1e4 * MON
    err.append({'업체': row['혜택업체명'], '분류': row['분류'], '실제': row['이용'], '예측': round(pred, 1),
                '로그오차': round(float(np.log((row['이용'] + 1) / (pred + 1))), 3)})
E = pd.DataFrame(err)
R['A_LOO'] = {'중앙_절대로그오차': float(E['로그오차'].abs().median()),
              '배수로': float(np.exp(E['로그오차'].abs().median())),
              '표': E.to_dict('records')}
# 합계 재현: 이용 표시 합(2024.6~2026.9) vs R1 이용 건수 합(2024.6~2026.8)
u1 = pd.read_csv('data/정보공개청구/R1_이용건수_20260918.csv')
R['A_합계대조'] = {'이용표시_합': float(bz['이용'].sum()), 'R1_합': float(u1['이용건수'].sum()),
                  '비': float(bz['이용'].sum() / u1['이용건수'].sum())}

# 시뮬레이션용 표본: 원도심 릴레이 식당이 "지금 안동의 비관람 혜택업체(식음료·체험) 중 하나처럼" 작동한다고 보고 그 이용률을 부트스트랩
pool = bz[bz['분류'].isin(['식음료', '체험'])]['이용률_1만'].values
R['A_표본풀'] = {'n': int(len(pool)), '중앙': float(np.median(pool)), 'P10': float(np.quantile(pool, .1)),
                'P90': float(np.quantile(pool, .9)), '값': sorted(np.round(pool, 4).tolist())}
R['A_관람_참고'] = {'하회마을': float(bz.set_index('혜택업체명').loc['하회마을', '이용률_1만']),
                  '관람_중앙': float(bz[bz['분류'] == '관람']['이용률_1만'].median())}
R['A_중구동_월방문'] = float(dv['중구동'])
R['A_강남동_월방문'] = float(dv['강남동'])

# ═════════ B. 자연 완주율 c ═════════════════════════════════════════
# 규칙 "월영교 → 문화의거리": conf = P(문화|월영), lift = conf / P(문화) → P(문화) = conf/lift, P(월영) = support/conf
rules = {'차량': (0.197, 0.595, 1.174), '철도': (0.237, 0.680, 1.054)}   # 철도공사 슬라이드 48~50 상위 규칙
B = {}
for k, (s, cf, lf) in rules.items():
    p_mun = cf / lf
    B[k] = {'P(문화의거리)': p_mun, 'P(월영교)': s / cf, 'P(월영교|문화의거리)': s / p_mun}
night = {'2024_1-8': 0.434, '2026_1-8': 0.402}                        # 월영교 검색 중 야간 비중(야간관광 BY_TH_NIGHT_TOUR, 9/18 보고서)
c_vals = [B[k]['P(월영교|문화의거리)'] * v for k in B for v in night.values()]
R['B_연관규칙'] = B
R['B_야간비중'] = night
R['B_c'] = {'값': c_vals, '최소': min(c_vals), '최대': max(c_vals), '평균': float(np.mean(c_vals))}

# ═════════ C. 월영야행 효과 (강남동/안동 외지인 소비 비중) ═══════════════════
gn = pd.read_csv('data/datalab_추가/안동시_강남동_외지인_소비_20260919/월별_관광총소비_화면확인.csv')
gn = gn.set_index('기준월')['금액_원']
cards = []
for f in ('시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv',
          '시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv',
          '시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv'):
    c = pd.read_csv(f'data/bdt/신용카드/{f}').drop_duplicates()
    cards.append(c[(c.SGG_NM == '안동시') & (c.KTO_TOB_MCLS_NM == '관광총소비')][['BASE_DATE', 'CNSM_AMT']])
ad = pd.concat(cards).drop_duplicates('BASE_DATE').set_index('BASE_DATE')['CNSM_AMT'] * 1000
df = pd.DataFrame({'강남동': gn, '안동': ad}).dropna()
df['비중'] = df['강남동'] / df['안동']
df['연'] = df.index // 100
df['월'] = df.index % 100
# 월영야행 개최일(보도·관광 누리집): 2023 7/29~8/6, 2024 7/26~8/4, 2025 8/1~8/9, 2026 7/31~8/9
ev = {}
for s, e in (('2023-07-29', '2023-08-06'), ('2024-07-26', '2024-08-04'), ('2025-08-01', '2025-08-09'), ('2026-07-31', '2026-08-09')):
    for d in pd.date_range(s, e):
        ev[d.year * 100 + d.month] = ev.get(d.year * 100 + d.month, 0) + 1
df['행사일'] = [ev.get(i, 0) for i in df.index]
df['로그비중'] = np.log(df['비중'])
m1 = smf.ols('로그비중 ~ 행사일 + C(연) + C(월)', data=df).fit(cov_type='HC3')
m0 = smf.ols('로그비중 ~ 행사일 + C(연)', data=df).fit(cov_type='HC3')           # 월 고정효과 없이(계절 혼입)
beta, se = m1.params['행사일'], m1.bse['행사일']
gn_day = df['강남동'].mean() / 30.4
R['C_월영야행'] = {
    '관측월': int(len(df)), '기간': f"{df.index.min()}~{df.index.max()}",
    '행사일_월별': {str(k): v for k, v in ev.items()},
    '월FE_β_행사1일': float(beta), '월FE_SE': float(se), '월FE_p': float(m1.pvalues['행사일']),
    '월FE_95%': [float(beta - 1.96 * se), float(beta + 1.96 * se)],
    '월FE없음_β': float(m0.params['행사일']), '월FE없음_p': float(m0.pvalues['행사일']),
    '행사1일당_강남동소비_증가율': float(np.exp(beta) - 1),
    '강남동_하루평균소비': float(gn_day),
    '행사1일당_증가액_원': float((np.exp(beta) - 1) * df['강남동'].mean()),     # 월 소비 대비 증가 → 그 달 강남동 소비의 증가분
    '비중_7·8월평균': float(df[df['월'].isin([7, 8])]['비중'].mean()), '비중_기타평균': float(df[~df['월'].isin([7, 8])]['비중'].mean()),
}
R['C_자료'] = df.reset_index().rename(columns={'index': '기준월'}).round(6).to_dict('records')
# 부트스트랩(잔차 재표본) 대신 β의 정규 근사 표본을 시뮬레이션에 넘긴다
beta_draws = rng.normal(beta, se, 10000)

# ═════════ D. 가격·객단가 ═════════════════════════════════════════
ex = pd.read_excel('조사/03_체험프로그램_목록가격.xlsx', sheet_name='체험프로그램')
prices = []
for t in ex['가격'].astype(str):
    if '30명' in t or '1박2일' in t:
        continue                                                        # 단체·숙박형은 개인 저녁 연결 불가(조사/03)
    for a, b in re.findall(r'(\d{1,3}(?:,\d{3})+|\d+)원?\s*~\s*(\d{1,3}(?:,\d{3})+|\d+)원', t):
        prices += [int(a.replace(',', '')), int(b.replace(',', ''))]
    for a in re.findall(r'(?<![~\d,])(\d{1,3}(?:,\d{3})+)원(?!\s*~)', t):
        prices.append(int(a.replace(',', '')))
prices = sorted(p for p in prices if 3000 <= p <= 60000)
R['D_체험가격'] = {'n': len(prices), '값': prices, '중앙': float(np.median(prices))}

fc = pd.read_csv('data/축제_전체/관광소비_FE_01_01_007.csv')
fc = fc[(fc.FSTV_YEAR == 2025) & (fc.LRFRN_DIV_CD == 1)].groupby('FSTV_ID')['SUM_CNSM_AMT'].sum()
fv = pd.read_csv('data/축제_전체/연도별방문자_FE_01_01_005_01.csv')
fv = fv[fv.BASE_YEAR == 2025].groupby('FSTV_ID')['TOT_OUT'].sum()
pv = (fc / fv).replace([np.inf, -np.inf], np.nan).dropna()
pv = pv[pv > 0]
R['D_축제객단가'] = {'n': int(len(pv)), 'P10': float(pv.quantile(.1)), '중앙': float(pv.median()), 'P90': float(pv.quantile(.9)),
                  '값': sorted(np.round(pv.values).tolist())}

# ═════════ E. 월영교 소비 배율 0.40의 분자·분모 ═════════════════════════
gap = pd.read_csv('data/external/철도공사_8대도시/안동_관광지_방문소비갭.csv')
R['E_철도공사'] = gap.head(3).to_dict('records')
# 월영교 방문자 35,116명(2022.4~6) · 소비건수 점유 6.05% — 총 소비건수는 보고서 비공개라 배율(점유율 비)로만 환산
R['E_배율'] = {'월영교': 0.40, '원도심(문화의거리)': 1.73, '월영교_방문자_2022Q2': 35116}

# ═════════ 저장 ═══════════════════════════════════════════════════
N = 10000
boot = pd.DataFrame({
    '업체이용률_1만': rng.choice(pool, N, replace=True),
    'c_자연완주율': rng.choice(c_vals, N, replace=True) * rng.uniform(0.9, 1.1, N),   # 네 조합 + ±10% 흔들기
    '월영야행_β': beta_draws,
    '체험가격': rng.choice(prices, N, replace=True),
    '팝업객단가': rng.choice(pv.values, N, replace=True),
})
boot.to_csv(f'{D}/파라미터_부트스트랩.csv', index=False, encoding='utf-8-sig')
json.dump(R, open(f'{D}/파라미터추정.json', 'w'), ensure_ascii=False, indent=1, default=float)

print('A 분류별 이용률(동 월방문 1만당 월 건수)\n', cat.round(3))
print('A GLM', R['A_GLM'])
print('A LOO 중앙 절대로그오차', round(R['A_LOO']['중앙_절대로그오차'], 3), '→ 배수', round(R['A_LOO']['배수로'], 2))
print('A 합계대조', R['A_합계대조'])
print('A 풀(식음+체험)', {k: v for k, v in R['A_표본풀'].items() if k != '값'}, '중구동 월방문', round(dv['중구동']))
print('B', {k: {a: round(b, 3) for a, b in v.items()} for k, v in B.items()}, 'c', [round(x, 3) for x in c_vals])
print('C', {k: (round(v, 4) if isinstance(v, float) else v) for k, v in R['C_월영야행'].items() if k != '행사일_월별'})
print('D 체험가격', R['D_체험가격']['n'], R['D_체험가격']['중앙'], prices)
print('D 축제', {k: v for k, v in R['D_축제객단가'].items() if k != '값'})
