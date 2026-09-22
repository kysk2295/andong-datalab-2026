# -*- coding: utf-8 -*-
"""⑥ 사후 효과 검증계획 — 합성통제 사전 적합 + 가짜 시행 검정 + 최소 검출 효과(MDE) (2026-09-23)

결과 변수: 분기별 방문당 체험·문화 소비(외지인 카드 ÷ D1 방문), 2022Q1 = 기준(2022~2023 평균 = 100) 지수
          2024Q4는 카드 자료 없음 → 제외, 2024Q3은 7·8월만
비교 후보: A = 디지털관광주민증 운영 지자체(릴레이 미시행, 시·군만) / B = 광역시 자치구를 뺀 전국 시·군(강건성)
설계: 사전 2022Q1~2025Q2로 가중치를 정하고, 2025Q3~2026Q2를 "가짜 시행 후"로 둬서
      ① 사전 적합 품질 ② 효과가 없을 때 검정이 잘못 잡지 않는지(가짜 시행) ③ 효과 δ를 넣었을 때 몇 %부터 잡히는지(MDE)를 본다.
추론: 후보 각 지역을 가짜 처치로 놓은 placebo → 사후/사전 RMSPE 비율의 순위 p값 (Abadie 2010)
출력: 보고서/성과도출_20260922/사후검증_결과.json, g6_합성통제.png, g7_검출력.png
"""
import json, numpy as np, pandas as pd
from scipy.optimize import nnls
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D = '보고서/성과도출_20260922'
S = json.load(open(f'{D}/시뮬레이션결과.json'))
pan = pd.read_csv('data/external/사후검증_패널/시군_월별_체험문화_방문.csv')
pan['분기'] = pan['연월'] // 100 * 10 + ((pan['연월'] % 100 - 1) // 3 + 1)      # 20251 = 2025Q1
pan = pan[(pan['연월'] >= 202201)]
Q = pan.groupby(['시군', '분기'])[['체험문화', '체험문화_유원제외', '방문']].sum().reset_index()
Q = Q[Q['분기'] != 20244]
Q = Q[Q['분기'] <= 20262]
QS = sorted(Q['분기'].unique())
PRE = [q for q in QS if q <= 20252]
POST = [q for q in QS if q >= 20253]

hx = pd.read_excel('조사/02_디지털관광주민증_운영지자체.xlsx', sheet_name='운영지자체')
jm = [n for n in hx['지자체명'].dropna() if (n.endswith('시') or n.endswith('군')) and '광역시' not in n and n != '안동시']


def panel(col):
    Y = Q.pivot(index='분기', columns='시군', values=col) / Q.pivot(index='분기', columns='시군', values='방문')
    Y = Y.loc[QS]
    ok = Y.notna().all() & (Y > 0).all() & (Q.groupby('시군')['방문'].sum().reindex(Y.columns) / len(QS) > 200_000)
    Y = Y.loc[:, ok]
    base = Y.loc[[q for q in QS if q <= 20234]].mean()
    return Y, Y / base * 100


def synth(Y, target, pool, K=10):
    # 과적합 방지: 사전 기간 추세 상관이 높은 후보 K곳만 쓴다(후보 수 > 사전 관측 수면 사전 적합이 거짓으로 완벽해짐)
    cor = Y.loc[PRE, pool].corrwith(Y.loc[PRE, target]).sort_values(ascending=False)
    pool = list(cor.index[:K])
    X = Y.loc[PRE, pool].values
    y = Y.loc[PRE, target].values
    lam = 1e3
    w, _ = nnls(np.vstack([X, lam * np.ones(len(pool))]), np.append(y, lam))
    return pd.Series(w, index=pool)


