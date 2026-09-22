"""관광소비 기대치 모델 (시·군 횡단면 다중회귀 + 2019→2025 변화량 모델)

Y  = log(외지인 방문당 카드소비)  카드 touDiv1 관광총소비 ÷ D1 외지인 방문 연인원
X  = 이동통신 기반 조건 (체류·숙박객 비중·야간·주말·수도권 유입·방문 규모) + 군/권역 통제
카드 소비로 만든 비율은 X에서 제외한다(순환 방지).

실행: .venv_pdf/bin/python scripts/관광소비_기대치_모델.py
"""
from pathlib import Path
import re
import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "보고서/관광소비_기대치_모델_20260917"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "_cache"
CACHE.mkdir(exist_ok=True)
con = duckdb.connect()

NIGHT = ("21~24시", "00~06시")
WEEKEND = ("토요일", "일요일")


def d1(year: int) -> pd.DataFrame:
    """외지인 방문 연인원, 야간 비중, 주말 비중 (시간대가 있는 행 기준)."""
    p = CACHE / f"d1_{year}.csv"
    if p.exists():
        return pd.read_csv(p, index_col=0)
    f = ROOT / f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv"
    df = con.sql(f"""
        SELECT "R:기초단체" region,
               SUM("V:방문자 수") visits,
               SUM(CASE WHEN "C:시간대" IN {NIGHT} THEN "V:방문자 수" ELSE 0 END) night,
               SUM(CASE WHEN "C:요일" IN {WEEKEND} THEN "V:방문자 수" ELSE 0 END) weekend
        FROM read_csv_auto('{f}')
        WHERE "C:방문자유형별"='외지인(b)' AND "C:시간대" IS NOT NULL
        GROUP BY 1""").df().set_index("region")
    df["야간비중"] = df.night / df.visits * 100
    df["주말비중"] = df.weekend / df.visits * 100
    df.to_csv(p)
    return df


