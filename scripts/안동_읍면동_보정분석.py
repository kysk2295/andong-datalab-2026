#!/usr/bin/env python3
"""2차 보정: 비관광 급감 지역(풍산읍·용상동) 제외 지수, 관광권역 vs 도심 비교, 월별 차트."""
import pathlib, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont("/System/Library/Fonts/AppleSDGothicNeo.ttc")
plt.rcParams.update({"font.family": "Apple SD Gothic Neo", "axes.unicode_minus": False, "figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})
pd.set_option("display.width", 250)
R = pathlib.Path("/Users/koyunseo/한국관광데이터분석"); O = R / "보고서/안동교통"
z = pd.read_csv(R / "data/api_region/읍면동별_외지인_기간별_BDT_01_01_005_1.csv", encoding="utf-8-sig", dtype={"Q_SGG_CD": str})
z = z[z.PERIOD.str.len() == 4]; z["y"] = z.PERIOD.astype(int)
GRP = {"47170": {"관광권역": ["풍천면", "도산면", "서후면", "와룡면", "임하면", "길안면", "남후면", "예안면", "녹전면", "임동면"],
                 "도심": ["중구동", "서구동", "명륜동", "태화동", "평화동", "안기동", "강남동", "옥동", "송하동"],
                 "비관광 급감": ["풍산읍", "용상동"]},
       "47130": {"관광권역": ["황남동", "불국동", "보덕동", "월성동", "양북면", "문무대왕면", "감포읍", "양남면", "산내면", "내남면"],
                 "도심": ["중부동", "황오동", "성건동", "동천동", "황성동", "용강동", "선도동"]},
       "47210": {"관광권역": ["풍기읍", "부석면", "순흥면", "단산면", "봉현면", "문수면"],
                 "도심": ["하망동", "영주1동", "영주2동", "가흥1동", "가흥2동", "휴천1동", "휴천2동", "휴천3동", "상망동"]}}
NM = {"47170": "안동", "47130": "경주", "47210": "영주"}
rows = {}
for cd, g in GRP.items():
    a = z[z.Q_SGG_CD == cd].pivot_table(index="AREA_NM", columns="y", values="TOU_NUM", aggfunc="sum").fillna(0)
    tot = a.sum()
    rows[(NM[cd], "읍면동 합계")] = tot
    if cd == "47170": rows[(NM[cd], "합계(풍산·용상 제외)")] = tot - a.loc[g["비관광 급감"]].sum()
    for k, lst in g.items(): rows[(NM[cd], k)] = a.reindex(lst).fillna(0).sum()
t = pd.DataFrame(rows).T
ix = (t.div(t[2019], axis=0) * 100).round(1)
print(ix.to_string()); ix.to_csv(O / "30_읍면동그룹_지수_2019=100.csv", encoding="utf-8-sig")
print((t / 1e4).round(0).to_string())

# 관광권역 방문 대비 카드 소비 (전환 효율)
c = pd.read_csv(R / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_BDT_02_01_003_35.csv", encoding="utf-8-sig")
c = c[c.SGG_NM.isin(["안동시", "경주시", "영주시"]) & (c.KTO_TOB_MCLS_NM == "관광총소비")]
c["y"] = c.BASE_DATE // 100
cc = c[c.y <= 2025].groupby(["SGG_NM", "y"]).CNSM_AMT.sum().unstack()
cix = (cc.div(cc[2019], axis=0) * 100).round(1)
print("카드 관광총소비 지수"); print(cix.to_string())

d = pd.read_csv(R / "data/api_region/안동_읍면동별_외지인_월별_BDT_01_01_005_1.csv", encoding="utf-8-sig")
p = d.pivot_table(index="BASE_YM", columns="AREA_NM", values="TOU_NUM")
p.index = pd.to_datetime(p.index.astype(str), format="%Y%m")
s = pd.DataFrame({"풍산읍": p["풍산읍"], "용상동": p["용상동"],
                  "관광권역(풍천·도산 등 10개 면)": p[GRP["47170"]["관광권역"]].sum(1), "도심 9개 동": p[GRP["47170"]["도심"]].sum(1)})
r = s.rolling(12).mean(); r = r / r.loc["2019-12-01"] * 100
fig, ax = plt.subplots(figsize=(10, 4.4))
for col, cl, lw in zip(r.columns, ["#8d6a9f", "#b9a", "#d1495b", "#30638e"], [2, 1.2, 2.4, 2]):
    ax.plot(r.index, r[col], color=cl, lw=lw, label=col)
for x, lab in [("2021-01", "KTX-이음"), ("2024-12", "중앙선 전 구간")]:
    ax.axvline(pd.Timestamp(x), color="gray", ls="--", lw=1); ax.text(pd.Timestamp(x), 132, lab, fontsize=8, color="gray")
ax.axhline(100, color="#999", lw=.6); ax.set_ylim(45, 140)
ax.set_title("안동 읍면동 그룹별 외지인 방문 (12개월 이동평균, 2019=100)"); ax.legend(frameon=False, ncol=2, fontsize=9)
fig.tight_layout(); fig.savefig(O / "c12_읍면동그룹.png"); plt.close()
print("ok")
