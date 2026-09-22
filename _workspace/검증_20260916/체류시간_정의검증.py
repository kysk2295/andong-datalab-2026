import pandas as pd

src = 'data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv'
d = pd.read_csv(src)
d = d[d['C:방문자유형별'].astype(str).str.contains('외지인')]
d['연'] = d['R:기준연월'].astype(int) // 100
d = d[d['연'].isin([2019, 2025])]

lodging = d[d['C:숙박일수'] != '무박']
cands = {
    '숙박행 시간합/관광객합': lambda x: x['V:숙박체류시간'].sum() / x['V:관광객수'].sum(),
    '숙박행 시간합/숙박자합': lambda x: x['V:숙박체류시간'].sum() / x['V:숙박자수'].sum(),
    '숙박행 시간 단순평균': lambda x: x['V:숙박체류시간'].mean(),
}
base = lodging.groupby(['R:기초단체', '연']).apply(
    lambda x: x['V:숙박체류시간'].sum() / x['V:관광객수'].sum(), include_groups=False
).unstack().dropna()
base['변화율'] = (base[2025] / base[2019] - 1) * 100
print('안동 절대값 2019/2025', round(base.loc['안동시', 2019], 2), round(base.loc['안동시', 2025], 2))
for thr in [239, 150, 100]:
    print(f'표본 {thr} 기준 중앙값', round(base['변화율'].median(), 2))
    break
for name, fn in cands.items():
    g = lodging.groupby(['R:기초단체', '연']).apply(fn, include_groups=False).unstack().dropna()
    g['변화율'] = (g[2025] / g[2019] - 1) * 100
    a = g.loc['안동시', '변화율']
    print(f'[숙박만] {name}: n={len(g)} 안동={a:.2f}% 중앙값={g["변화율"].median():.2f}% 순위={(g["변화율"] < a).sum() + 1}')

defs = {
    '체류시간합/관광객수합': lambda x: x['V:숙박체류시간'].sum() / x['V:관광객수'].sum(),
    '체류시간합/숙박자수합': lambda x: x['V:숙박체류시간'].sum() / x['V:숙박자수'].sum(),
    '체류시간 단순평균': lambda x: x['V:숙박체류시간'].mean(),
    '1박행만 시간/관광객': lambda x: (x[x['C:숙박일수'] == '1박']['V:숙박체류시간'].sum()
                                  / x[x['C:숙박일수'] == '1박']['V:관광객수'].sum()),
}
for name, fn in defs.items():
    g = d.groupby(['R:기초단체', '연']).apply(fn, include_groups=False).unstack().dropna()
    g['변화율'] = (g[2025] / g[2019] - 1) * 100
    a = g.loc['안동시', '변화율']
    rank = (g['변화율'] < a).sum() + 1
    print(f'{name}: n={len(g)} 안동={a:.2f}% 중앙값={g["변화율"].median():.2f}% 순위={rank}')