def card(year: int) -> pd.Series:
    files = {2019: "2019·2020·2025", 2025: "2019·2020·2025"}
    c = pd.read_csv(ROOT / f"data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_{files[year]}_BDT_02_01_003_35.csv").drop_duplicates()
    c = c[(c.BASE_DATE // 100 == year) & (c.KTO_TOB_MCLS_NM == "관광총소비")]
    months = c.groupby("SGG_NM").BASE_DATE.nunique()
    dup = c.groupby(["SGG_NM", "BASE_DATE"]).size()
    dup_names = set(dup[dup > 1].index.get_level_values(0))
    s = c.groupby("SGG_NM").CNSM_AMT.sum() * 1000  # 천원 → 원
    return s[(months == 12) & ~s.index.isin(dup_names)]


stay_raw = pd.read_csv(ROOT / "data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv")
stay_raw = stay_raw[stay_raw["C:방문자유형별"] == "외지인(b)"]
SIDO = stay_raw.groupby("R:기초단체")["R:광역단체"].agg(lambda s: s.mode()[0])
dup_stay = stay_raw.groupby("R:기초단체")["R:광역단체"].nunique()
DUP = set(dup_stay[dup_stay > 1].index)


def stay(year: int) -> pd.DataFrame:
    s = stay_raw[stay_raw["R:기준연월"] // 100 == year].copy()
    s["숙"] = np.where(s["C:숙박일수"] == "무박", 0, s["V:관광객수"])
    g = s.groupby("R:기초단체")[["V:관광객수", "V:숙박체류시간", "숙"]].sum()
    return pd.DataFrame({"체류시간": g["V:숙박체류시간"] / g["V:관광객수"],
                         "숙박객비중": g["숙"] / g["V:관광객수"] * 100})


inflow = pd.read_csv(ROOT / "data/api_region/유입권역비중_전국_연도별_LN_03_01_053.csv")
inflow["region"] = inflow.SGG_NM.str.split().str[-1]
dup_in = inflow.groupby("region").SGG_CD.nunique()
DUP |= set(dup_in[dup_in > 1].index)


def metro(year: int) -> pd.Series:
    x = inflow[inflow.PERIOD == year]
    return x.groupby("region")["수도권"].first()


REGION_GROUP = {"서울특별시": "수도권", "인천광역시": "수도권", "경기도": "수도권",
                "강원특별자치도": "강원", "강원도": "강원",
                "대전광역시": "충청", "세종특별자치시": "충청", "충청북도": "충청", "충청남도": "충청",
                "광주광역시": "호남", "전북특별자치도": "호남", "전라북도": "호남", "전라남도": "호남",
                "대구광역시": "대경", "경상북도": "대경",
                "부산광역시": "동남", "울산광역시": "동남", "경상남도": "동남",
                "제주특별자치도": "제주"}


def panel(year: int) -> pd.DataFrame:
    v, c, s, m = d1(year), card(year), stay(year), metro(year)
    idx = sorted(set(v.index) & set(c.index) & set(s.index) & set(m.index))
    idx = [r for r in idx if re.fullmatch(r"[^ ]+(시|군)", r) and r not in DUP]
    D = pd.DataFrame(index=idx)
    D["방문"] = v.visits
    D["소비"] = c
    D["방문당소비"] = D.소비 / D.방문
    D["야간비중"] = v.야간비중
    D["주말비중"] = v.주말비중
    D = D.join(s).join(m.rename("수도권비중"))
    D["권역"] = SIDO.reindex(D.index).map(REGION_GROUP)
    D["군"] = D.index.str.endswith("군").astype(int)
    return D.dropna()


P25 = panel(2025)
P19 = panel(2019)
P25.to_csv(OUT / "모델_입력표_2025.csv", encoding="utf-8-sig")

CONT = ["log체류시간", "숙박객비중", "야간비중", "주말비중", "수도권비중", "log방문"]


def design(D: pd.DataFrame, cont=CONT):
    X = pd.DataFrame(index=D.index)
    X["log체류시간"] = np.log(D.체류시간)
    X["log방문"] = np.log(D.방문)
    for k in ["숙박객비중", "야간비중", "주말비중", "수도권비중"]:
        X[k] = D[k]
    X = X[cont]
    X["군"] = D.군
    X = X.join(pd.get_dummies(D.권역, prefix="권역", drop_first=True, dtype=float))
    return X, np.log(D.방문당소비)


# ---------- 1. 횡단면 OLS ----------
X, y = design(P25)
ols = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HC3")
coef = pd.DataFrame({"계수": ols.params, "하한95": ols.conf_int()[0], "상한95": ols.conf_int()[1], "p값": ols.pvalues})
Xz = X.copy()
for k in CONT:
    Xz[k] = (X[k] - X[k].mean()) / X[k].std()
olsz = sm.OLS(y, sm.add_constant(Xz)).fit(cov_type="HC3")
coef["표준화계수"] = olsz.params
coef["표준화_하한95"] = olsz.conf_int()[0]
coef["표준화_상한95"] = olsz.conf_int()[1]
coef.round(4).to_csv(OUT / "회귀계수_2025.csv", encoding="utf-8-sig")
vif = pd.Series([variance_inflation_factor(sm.add_constant(X[CONT]).values, i + 1) for i in range(len(CONT))], index=CONT, name="VIF")
vif.round(2).to_csv(OUT / "VIF_2025.csv", encoding="utf-8-sig")

# ---------- 2. 교차검증 (5-겹 × 20회) ----------
Xa, ya = X.values.astype(float), y.values
spv = P25.방문당소비.values
rows = []
for rep in range(20):
    kf = KFold(5, shuffle=True, random_state=rep)
    pred = {"평균예측": np.zeros(len(ya)), "다중회귀": np.zeros(len(ya)), "랜덤포레스트": np.zeros(len(ya))}
    for tr, te in kf.split(Xa):
        pred["평균예측"][te] = ya[tr].mean()
        pred["다중회귀"][te] = LinearRegression().fit(Xa[tr], ya[tr]).predict(Xa[te])
        pred["랜덤포레스트"][te] = RandomForestRegressor(300, min_samples_leaf=3, random_state=rep, n_jobs=-1).fit(Xa[tr], ya[tr]).predict(Xa[te])
    for k, p in pred.items():
        ss = ((ya - p) ** 2).sum()
        rows.append({"모델": k, "회차": rep, "R2": 1 - ss / ((ya - ya.mean()) ** 2).sum(),
                     "MAE_원": np.abs(spv - np.exp(p)).mean(), "MAPE_%": np.mean(np.abs(spv - np.exp(p)) / spv) * 100})
cv = pd.DataFrame(rows).groupby("모델")[["R2", "MAE_원", "MAPE_%"]].agg(["mean", "std"]).round(3)
cv.to_csv(OUT / "교차검증_성능.csv", encoding="utf-8-sig")

# ---------- 3. 지역별 표본 외 잔차 (LOO) ----------
loo = np.zeros(len(ya))
for i in range(len(ya)):
    m = np.ones(len(ya), bool); m[i] = False
    loo[i] = LinearRegression().fit(Xa[m], ya[m]).predict(Xa[i:i + 1])[0]
res = P25[["방문", "방문당소비", "체류시간", "숙박객비중", "야간비중", "주말비중", "수도권비중", "권역"]].copy()
res["예측_방문당소비"] = np.exp(loo)
res["격차_%"] = (res.방문당소비 / res.예측_방문당소비 - 1) * 100
res["격차_순위(낮은순)"] = res["격차_%"].rank().astype(int)
res = res.sort_values("격차_%")
res.round(2).to_csv(OUT / "지역별_조건대비_격차_2025.csv", encoding="utf-8-sig")

# ---------- 4. 2019→2025 변화량 모델 ----------
common = P19.index.intersection(P25.index)
dX = pd.DataFrame(index=common)
dX["Δlog체류시간"] = np.log(P25.loc[common, "체류시간"]) - np.log(P19.loc[common, "체류시간"])
for k in ["숙박객비중", "야간비중", "주말비중", "수도권비중"]:
    dX["Δ" + k] = P25.loc[common, k] - P19.loc[common, k]
dX["Δlog방문"] = np.log(P25.loc[common, "방문"]) - np.log(P19.loc[common, "방문"])
dX["군"] = P25.loc[common, "군"]
dX = dX.join(pd.get_dummies(P25.loc[common, "권역"], prefix="권역", drop_first=True, dtype=float))
dy = np.log(P25.loc[common, "방문당소비"]) - np.log(P19.loc[common, "방문당소비"])
fd = sm.OLS(dy, sm.add_constant(dX)).fit(cov_type="HC3")
pd.DataFrame({"계수": fd.params, "하한95": fd.conf_int()[0], "상한95": fd.conf_int()[1], "p값": fd.pvalues}).round(4).to_csv(OUT / "변화량모델_계수_2019-2025.csv", encoding="utf-8-sig")

# ---------- 5. 민감도 ----------
sens = []
def run(name, D, cont=CONT):
    Xs, ys = design(D, cont)
    f = sm.OLS(ys, sm.add_constant(Xs)).fit(cov_type="HC3")
    r = {"조건": name, "표본": len(D), "adjR2": f.rsquared_adj}
    for k in cont:
        r[k] = f.params[k]; r[k + "_p"] = f.pvalues[k]
    if "안동시" in D.index:
        Xa_, ya_ = Xs.values.astype(float), ys.values
        i = list(D.index).index("안동시"); m = np.ones(len(ya_), bool); m[i] = False
        r["안동_격차_%"] = (np.exp(ya_[i] - LinearRegression().fit(Xa_[m], ya_[m]).predict(Xa_[i:i + 1])[0]) - 1) * 100
    sens.append(r)
run("기본(2025)", P25)
run("2019 기준", P19)
run("군 제외(시만)", P25[P25.군 == 0])
run("방문 500만 이상", P25[P25.방문 >= 5e6])
run("주말비중 제외", P25, [c for c in CONT if c != "주말비중"])
run("수도권 권역 제외", P25[P25.권역 != "수도권"])
pd.DataFrame(sens).round(4).to_csv(OUT / "민감도.csv", encoding="utf-8-sig")

with open(OUT / "요약.txt", "w") as fp:
    fp.write(f"표본 2025: {len(P25)} / 2019: {len(P19)} / 변화량: {len(common)}\n\n")
    fp.write(ols.summary().as_text() + "\n\nVIF\n" + vif.round(2).to_string() + "\n\n")
    fp.write("교차검증\n" + cv.to_string() + "\n\n")
    fp.write(fd.summary().as_text() + "\n")
print(open(OUT / "요약.txt").read())
print(pd.DataFrame(sens).round(3).T)
keys = ["안동시", "경주시", "전주시", "군산시", "포항시", "영주시", "익산시", "인제군", "태안군", "충주시", "홍천군"]
print(res.reindex([k for k in keys if k in res.index]).round(2))
print(P25.loc["안동시"] if "안동시" in P25.index else "안동 없음")
