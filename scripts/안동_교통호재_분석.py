#!/usr/bin/env python3
"""안동(메인) + 경주·포항·전주·군산 — 교통 호재(KTX-이음 2021.01 / 중앙선 전 구간 2024.12) 전후 관광 변화 분석.
로컬 수집 데이터만 사용 (API 재호출 없음).
실행: .venv_pdf/bin/python scripts/안동_교통호재_분석.py
출력: 보고서/안동교통/*.csv, *.png  + 표준출력 요약
"""
import pathlib, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

warnings.filterwarnings("ignore")
ROOT = pathlib.Path("/Users/koyunseo/한국관광데이터분석")
D, OUT = ROOT / "data", ROOT / "보고서" / "안동교통"
OUT.mkdir(parents=True, exist_ok=True)
XTAB = pathlib.Path("/private/tmp/claude-501/-Users-koyunseo----------/777ba665-d962-4860-8b1c-5d8f6f95dcd7/scratchpad/xtab5.csv")

fm.fontManager.addfont("/System/Library/Fonts/AppleSDGothicNeo.ttc")
plt.rcParams.update({"font.family": "Apple SD Gothic Neo", "axes.unicode_minus": False,
                     "figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})

CITY = {"안동": [47170], "경주": [47130], "포항": [47111, 47113], "전주": [52111, 52113], "군산": [52130]}
CITYNM = {"안동": ["안동시"], "경주": ["경주시"], "포항": ["포항시 남구", "포항시 북구"],
          "전주": ["전주시 완산구", "전주시 덕진구"], "군산": ["군산시"]}
COL = {"안동": "#d1495b", "경주": "#edae49", "포항": "#00798c", "전주": "#30638e", "군산": "#8d6a9f"}
ORDER = list(CITY)
pd.set_option("display.width", 220, "display.max_columns", 40)


def L(f):
    return pd.read_csv(D / "api_region" / f, encoding="utf-8-sig")


def city_of_code(cd):
    for k, v in CITY.items():
        if cd in v:
            return k


def save(df, name):
    df.to_csv(OUT / f"{name}.csv", encoding="utf-8-sig")
    print(f"\n### {name}\n{df.round(2).to_string()}")


def vlines(ax):
    for x, lab in [("2021-01", "KTX-이음\n청량리-안동"), ("2024-12", "중앙선\n전 구간")]:
        ax.axvline(pd.Timestamp(x), color="gray", ls="--", lw=1)
        ax.text(pd.Timestamp(x), ax.get_ylim()[1], lab, fontsize=8, va="top", ha="left", color="gray")


# ─────────────────────────── 1. 외지인 방문자수 (월별, 전 시군구) ───────────────────────────
v = L("월별_방문자수_외지인_LN_03_01_002.csv")
v = v[v.SGG_CD.astype(str).str.len() == 5]
v["ym"] = pd.to_datetime(v.BASE_YM.astype(str), format="%Y%m")
v["y"] = v.ym.dt.year
# 시(구 합산) — 구 합산 시 시 내부 구간 이동이 이중계상될 수 있어 '규모'가 아닌 '변화율' 해석용
v["city"] = v.SGG_CD.map(city_of_code)
cv = v.dropna(subset=["city"]).groupby(["city", "ym"]).TOU_NUM.sum().unstack(0)[ORDER]
cv.to_csv(OUT / "01_월별_외지인방문자.csv", encoding="utf-8-sig")

yr = cv[cv.index < "2026-01"].groupby(cv[cv.index < "2026-01"].index.year).sum()
save((yr / 1e4).round(0), "01_연도별_외지인방문자_만명")
save((yr / yr.loc[2019] * 100), "01_연도별_외지인방문자_2019=100")

# 전국 시군구 대비 순위 (Diff-in-Diff 식 비교: 2019 대비 증감률의 전국 분포 내 위치)
sg = v[v.y <= 2025].groupby(["SGG_CD", "y"]).TOU_NUM.sum().unstack()
sg = sg[(sg[2019] > 0)]
rel = sg.div(sg[2019], axis=0) * 100
rows = []
for c in ORDER:
    s = sg.loc[[x for x in CITY[c] if x in sg.index]].sum()
    r = s / s[2019] * 100
    rows.append({"도시": c, **{f"{y}": r[y] for y in [2020, 2021, 2022, 2023, 2024, 2025]},
                 **{f"{y}_전국백분위": (rel[y] < r[y]).mean() * 100 for y in [2021, 2022, 2023, 2025]}})
rows.append({"도시": "전국 시군구 중앙값", **{f"{y}": rel[y].median() for y in [2020, 2021, 2022, 2023, 2024, 2025]}})
gb = v[(v.SGG_CD // 1000 == 47) & (v.y <= 2025)].groupby(["SGG_CD", "y"]).TOU_NUM.sum().unstack()
gbr = gb.div(gb[2019], axis=0) * 100
rows.append({"도시": "경북 시군 중앙값", **{f"{y}": gbr[y].median() for y in [2020, 2021, 2022, 2023, 2024, 2025]}})
save(pd.DataFrame(rows).set_index("도시"), "02_2019대비_방문자지수_전국비교")

# 중앙선 전 구간(2024.12) 전후: 1~8월 동기간 비교
def jan_aug(df, y):
    return df[(df.index.year == y) & (df.index.month <= 8)].sum()
e = pd.DataFrame({"2024(1-8월)": jan_aug(cv, 2024), "2025(1-8월)": jan_aug(cv, 2025), "2026(1-8월)": jan_aug(cv, 2026)})
e["25/24 %"] = (e["2025(1-8월)"] / e["2024(1-8월)"] - 1) * 100
e["26/24 %"] = (e["2026(1-8월)"] / e["2024(1-8월)"] - 1) * 100
nat = v[v.ym.dt.month <= 8].groupby(["SGG_CD", "y"]).TOU_NUM.sum().unstack()
e.loc["전국 시군구 중앙값", ["25/24 %", "26/24 %"]] = [((nat[2025] / nat[2024] - 1) * 100).median(),
                                                ((nat[2026] / nat[2024] - 1) * 100).median()]
save(e, "03_중앙선전구간_전후_방문자_1-8월")

# ─────────────────────────── 2. 숙박방문자 비율 / 평균숙박일수 ───────────────────────────
s = L("월별_숙박비율_평균숙박일수_LN_02_01_013.csv")
s["ym"] = pd.to_datetime(s.BASE_YM.astype(str), format="%Y%m")
s["city"] = s.SGG_CD.map(city_of_code)
s = s.merge(v[["SGG_CD", "ym", "TOU_NUM"]], on=["SGG_CD", "ym"], how="left")
s["w"] = s.TOU_NUM.fillna(1)
cs = s.dropna(subset=["city"])
lr = cs.groupby(["city", "ym"]).apply(lambda g: np.average(g.LODG_TOU_NUM_RATE, weights=g.w)).unstack(0)[ORDER]
ld = cs.groupby(["city", "ym"]).apply(lambda g: np.average(g.AVG_LODG_DAYS, weights=g.w)).unstack(0)[ORDER]
lr.to_csv(OUT / "04_월별_숙박방문자비율.csv", encoding="utf-8-sig")
lry = lr.groupby(lr.index.year).mean()
s["y"] = s.ym.dt.year
natl = s.groupby("y").LODG_TOU_NUM_RATE.median()
lry["전국 시군구 중앙값"] = natl
save(lry, "04_연도별_숙박방문자비율_%")
save(ld.groupby(ld.index.year).mean(), "05_연도별_평균숙박일수")

# 숙박비율 × 방문자 → '숙박 방문자 수' vs '당일 방문자 수' 분해 (KTX 이후 증가분이 어디로 갔나)
ov = (cv * lr / 100)
dt = cv - ov
yy = lambda d: d[d.index < "2026-01"].groupby(d[d.index < "2026-01"].index.year).sum()
dec = pd.DataFrame({f"{c}_숙박방문자(만)": yy(ov)[c] / 1e4 for c in ORDER} | {f"{c}_당일방문자(만)": yy(dt)[c] / 1e4 for c in ORDER})
save(dec[[f"{c}_{k}" for c in ORDER for k in ["숙박방문자(만)", "당일방문자(만)"]]], "06_숙박vs당일_방문자분해")
g = pd.DataFrame({c: {"당일 증감(2019→2025,%)": (yy(dt)[c][2025] / yy(dt)[c][2019] - 1) * 100,
                      "숙박 증감(2019→2025,%)": (yy(ov)[c][2025] / yy(ov)[c][2019] - 1) * 100,
                      "당일 증감(2019→2023,%)": (yy(dt)[c][2023] / yy(dt)[c][2019] - 1) * 100,
                      "숙박 증감(2019→2023,%)": (yy(ov)[c][2023] / yy(ov)[c][2019] - 1) * 100} for c in ORDER}).T
save(g, "06b_당일vs숙박_증감률")

# 숙박유형(전체기간)
t = L("숙박유형별_방문자_LN_02_01_011.csv")
t["city"] = t.SGG_CD.map(city_of_code)
tt = t.dropna(subset=["city"]).groupby(["city", "LODG_NM"]).TOU_NUM.sum().unstack(0)[ORDER]
tt = tt.reindex(["무박", "1박", "2박", "3박", "4박", "5박", "6박", "7박이상"])
save(tt / tt.sum() * 100, "07_숙박유형_구성비_전체기간_%")

# ─────────────────────────── 3. 요일·시간대·연령 (이동통신 교차표) ───────────────────────────
x = pd.read_csv(XTAB, encoding="utf-8-sig")
x.columns = ["sgg", "sido", "ym", "type", "sex", "age", "dow", "tm", "n"]
x["city"] = x.sgg.map({n: c for c, ns in CITYNM.items() for n in ns})
x["y"] = x.ym // 100
xo = x[(x.type == "외지인(b)") & (x.y <= 2025)]
tot = xo.groupby(["city", "y"]).n.sum()
wk = xo[xo.dow.isin(["토요일", "일요일"])].groupby(["city", "y"]).n.sum() / tot * 100
fri = xo[xo.dow == "금요일"].groupby(["city", "y"]).n.sum() / tot * 100
night = xo[xo.tm.isin(["21~24시", "00~06시"])].groupby(["city", "y"]).n.sum() / tot * 100
save(wk.unstack(0)[ORDER], "08_외지인_주말(토일)비중_%")
save(fri.unstack(0)[ORDER], "08b_외지인_금요일비중_%")
save(night.unstack(0)[ORDER], "09_외지인_야간(21-06시)체류비중_%")
# 주말 야간(토 00~06시 = 금요일밤 숙박, 일 00~06 = 토요일밤 숙박) 비중
sat_night = xo[(xo.dow.isin(["토요일", "일요일"])) & (xo.tm == "00~06시")].groupby(["city", "y"]).n.sum() / \
            xo[xo.dow.isin(["토요일", "일요일"])].groupby(["city", "y"]).n.sum() * 100
save(sat_night.unstack(0)[ORDER], "09b_주말_새벽(00-06시)체류비중_%")
tmd = xo[xo.city == "안동"].groupby(["y", "tm"]).n.sum().unstack()
save(tmd.div(tmd.sum(1), axis=0) * 100, "09c_안동_시간대별_외지인분포_%")
age = xo.groupby(["city", "y", "age"]).n.sum()
age = age / age.groupby(["city", "y"]).transform("sum") * 100
a2030 = age[age.index.get_level_values(2).isin(["20~29세", "30~39세"])].groupby(["city", "y"]).sum().unstack(0)[ORDER]
a60 = age[age.index.get_level_values(2).isin(["60~69세", "70세 이상"])].groupby(["city", "y"]).sum().unstack(0)[ORDER]
save(a2030, "10_외지인_2030비중_%")
save(a60, "10b_외지인_60대이상비중_%")
save(age.loc["안동"].unstack(), "10c_안동_연령구성_연도별_%")
# 월별 주말비중 (KTX 개통 전후 12개월)
xm = x[x.type == "외지인(b)"]
wkm = (xm[xm.dow.isin(["토요일", "일요일"])].groupby(["city", "ym"]).n.sum() / xm.groupby(["city", "ym"]).n.sum() * 100).unstack(0)[ORDER]
wkm.index = pd.to_datetime(wkm.index.astype(str), format="%Y%m")
wkm.to_csv(OUT / "08c_월별_주말비중.csv", encoding="utf-8-sig")

# ─────────────────────────── 4. 숙박일수별 관광객 (이동통신) ───────────────────────────
n = pd.read_csv(D / "bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv", encoding="utf-8-sig")
n.columns = ["sgg", "sido", "ym", "nights", "type", "tou", "lodg", "stay_tm"]
n["city"] = n.sgg.map({nm: c for c, ns in CITYNM.items() for nm in ns})
n["y"] = n.ym // 100
nn = n[(n.type == "외지인(b)") & n.city.notna() & (n.y <= 2025)]
nt = nn.groupby(["city", "y", "nights"]).tou.sum().unstack()
one = (nt["1박"] / nt.sum(1) * 100).unstack(0)[ORDER]
save(one, "11_숙박관광객중_1박비중_%")
save((nt.sum(1) / 1e4).unstack(0)[ORDER], "11b_숙박관광객수_만명")
fn = n[(n.type == "외국인(c)") & n.city.notna() & (n.y <= 2025)].groupby(["city", "y"]).tou.sum().unstack(0)[ORDER]
save(fn, "11c_외국인_숙박관광객수")

# ─────────────────────────── 5. 신용카드 외지인 관광소비 ───────────────────────────
c = pd.read_csv(D / "bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_BDT_02_01_003_35.csv", encoding="utf-8-sig")
cm = {"안동시": "안동", "경주시": "경주", "포항시": "포항", "전주시": "전주", "군산시": "군산"}
c = c[c.SGG_NM.isin(cm)].copy()
c["city"] = c.SGG_NM.map(cm)
c["y"] = c.BASE_DATE // 100
c = c[c.y <= 2025]
GRP = {"숙박": ["호텔", "캠핑장/펜션", "기타숙박", "콘도"], "식음료": ["일반외식업", "제과음료업"],
       "여가·문화": ["관광유원시설", "기타레저", "문화서비스"], "골프": ["골프장"], "쇼핑": ["대형쇼핑몰", "레저용품쇼핑", "기타관광쇼핑", "면세점"],
       "운송": ["육상운송", "렌터카", "수상운송", "항공운송"]}
tot_c = c[c.KTO_TOB_MCLS_NM == "관광총소비"].groupby(["city", "y"]).CNSM_AMT.sum()
save((tot_c / 1e5).unstack(0)[ORDER].round(0), "12_외지인관광소비_억원")  # 단위: 천원 → 억원
share = {}
for k, items in GRP.items():
    share[k] = c[c.KTO_TOB_MCLS_NM.isin(items)].groupby(["city", "y"]).CNSM_AMT.sum() / tot_c * 100
sh = pd.DataFrame(share)
save(sh.xs(2025, level="y").loc[ORDER], "13_업종구성_2025_%")
save(sh["숙박"].unstack(0)[ORDER], "13b_숙박업비중_연도별_%")
save(sh["여가·문화"].unstack(0)[ORDER], "13c_여가문화비중_연도별_%")
save(sh["운송"].unstack(0)[ORDER], "13d_운송비중_연도별_%")
det = c[(c.city == "안동") & (c.KTO_TOB_MCLS_NM != "관광총소비")].groupby(["y", "KTO_TOB_MCLS_NM"]).CNSM_AMT.sum().unstack()
save((det.div(det.sum(1), axis=0) * 100).T.sort_values(2025, ascending=False), "13e_안동_세부업종구성_%")
# 방문자 1인당 카드소비(원) = 외지인 관광소비 / 외지인 방문자수
pc = (tot_c.unstack(0)[ORDER] * 1000) / yr.loc[2018:2025]
save(pc.round(0), "14_외지인1인당관광소비_원")
# 중앙선 전 구간 전후 (1~8월)
c2 = pd.read_csv(D / "bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_BDT_02_01_003_35.csv", encoding="utf-8-sig")
c2 = c2[c2.SGG_NM.isin(cm)]
c2["city"] = c2.SGG_NM.map(cm); c2["y"] = c2.BASE_DATE // 100; c2["m"] = c2.BASE_DATE % 100
c2 = c2[c2.m <= 8]
q = {}
for yv in [2024, 2025, 2026]:
    tt_ = c2[(c2.y == yv) & (c2.KTO_TOB_MCLS_NM == "관광총소비")].groupby("city").CNSM_AMT.sum()
    ll_ = c2[(c2.y == yv) & c2.KTO_TOB_MCLS_NM.isin(GRP["숙박"])].groupby("city").CNSM_AMT.sum()
    q[f"총소비{yv}(억)"] = tt_ / 1e5
    q[f"숙박비중{yv}%"] = ll_ / tt_ * 100
q = pd.DataFrame(q).loc[ORDER]
q["총소비 25/24 %"] = (q["총소비2025(억)"] / q["총소비2024(억)"] - 1) * 100
q["총소비 26/24 %"] = (q["총소비2026(억)"] / q["총소비2024(억)"] - 1) * 100
for yv in [2024, 2025, 2026]:
    q[f"1인당{yv}(원)"] = q[f"총소비{yv}(억)"] * 1e8 / e.loc[ORDER, f"{yv}(1-8월)"]
q["1인당 26/24 %"] = (q["1인당2026(원)"] / q["1인당2024(원)"] - 1) * 100
q["1인당 25/24 %"] = (q["1인당2025(원)"] / q["1인당2024(원)"] - 1) * 100
save(q, "15_중앙선전구간_전후_카드소비_1-8월")

# ─────────────────────────── 6. 내비게이션 목적지 검색 ───────────────────────────
nv = pd.read_csv(D / "bdt/내비게이션/시군구별_검색건수_연도별_BDT_03_01_003_1.csv", encoding="utf-8-sig")
nv["city"] = nv.SGG_CD.map(lambda cd: {47110: "포항", 52110: "전주"}.get(cd) or city_of_code(cd))
print("내비 SGG:", nv[nv.city.notna()].groupby("city").SGG_CD.unique().to_dict())
nvy = nv.dropna(subset=["city"]).groupby(["city", "_YEAR"]).SRCH_CNT.sum().unstack(0)[ORDER]
save(nvy / 1e4, "16_내비목적지검색_만건")
save(nvy / nvy.loc[2019] * 100, "16b_내비검색_2019=100")

# ─────────────────────────── 7. 외국인 방문자 (SKT) ───────────────────────────
f = pd.read_csv(D / "bdt/이동통신/외국인방문자_월별시계열_SKT_BDT_SKT_FRG_01_01_003.csv", encoding="utf-8-sig")
f = f[f._조회_시군구 == f.SIDO_NM]
f["city"] = f.SIDO_NM.map({nm: c for c, ns in CITYNM.items() for nm in ns})
f["y"] = f.BASE_DATE // 100
fy = f.dropna(subset=["city"])[lambda d: d.y <= 2025].groupby(["city", "y"]).TOU_NUM.sum().unstack(0)[ORDER]
save(fy / 1e4, "17_외국인방문자_만명")

# ─────────────────────────── 8. 유입지(출발지) 분포 — 기간합 ───────────────────────────
u = L("유입지_분포_LN_03_01_053.csv")
u["city"] = u.SGG_CD.map(city_of_code)
uo = u.dropna(subset=["city"]).drop_duplicates(["SGG_CD", "DPTR_REGN_NM"])
uo = uo.groupby(["city", "DPTR_REGN_NM"]).TOU_NUM.sum()
uo = (uo / uo.groupby("city").transform("sum") * 100).unstack(0)[ORDER]
reg = {"수도권": ["서울특별시", "경기도", "인천광역시"], "부울경": ["부산광역시", "울산광역시", "경상남도"],
       "대구·경북": ["대구광역시", "경상북도"], "호남": ["광주광역시", "전라남도", "전북특별자치도"],
       "충청·대전·세종": ["대전광역시", "세종특별자치시", "충청남도", "충청북도"], "강원": ["강원특별자치도"]}
ug = pd.DataFrame({k: uo.reindex(vv).sum() for k, vv in reg.items()}).T
save(ug, "18_유입권역_구성비_%(기간합,동일시군구포함)")
ud = u[u.SGG_CD == 47170].sort_values("DTL_TOU_NUM", ascending=False)[["DPTR_REGN_NM", "DPTR_REGN_DTL_NM", "DTL_TOU_NUM", "DTL_TOU_NUM_RATE"]].head(15)
save(ud.set_index("DPTR_REGN_DTL_NM"), "18b_안동_유입_상위시군구")

# ─────────────────────────── 9. 안동 읍면동 방문 분포 ───────────────────────────
z = pd.read_csv(D / "bdt/이동통신/시군구_주변지역_방문자수_BDT_01_01_005_1_외지인b.csv", encoding="utf-8-sig")
z = z[z._조회_시군구 == "안동시"].sort_values("TOU_NUM", ascending=False)
z["비중%"] = z.TOU_NUM / z.TOU_NUM.sum() * 100
save(z.set_index("AREA_NM")[["TOU_NUM", "비중%"]].head(15), "19_안동_읍면동별_외지인방문")

# ─────────────────────────── 10. 관광진단지수 / 소비비중 / 검색 ───────────────────────────
dg = L("관광진단지수_LN_04_01_001.csv")
dg["city"] = dg.SGG_CD.map(city_of_code)
save(dg.dropna(subset=["city"]).pivot_table(index=["city", "SGG_NM"], columns="TURSM_DNS_DIV_NM", values="TURSM_DNS_DIV_VAL"), "20_관광진단지수_전국순위")
ms = L("검색_중분류별_LN_03_01_065.csv")
ms["city"] = ms.SGG_CD.map(city_of_code)
ms = ms.dropna(subset=["city"]).groupby(["city", "MCLS_NM"]).SRCH_CNT.sum()
save((ms / ms.groupby("city").transform("sum") * 100).unstack(0)[ORDER], "21_목적지검색_중분류구성_%")

# ─────────────────────────── 차트 ───────────────────────────
def roll(d):
    return d.rolling(12, min_periods=12).sum()

fig, ax = plt.subplots(figsize=(10, 4.6))
r12 = roll(cv)
for k in ORDER:
    ax.plot(r12.index, r12[k] / r12[k]["2019-12-01"] * 100, color=COL[k], lw=2.4 if k == "안동" else 1.3, label=k)
ax.axhline(100, color="#999", lw=.6); vlines(ax)
ax.set_title("외지인 방문자수 12개월 누적 (2019년=100)"); ax.legend(ncol=5, frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig(OUT / "c1_방문자지수.png"); plt.close()

fig, ax = plt.subplots(figsize=(10, 4.6))
lr12 = lr.rolling(12, min_periods=12).mean()
for k in ORDER:
    ax.plot(lr12.index, lr12[k], color=COL[k], lw=2.4 if k == "안동" else 1.3, label=k)
vlines(ax); ax.set_title("숙박방문자 비율 (12개월 이동평균, %)"); ax.legend(ncol=5, frameon=False)
fig.tight_layout(); fig.savefig(OUT / "c2_숙박비율.png"); plt.close()

fig, ax = plt.subplots(figsize=(10, 4.6))
a_dt, a_ov = roll(dt["안동"]) / 1e4, roll(ov["안동"]) / 1e4
ax.fill_between(a_dt.index, 0, a_dt, color="#f4a261", label="당일 방문자")
ax.fill_between(a_ov.index, a_dt, a_dt + a_ov, color="#264653", label="숙박 방문자")
vlines(ax); ax.set_title("안동 외지인 방문자 — 당일 vs 숙박 (12개월 누적, 만 명)"); ax.legend(frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig(OUT / "c3_안동_당일vs숙박.png"); plt.close()

fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
for k in ORDER:
    axs[0].plot(wk.unstack(0).index, wk.unstack(0)[k], marker="o", color=COL[k], lw=2.4 if k == "안동" else 1.2, label=k)
    axs[1].plot(night.unstack(0).index, night.unstack(0)[k], marker="o", color=COL[k], lw=2.4 if k == "안동" else 1.2, label=k)
axs[0].set_title("외지인 중 주말(토·일) 비중 %"); axs[1].set_title("외지인 중 야간(21~06시) 체류 비중 %")
axs[0].legend(frameon=False, fontsize=8)
for a in axs: a.axvline(2021, color="gray", ls="--", lw=1); a.axvline(2024.95, color="gray", ls="--", lw=1)
fig.tight_layout(); fig.savefig(OUT / "c4_주말_야간.png"); plt.close()

fig, ax = plt.subplots(figsize=(9, 4.2))
s25 = sh.xs(2025, level="y").loc[ORDER][["식음료", "숙박", "여가·문화", "골프", "쇼핑", "운송"]]
s25.plot.barh(stacked=True, ax=ax, color=["#e76f51", "#264653", "#2a9d8f", "#8ab17d", "#e9c46a", "#999"])
ax.invert_yaxis(); ax.set_title("외지인 카드 관광소비 업종 구성 (2025, %)"); ax.legend(ncol=6, frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(.5, -.28))
fig.tight_layout(); fig.savefig(OUT / "c5_업종구성.png"); plt.close()

fig, ax = plt.subplots(figsize=(10, 4.2))
for k in ORDER:
    ax.plot(pc.index, pc[k], marker="o", color=COL[k], lw=2.4 if k == "안동" else 1.2, label=k)
ax.axvline(2021, color="gray", ls="--", lw=1)
ax.set_title("외지인 1인(방문)당 카드 관광소비 (원)"); ax.legend(ncol=5, frameon=False)
fig.tight_layout(); fig.savefig(OUT / "c6_1인당소비.png"); plt.close()
print("\nDONE ->", OUT)
