# -*- coding: utf-8 -*-
"""⑦ 전국 진단표 — 시·군별 4개 지표로 "방문은 오는데 소비·체류로 안 이어지는" 유형을 찾는 탐색 지표 (2026-09-23)

지표 (모두 외지인 기준, 같은 방향 = 값이 나쁠수록 문제 백분위가 높다)
  ① 방문당 체험·문화 소비 변화율  2024→2026 1~8월 (카드 문화서비스+관광유원시설+기타레저 ÷ D1 방문)   낮을수록 문제
  ② 평균 숙박일수                  2025 (데이터랩 LN_02_01_013)                                          짧을수록 문제
  ③ 저녁 전환율                    18~21시 ÷ 14~18시 방문, 2026 1~8월 (D1)                               낮을수록 문제
  ④ 야간 방문 비중                 21~24시 ÷ 06~24시 방문, 2026 1~8월 (D1)                               낮을수록 문제
진단 점수 = 네 지표 문제 백분위의 가중평균(기본 같은 가중치). 정책 효과 점수가 아니라 추가 진단이 필요한 곳을 골라내는 탐색 지표.
가중치 민감도: 디리클레 무작위 가중치 1,000번 → 순위 분포(P10~P90)
대상: 네 지표가 모두 있는 시·군, 방문 연인원(2026 1~8월) 100만 이상
출력: 보고서/전국진단_20260923/전국진단표.csv · 전국진단.json · g8_안동위치.png
"""
import os, json, numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = '보고서/전국진단_20260923'
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20260923)

# ① 체험·문화 변화율 (사후검증 패널 재사용: 시군 월별 체험문화·방문)
pan = pd.read_csv('data/external/사후검증_패널/시군_월별_체험문화_방문.csv')
pan['연'] = pan['연월'] // 100
p18 = pan[(pan['연월'] % 100) <= 8].groupby(['시군', '연'])[['체험문화', '방문']].sum()
e = (p18['체험문화'] / p18['방문']).unstack()
I1 = pd.DataFrame({'체험문화_2024': e[2024], '체험문화_2026': e[2026], '방문_2026': p18['방문'].unstack()[2026]})
I1 = I1[(I1['체험문화_2024'] > 0) & (I1['방문_2026'] >= 1_000_000)]
I1['①체험문화_변화율'] = I1['체험문화_2026'] / I1['체험문화_2024'] - 1

