#!/usr/bin/env python3
"""합성통제(Synthetic Control): 'KTX-이음이 없었다면'의 안동을 전국 시·군 가중조합으로 만들어 실제와 비교.
결과변수: 월별 외지인 방문자수 / 2019년 월평균 (지수). 사전기간 2018.01~2020.12 (코로나 충격 포함 → 충격 민감도까지 매칭)
공여군: 특별·광역시 자치구 제외 시·군 중, 중앙선 KTX-이음 정차 도시(원주·제천·단양·영주·의성·영천·경주·안동) 제외.
추론: 공여군 각 지역을 가짜 처치로 놓은 placebo 검정 → 사후/사전 RMSPE 비율 순위로 p값.
"""
import pathlib, numpy as np, pandas as pd
from scipy.optimize import nnls
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/System/Library/Fonts/AppleSDGothicNeo.ttc")
plt.rcParams.update({"font.family": "Apple SD Gothic Neo", "axes.unicode_minus": False, "figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})
R = pathlib.Path("/Users/koyunseo/한국관광데이터분석"); O = R / "보고서/안동교통"
v = pd.read_csv(R / "data/api_region/월별_방문자수_외지인_LN_03_01_002.csv", encoding="utf-8-sig")
v = v[v.SGG_CD.astype(str).str.len() == 5]
p = v.pivot_table(index="BASE_YM", columns="SGG_CD", values="TOU_NUM").sort_index()
p = p.loc[:, (p.loc[201801:201912] > 0).all()]
idx = p / p.loc[201901:201912].mean() * 100
metro = {11, 26, 27, 28, 29, 30, 31}
corridor = {42130, 43150, 43800, 47210, 47730, 47230, 47130, 47170}
donors = [c for c in idx.columns if c // 1000 not in metro and c not in corridor and idx[c].notna().all()]
pre = idx.index[(idx.index >= 201801) & (idx.index <= 202012)]
post = idx.index[idx.index >= 202101]

def synth(target, pool):
    X = idx.loc[pre, pool].values; y = idx.loc[pre, target].values
    lam = 1e3  # sum-to-one 제약을 벌점 행으로
    A = np.vstack([X, lam * np.ones(len(pool))]); b = np.append(y, lam)
    w, _ = nnls(A, b)
    return pd.Series(w, index=pool)

def run(target, pool):
    w = synth(target, pool)
    s = idx[pool] @ w
    gap = idx[target] - s
    rm_pre = np.sqrt((gap.loc[pre] ** 2).mean()); rm_post = np.sqrt((gap.loc[post] ** 2).mean())
    return w, s, gap, rm_pre, rm_post

w, s, gap, rp, rq = run(47170, donors)
names = v.drop_duplicates("SGG_CD").set_index("SGG_CD").SGG_NM
top = w[w > 0.01].sort_values(ascending=False)
print("합성 안동 구성:"); print(pd.DataFrame({"지역": names.reindex(top.index), "가중치": top.round(3)}).to_string())
print(f"사전 RMSPE {rp:.2f}  사후 RMSPE {rq:.2f}  비율 {rq/rp:.1f}")
yr = lambda d: d.groupby(d.index // 100).mean()
res = pd.DataFrame({"실제 안동": yr(idx[47170]), "합성 안동": yr(s), "격차(지수p)": yr(gap)}).loc[2018:2026]
res["격차율%"] = res["격차(지수p)"] / res["합성 안동"] * 100
print(res.round(1).to_string())
# 연간 방문자 수로 환산한 '잃어버린 방문'
base = p.loc[201901:201912, 47170].mean()
lost = (gap.loc[post] * base / 100)
lostY = lost.groupby(lost.index // 100).sum() / 1e4
print("합성 대비 부족 방문(만 명/년):", lostY.round(0).to_dict(), " 누적:", round(lost.sum() / 1e4))
res.to_csv(O / "24_합성통제_연도별.csv", encoding="utf-8-sig")
top.rename(index=names).to_csv(O / "24b_합성통제_가중치.csv", encoding="utf-8-sig")

# placebo
ratios = {}
for c in donors:
    pool = [d for d in donors if d != c]
    _, _, g2, a, b = run(c, pool)
    if a > 0: ratios[c] = b / a
rt = pd.Series(ratios)
rank = (rt >= rq / rp).sum() + 1
print(f"placebo: 공여군 {len(rt)}곳 중 안동의 RMSPE비율 순위 {rank} → p≈{rank/(len(rt)+1):.3f}")
# 사전 적합이 좋은 placebo만 (사전 RMSPE ≤ 2×안동)
good = []
for c in donors:
    pool = [d for d in donors if d != c]
    _, _, g2, a, b = run(c, pool)
    if a <= 2 * rp: good.append((c, g2))
fig, ax = plt.subplots(figsize=(10, 4.4))
t = pd.to_datetime(idx.index.astype(str), format="%Y%m")
for c, g2 in good: ax.plot(t, g2.values, color="#ccc", lw=.5)
ax.plot(t, gap.values, color="#d1495b", lw=2.4, label="안동 (실제 - 합성)")
ax.axvline(pd.Timestamp("2021-01"), color="gray", ls="--"); ax.axvline(pd.Timestamp("2024-12"), color="gray", ls="--")
ax.axhline(0, color="#333", lw=.8); ax.set_ylim(-45, 45)
ax.set_title(f"합성통제 격차 — 회색: placebo {len(good)}개 지역, 안동 p≈{rank/(len(rt)+1):.2f}"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(O / "c10_합성통제_placebo.png"); plt.close()
fig, ax = plt.subplots(figsize=(10, 4.4))
r12 = lambda d: d.rolling(12).mean()
ax.plot(t, r12(idx[47170]).values, color="#d1495b", lw=2.4, label="실제 안동")
ax.plot(t, r12(s).values, color="#30638e", lw=2, ls="--", label="합성 안동 (KTX 없었다면)")
ax.axvline(pd.Timestamp("2021-01"), color="gray", ls="--"); ax.axvline(pd.Timestamp("2024-12"), color="gray", ls="--")
ax.set_title("외지인 방문 지수 (2019=100, 12개월 이동평균)"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(O / "c11_합성통제.png"); plt.close()
