# -*- coding: utf-8 -*-
"""⑥ 주 검증 — 참여 식당 순차 도입(stepped-wedge) 검정력 모의실험 (2026-09-23)

설계: 참여 식당을 4묶음으로 나눠 도입 순서를 추첨. 1개월째는 전부 미도입, 매달 한 묶음씩 혜택(체험권)을 켠다(총 5개월).
      측정은 첫 달부터 모든 식당에서 같게 한다: 체험 시설이 "원도심 참여 식당 영수증을 가진 체험 결제"를 식당별로 센다.
결과: 식당·월별 체험 결제 건수. 분석 = 포아송 GLM(식당 고정효과 + 월 고정효과 + 도입 여부), 식당 군집 강건 표준오차.
기준 건수(혜택 없을 때 식당 1곳 월 체험 결제)는 ⑤ 시뮬레이션에서 가져온다:
      식당 1곳 월 인증 × 체험 결제율 r × 반사실 몫(혜택 없어도 체험했을 비율)
출력: 보고서/성과도출_20260922/순차도입_검정력.json
"""
import json, numpy as np, pandas as pd
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

D = '보고서/성과도출_20260922'
S = json.load(open(f'{D}/시뮬레이션결과.json'))
rng = np.random.default_rng(20260923)
STEPS, PERIODS = 4, 5
NSIM = 400


def base_count(sc):
    r = S[sc]
    per_shop = r['인증_월']['P50'] / r['입력']['n1']            # 식당 1곳 월 인증
    return per_shop * 0.25 * 0.5                                  # × r 평균 25% × 반사실 50% = 혜택 없을 때 체험 결제


def one(n_shop, lam0, eff, cv=0.8, season=0.15, step_len=1):
    periods = PERIODS * step_len
    g = rng.permutation(np.repeat(np.arange(STEPS), int(np.ceil(n_shop / STEPS)))[:n_shop])   # 묶음 추첨
    lam_i = rng.gamma(1 / cv ** 2, lam0 * cv ** 2, n_shop)                                   # 식당별 기본 건수 차이
    s_t = np.exp(rng.normal(0, season, periods))                                              # 달마다 전체가 출렁임
    rows = []
    for i in range(n_shop):
        for t in range(periods):
            tr = int(t // step_len >= g[i] + 1)
            mu = lam_i[i] * s_t[t] * (1 + eff) ** tr
            y = rng.poisson(rng.gamma(4, mu / 4))                                             # 과산포(음이항)
            rows.append((i, t, tr, y))
    d = pd.DataFrame(rows, columns=['식당', '월', '도입', 'y'])
    d = d[d.groupby('식당')['y'].transform('sum') > 0]                                      # 전 기간 0건 식당은 정보가 없어 제외
    X = pd.get_dummies(d[['식당', '월']].astype(str), drop_first=True).astype(float)
    X['도입'] = d['도입']; X = sm.add_constant(X)
    try:
        m = sm.GLM(d['y'], X, family=sm.families.Poisson()).fit(cov_type='cluster', cov_kwds={'groups': d['식당']})
    except Exception:
        return False
    return m.pvalues['도입'] < 0.05 and m.params['도입'] > 0


R = {'설계': {'묶음': STEPS, '기간_개월': PERIODS, '반복': NSIM, '유의수준': 0.05}}
CASES = [('기본안', '기본안', 20, 1, '묶음당 1개월(총 5개월)'), ('기본안_2개월', '기본안', 20, 2, '묶음당 2개월(총 10개월)'),
         ('확대안', '확대안', 83, 1, '묶음당 1개월(총 5개월)')]
for key, sc, n_shop, sl, lab in CASES:
    lam0 = base_count(sc)
    curve = []
    for eff in (0.1, 0.2, 0.3, 0.5, 0.75, 1.0):
        pw = np.mean([one(n_shop, lam0, eff, step_len=sl) for _ in range(NSIM)])
        curve.append({'효과': eff, '검정력': float(pw)})
        print(key, n_shop, '곳 기준건수', round(lam0, 2), '효과', eff, '검정력', round(pw, 2), flush=True)
    mde = next((c['효과'] for c in curve if c['검정력'] >= 0.8), None)
    fp = np.mean([one(n_shop, lam0, 0.0, step_len=sl) for _ in range(NSIM)])               # 효과 0일 때 거짓 양성
    R[key] = {'식당수': n_shop, '설명': lab, '혜택없을때_식당월_체험결제': lam0, '곡선': curve, '검정력80_최소효과': mde, '효과0_거짓양성': float(fp)}
    print(key, '검정력 80% 최소 효과', mde, '거짓양성', round(fp, 3), flush=True)
R['예측_상대효과'] = 1 / 0.5 - 1      # 반사실 50%: 혜택 없어도 체험했을 사람의 두 배 → +100%
json.dump(R, open(f'{D}/순차도입_검정력.json', 'w'), ensure_ascii=False, indent=1)