# ② 평균 숙박일수 2025
l = pd.read_csv('data/api_region/월별_숙박비율_평균숙박일수_LN_02_01_013.csv')
l = l[l.BASE_YM // 100 == 2025]
l['시군'] = l['SGG_NM'].str.split().str[-1]
dup = l.groupby('시군')['SGG_NM'].nunique()
l = l[l['시군'].isin(dup[dup == 1].index)]
I2 = l.groupby('시군')['AVG_LODG_DAYS'].mean().rename('②평균숙박일수')

# ③④ 시간대 (D1 2026 1~8월)
parts = []
for ch in pd.read_csv('data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_2026.csv', chunksize=3_000_000,
                      usecols=['R:기초단체', 'R:기준연월', 'C:방문자유형별', 'C:시간대', 'V:방문자 수']):
    ch = ch[(ch['C:방문자유형별'] == '외지인(b)') & ch['C:시간대'].notna() & ((ch['R:기준연월'] % 100) <= 8)]
    parts.append(ch.groupby(['R:기초단체', 'C:시간대'])['V:방문자 수'].sum())
h = pd.concat(parts).groupby(level=[0, 1]).sum().unstack()
day = h[['06~11시', '11~14시', '14~18시', '18~21시', '21~24시']].sum(axis=1)
I34 = pd.DataFrame({'③저녁전환율': h['18~21시'] / h['14~18시'], '④야간방문비중': h['21~24시'] / day})

T = I1.join(I2, how='inner').join(I34, how='inner')
T = T[T.index.str.endswith(('시', '군'))]                                  # 광역시 자치구 제외(시·군 비교)
IND = ['①체험문화_변화율', '②평균숙박일수', '③저녁전환율', '④야간방문비중']
for c in IND:
    T[c + '_문제백분위'] = (1 - T[c].rank(pct=True)) * 100                  # 낮을수록 문제 → 높은 문제 백분위
PC = [c + '_문제백분위' for c in IND]
T['진단점수'] = T[PC].mean(axis=1)
T['순위'] = T['진단점수'].rank(ascending=False, method='min').astype(int)
T['유형'] = T[PC].apply(lambda r: ' · '.join(n.split('_')[0][1:] for n, v in zip(IND, r) if v >= 75) or '-', axis=1)

# 가중치 민감도
W = rng.dirichlet(np.ones(4), 1000)
ranks = np.array([pd.Series(T[PC].values @ w, index=T.index).rank(ascending=False, method='min').values for w in W])
T['순위_P10'] = np.percentile(ranks, 10, axis=0).astype(int)
T['순위_P90'] = np.percentile(ranks, 90, axis=0).astype(int)
T['상위20_비율'] = (ranks <= 20).mean(axis=0)
T = T.sort_values('순위')
T.to_csv(f'{OUT}/전국진단표.csv', encoding='utf-8-sig')

a = T.loc['안동시']
R = {'대상수': int(len(T)), '안동': {k: (float(a[k]) if not isinstance(a[k], str) else a[k]) for k in T.columns},
     '중앙값': {c: float(T[c].median()) for c in IND},
     '유형분포': T['유형'].value_counts().head(12).to_dict(),
     '안동과_같은_유형': T[T['유형'] == a['유형']].index.tolist(),
     '상위20': T.head(20)[IND + ['진단점수', '순위_P10', '순위_P90', '유형']].round(3).reset_index().to_dict('records'),
     '민감도_안동': {'P10': int(a['순위_P10']), 'P90': int(a['순위_P90'])},
     '순위안정_상위10': T[T['순위_P90'] <= 20].index.tolist()}
json.dump(R, open(f'{OUT}/전국진단.json', 'w'), ensure_ascii=False, indent=1, default=float)

print('대상', len(T), '안동 순위', int(a['순위']), f"(가중치 흔들면 {int(a['순위_P10'])}~{int(a['순위_P90'])}위)", '유형', a['유형'])
for c in IND:
    print(f"  {c}: 안동 {a[c]:.3f} / 중앙 {T[c].median():.3f} / 문제 백분위 {a[c + '_문제백분위']:.0f}")
print('같은 유형', R['안동과_같은_유형'][:15])
print(T.head(15)[IND + ['진단점수', '순위_P10', '순위_P90', '유형']].round(3).to_string())
print('유형 분포', R['유형분포'])

# 그림: 네 지표에서 안동의 위치
plt.rcParams.update({'font.family': 'NanumGothic', 'axes.unicode_minus': False, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'axes.edgecolor': '#999999', 'font.size': 9})
RED, GRAY = '#D64541', '#BFBFBF'
lab = {'①체험문화_변화율': '① 방문당 체험·문화 소비 변화율 (2024→2026, 1~8월)', '②평균숙박일수': '② 평균 숙박일수 (2025)',
       '③저녁전환율': '③ 저녁 전환율 (18~21시 ÷ 14~18시)', '④야간방문비중': '④ 야간 방문 비중 (21~24시)'}
fmt = {'①체험문화_변화율': lambda v: f'{v * 100:+.1f}%', '②평균숙박일수': lambda v: f'{v:.2f}일', '③저녁전환율': lambda v: f'{v:.3f}', '④야간방문비중': lambda v: f'{v * 100:.1f}%'}
fig, axs = plt.subplots(4, 1, figsize=(9, 4.2))
for ax, c in zip(axs, IND):
    v = T[c].clip(T[c].quantile(.02), T[c].quantile(.98))
    ax.scatter(v, rng.uniform(-.3, .3, len(v)), s=8, color=GRAY, alpha=.7, linewidths=0)
    ax.axvline(T[c].median(), color='#666', lw=.8, ls='--')
    ax.scatter([a[c]], [0], s=60, color=RED, zorder=3)
    ax.text(a[c], .42, f"안동 {fmt[c](a[c])} (문제 백분위 {a[c + '_문제백분위']:.0f})", color=RED, ha='center', fontsize=8.3)
    ax.set_yticks([]); ax.set_ylim(-.5, .75)
    ax.set_title(lab[c], loc='left', fontsize=9, pad=2)
    ax.tick_params(axis='x', labelsize=7.5)
    if c == '①체험문화_변화율':
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f'{x * 100:.0f}%'))
    if c == '④야간방문비중':
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f'{x * 100:.0f}%'))
fig.tight_layout(h_pad=.6)
fig.savefig(f'{OUT}/g8_안동위치.png', dpi=200, bbox_inches='tight', facecolor='white'); plt.close(fig)
