#!/usr/bin/env python3
"""추가 차트: 권역별 방문 증감 / 개통 전후 월별 YoY / 1인당 소비 변화."""
import pathlib, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/System/Library/Fonts/AppleSDGothicNeo.ttc")
plt.rcParams.update({"font.family": "Apple SD Gothic Neo", "axes.unicode_minus": False, "figure.dpi": 130,
                     "axes.spines.top": False, "axes.spines.right": False})
R = pathlib.Path("/Users/koyunseo/한국관광데이터분석"); O = R / "보고서/안동교통"; D = R / "data/api_region"

r = pd.read_csv(O / "23b_권역별_증감률_2019-2025.csv", encoding="utf-8-sig", index_col=0)
cols = ["수도권", "충청권", "부울경", "대구", "경북"]; cities = ["안동", "영주", "제천", "단양", "경주", "포항", "전주", "군산"]
fig, ax = plt.subplots(figsize=(10, 4.4))
w = .16
for i, c in enumerate(cols):
    ax.bar([j + i * w for j in range(len(cities))], r.loc[cities, c], w, label=c,
           color=["#d1495b", "#edae49", "#00798c", "#30638e", "#8d6a9f"][i])
ax.axhline(0, color="#333", lw=.8); ax.set_xticks([j + 2 * w for j in range(len(cities))]); ax.set_xticklabels(cities)
ax.set_title("출발 권역별 외지인 방문 증감률 (2019→2025, %)  — 안동만 원거리 권역이 모두 감소"); ax.legend(ncol=5, frameon=False)
fig.tight_layout(); fig.savefig(O / "c7_권역별증감.png"); plt.close()

v = pd.read_csv(D / "월별_방문자수_외지인_LN_03_01_002.csv", encoding="utf-8-sig")
v = v[v.SGG_CD.astype(str).str.len() == 5]
p = v.pivot_table(index="SGG_CD", columns="BASE_YM", values="TOU_NUM")
yms = [c for c in p.columns if c >= 202001]
rows = []
for ym in yms:
    if ym - 100 in p.columns:
        y = (p[ym] / p[ym - 100] - 1) * 100
        rows.append((pd.Timestamp(str(ym) + "01"), y[47170] - y.median()))
g = pd.DataFrame(rows, columns=["ym", "gap"]).set_index("ym")
fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(g.index, g.gap, width=25, color=["#d1495b" if x > 0 else "#9aa" for x in g.gap])
for x, lab in [("2021-01", "KTX-이음 개통"), ("2024-12", "중앙선 전 구간")]:
    ax.axvline(pd.Timestamp(x), color="gray", ls="--", lw=1); ax.text(pd.Timestamp(x), ax.get_ylim()[1] * .9, lab, fontsize=8, color="gray")
ax.axhline(0, color="#333", lw=.8)
ax.set_title("안동 외지인 방문 전년동월비 - 전국 시군구 중앙값 (%p)  — 개통 특수는 2~3개월"); fig.tight_layout(); fig.savefig(O / "c8_월별초과성장.png"); plt.close()

q = pd.read_csv(O / "15_중앙선전구간_전후_카드소비_1-8월.csv", encoding="utf-8-sig", index_col=0)
e = pd.read_csv(O / "03_중앙선전구간_전후_방문자_1-8월.csv", encoding="utf-8-sig", index_col=0)
cc = ["안동", "경주", "포항", "전주", "군산"]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar([i - .2 for i in range(5)], e.loc[cc, "26/24 %"], .4, label="외지인 방문자", color="#30638e")
ax.bar([i + .2 for i in range(5)], q.loc[cc, "1인당 26/24 %"], .4, label="1인당 카드소비", color="#d1495b")
ax.axhline(0, color="#333", lw=.8); ax.set_xticks(range(5)); ax.set_xticklabels(cc)
for i, c in enumerate(cc):
    ax.text(i - .2, e.loc[c, "26/24 %"] + .4, f"{e.loc[c, '26/24 %']:+.1f}", ha="center", fontsize=8)
    ax.text(i + .2, q.loc[c, "1인당 26/24 %"] - 1.4, f"{q.loc[c, '1인당 26/24 %']:+.1f}", ha="center", fontsize=8)
ax.set_title("중앙선 전 구간 개통 전후 (2026 vs 2024, 1~8월, %)"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(O / "c9_개통전후_방문vs소비.png"); plt.close()
print("ok")