def rmspe(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def run(col, pool_name, K=10, split=20252):
    global PRE, POST
    PRE = [q for q in QS if q <= split]
    POST = [q for q in QS if q > split][:4]
    Y, I = panel(col)
    pool = [c for c in (jm if pool_name == 'A' else [c for c in I.columns if c.endswith(('시', '군')) and c != '안동시']) if c in I.columns]
    units = ['안동시'] + pool
    res = {}
    for u in units:
        donors = [p for p in pool if p != u]
        w = synth(I, u, donors, K)
        syn = I[w.index] @ w
        res[u] = {'w': w, 'syn': syn, 'pre': rmspe(I.loc[PRE, u], syn.loc[PRE]), 'post': rmspe(I.loc[POST, u], syn.loc[POST])}
    ratio = pd.Series({u: r['post'] / r['pre'] for u, r in res.items()})
    # 한 방향 통계량: 사후 평균 격차 ÷ 사전 RMSPE (효과가 "올랐나"만 본다)
    sig = pd.Series({u: float((I.loc[POST, u] - r['syn'].loc[POST]).mean()) / r['pre'] for u, r in res.items()})
    pre_r = pd.Series({u: r['pre'] for u, r in res.items()})
    a = res['안동시']
    p_placebo = float((ratio >= ratio['안동시']).mean())
    # MDE: 안동 사후 값에 효과 δ를 곱해 넣고 순위 p값이 0.10 이하가 되는 최소 δ
    curve = []
    for d in np.arange(0, 0.505, 0.005):
        yp = I.loc[POST, '안동시'] * (1 + d)
        r_d = rmspe(yp, a['syn'].loc[POST]) / a['pre']
        rr = ratio.copy(); rr['안동시'] = r_d
        t_d = float((yp - a['syn'].loc[POST]).mean()) / a['pre']
        ss = sig.copy(); ss['안동시'] = t_d
        curve.append({'δ': float(d), 'p': float((rr >= r_d).mean()), 'p_한방향': float((ss >= t_d).mean())})
    cv = pd.DataFrame(curve)
    mde10 = cv[cv['p'] <= 0.10]['δ'].min()
    mde05 = cv[cv['p'] <= 0.05]['δ'].min()
    mde_s = cv[cv['p_한방향'] <= 0.10]['δ'].min()
    top = a['w'][a['w'] > 0.01].sort_values(ascending=False)
    return {
        '후보수': len(pool), '사전분기': len(PRE), '가짜사후분기': len(POST),
        '안동_사전RMSPE': a['pre'], '사전RMSPE_순위(낮을수록 좋음)': int((pre_r < a['pre']).sum() + 1), '후보포함_단위수': len(units),
        '사전RMSPE_중앙(후보)': float(pre_r.drop('안동시').median()),
        '가짜시행_p': p_placebo, '가짜시행_사후사전비': float(ratio['안동시']),
        'MDE_p10': None if pd.isna(mde10) else float(mde10), 'MDE_한방향_p10': None if pd.isna(mde_s) else float(mde_s),
        '가짜시행_p_한방향': float((sig >= sig['안동시']).mean()), '사후평균격차': float((I.loc[POST, '안동시'] - a['syn'].loc[POST]).mean()), 'MDE_p05': None if pd.isna(mde05) else float(mde05),
        '가중치': {k: round(float(v), 3) for k, v in top.items()},
        '곡선': curve,
    }, I, a


R = {'결과변수': '분기별 방문당 체험·문화 소비 지수(2022~2023 평균 = 100)'}
# 강건성 격자: 후보 수 K × 가짜 시행 시점 → 효과가 없는 구간에서 거짓 양성(p ≤ 0.10)이 나오는지
grid = []
for K in (5, 10, 15, 48):
    for sp in (20242, 20251, 20252):
        r, _, _ = run('체험문화', 'A', K, sp)
        grid.append({'K': K, '가짜시행_기준분기': sp, 'p': r['가짜시행_p'], 'p_한방향': r['가짜시행_p_한방향'], '격차': r['사후평균격차'],
                     'MDE_p10': r['MDE_p10'], 'MDE_한방향': r['MDE_한방향_p10'], '안동_사전RMSPE': r['안동_사전RMSPE']})
R['강건성격자'] = grid
print(pd.DataFrame(grid).to_string())
main, I, A = run('체험문화', 'A', 10, 20252)
R['A_주민증후보'] = main
R['사전'] = [str(q) for q in PRE]; R['가짜사후'] = [str(q) for q in POST]
R['B_전국시군'], _, _ = run('체험문화', 'B', 10, 20252)
R['A_유원시설제외'], _, _ = run('체험문화_유원제외', 'A', 10, 20252)
main, I, A = run('체험문화', 'A', 10, 20252)
R['시계열'] = {'분기': [str(q) for q in QS], '안동': [float(v) for v in I['안동시'].values], '합성': [float(v) for v in A['syn'].values],
              '사전분기수': len(PRE)}
R['예측효과'] = {'기본안': S['기본안']['지표1_증가율']['P50'], '확대안': S['확대안']['지표1_증가율']['P50'],
               '확대안_P95': S['확대안']['지표1_증가율']['P95'], '목표': S['고정값']['목표'] / 152.66675490128523 - 1}
json.dump(R, open(f'{D}/사후검증_결과.json', 'w'), ensure_ascii=False, indent=1, default=float)

for k in ('A_주민증후보', 'B_전국시군', 'A_유원시설제외'):
    r = R[k]
    print(k, {x: (round(v, 3) if isinstance(v, float) else v) for x, v in r.items() if x not in ('곡선',)})
print('예측효과', R['예측효과'])

# ── 그림 ───────────────────────────────────────────────────────────
plt.rcParams.update({'font.family': 'NanumGothic', 'axes.unicode_minus': False, 'svg.fonttype': 'path',
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#999999',
                     'axes.titleweight': 'bold', 'axes.titlesize': 11, 'font.size': 9.5})
RED, GRAY = '#D64541', '#8C8C8C'
lab = [f"{str(q)[2:4]}.{str(q)[4]}Q" for q in QS]
x = np.arange(len(QS))
fig, ax = plt.subplots(figsize=(9, 3.2))
ax.plot(x, I['안동시'].values, color=RED, lw=2, marker='o', ms=3, label='안동(실제)')
ax.plot(x, A['syn'].values, color=GRAY, lw=2, ls='--', label='비교 조합(합성 안동)')
ax.axvspan(len(PRE) - .5, len(QS) - .5, color='#FFE599', alpha=.45, zorder=0)
ax.text(len(PRE) + (len(POST) - 1) / 2, ax.get_ylim()[1] * .98, '가짜 시행 후\n(효과 없어야 정상)', ha='center', va='top', fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=7.5, rotation=0)
ax.set_ylabel('지수 (2022~2023 평균 = 100)', fontsize=8.5); ax.legend(frameon=False, fontsize=8.5, loc='lower left')
save_kw = dict(dpi=200, bbox_inches='tight', facecolor='white')
fig.savefig(f'{D}/g6_합성통제.png', **save_kw); fig.savefig(f'{D}/g6_합성통제.svg', **save_kw); plt.close(fig)

cv = pd.DataFrame(main['곡선'])
cvb = pd.DataFrame(R['B_전국시군']['곡선'])
fig, ax = plt.subplots(figsize=(9, 3.0))
ax.plot(cv['δ'] * 100, cv['p_한방향'], color=RED, lw=2, label=f"한 방향 검정(주): 주민증 운영 후보 {main['후보수']}곳")
ax.plot(cvb['δ'] * 100, cvb['p_한방향'], color=GRAY, lw=1.5, ls='--', label=f"한 방향 검정: 전국 시·군 {R['B_전국시군']['후보수']}곳")
ax.plot(cv['δ'] * 100, cv['p'], color=RED, lw=1, ls=':', alpha=.7, label='양방향(RMSPE 비) 참고')
ax.axhline(0.10, color='#333', lw=.8, ls=':'); ax.text(49, 0.115, '유의수준 0.10', ha='right', fontsize=8)
ef = R['예측효과']
for v, t in ((ef['기본안'], '기본안\n예측'), (ef['확대안'], '확대안\n예측'), (ef['목표'], '회복\n목표')):
    ax.axvline(v * 100, color='#999', lw=.8)
    ax.text(v * 100 + .4, .82, f"{t}\n+{v * 100:.1f}%", fontsize=7.5, va='top')
ax.set_xlim(0, 50); ax.set_ylim(0, 1.02)
ax.set_xlabel('사업 후 방문당 체험·문화 소비가 오른 폭 δ (%)', fontsize=8.5); ax.set_ylabel('가짜 처치 순위 p값', fontsize=8.5)
ax.legend(frameon=False, fontsize=8.5, loc='upper right')
fig.savefig(f'{D}/g7_검출력.png', **save_kw); fig.savefig(f'{D}/g7_검출력.svg', **save_kw); plt.close(fig)
