#!/usr/bin/env python3
"""합성통제 강건성: (1) 안동 인접·생활권 시군(예천·영주·의성·청송·봉화·영양·문경·상주·예천) 제외 (2) 사전적합 양호 placebo만으로 p값
(3) 사전기간을 코로나 이전(2018.01~2019.12)으로 한정."""
import numpy as np, pandas as pd, pathlib
from scipy.optimize import nnls
R = pathlib.Path("/Users/koyunseo/한국관광데이터분석")
v = pd.read_csv(R / "data/api_region/월별_방문자수_외지인_LN_03_01_002.csv", encoding="utf-8-sig")
v = v[v.SGG_CD.astype(str).str.len() == 5]
p = v.pivot_table(index="BASE_YM", columns="SGG_CD", values="TOU_NUM").sort_index()
p = p.loc[:, (p.loc[201801:201912] > 0).all()]
idx = p / p.loc[201901:201912].mean() * 100
names = v.drop_duplicates("SGG_CD").set_index("SGG_CD").SGG_NM
metro = {11, 26, 27, 28, 29, 30, 31}
corridor = {42130, 43150, 43800, 47210, 47730, 47230, 47130, 47170}
near = {47900, 47730, 47750, 47920, 47760, 47280, 47250}
post = idx.index[idx.index >= 202101]
def run(target, pool, pre):
    X = idx.loc[pre, pool].values; y = idx.loc[pre, target].values
    w, _ = nnls(np.vstack([X, 1e3 * np.ones(len(pool))]), np.append(y, 1e3)); w = pd.Series(w, index=pool)
    gap = idx[target] - idx[pool] @ w
    return w, gap, np.sqrt((gap.loc[pre] ** 2).mean()), np.sqrt((gap.loc[post] ** 2).mean())
rows = []
for label, excl, pre in [("기본(사전 2018-2020)", set(), idx.index[idx.index <= 202012]),
                         ("인접·생활권 제외", near, idx.index[idx.index <= 202012]),
                         ("인접 제외 + 사전 2018-2019", near, idx.index[idx.index <= 201912])]:
    donors = [c for c in idx.columns if c // 1000 not in metro and c not in corridor | excl and idx[c].notna().all()]
    w, gap, a, b = run(47170, donors, pre)
    ratios, pres = {}, {}
    for c in donors:
        _, _, a2, b2 = run(c, [d for d in donors if d != c], pre)
        ratios[c], pres[c] = b2 / a2 if a2 > 0 else np.nan, a2
    rt, pr = pd.Series(ratios), pd.Series(pres)
    p_all = ((rt >= b / a).sum() + 1) / (len(rt) + 1)
    good = rt[pr <= 2 * a]
    p_good = ((good >= b / a).sum() + 1) / (len(good) + 1)
    # 사후 평균 격차 크기 기준 (단측: 음(-)의 격차가 더 큰 곳 비율)
    mg = {}
    for c in good.index:
        _, g2, _, _ = run(c, [d for d in donors if d != c], pre); mg[c] = g2.loc[202201:202512].mean()
    mg = pd.Series(mg); g_and = gap.loc[202201:202512].mean()
    p_neg = ((mg <= g_and).sum() + 1) / (len(mg) + 1)
    yr = gap.groupby(gap.index // 100).mean()
    top = w[w > .03].sort_values(ascending=False)
    rows.append({"설정": label, "공여군": len(donors), "사전RMSPE": round(a, 2), "사후RMSPE": round(b, 2),
                 "2022-25 평균격차(지수p)": round(g_and, 1), "2023 격차": round(yr[2023], 1), "2025 격차": round(yr[2025], 1),
                 "p(전체 placebo)": round(p_all, 3), "p(사전적합 양호)": round(p_good, 3), "p(음의 격차 단측)": round(p_neg, 3),
                 "주요 가중치": ", ".join(f"{names[i].split()[-1]} {w[i]:.2f}" for i in top.index)})
res = pd.DataFrame(rows).set_index("설정")
print(res.T.to_string())
res.to_csv(R / "보고서/안동교통/24c_합성통제_강건성.csv", encoding="utf-8-sig")
