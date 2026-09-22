"""기대치 모델 2차: (1) 쇼핑·운송을 뺀 소비로 재추정 (2) 격차 큰 후보 지역의 업종별 분해

입력: 보고서/관광소비_기대치_모델_20260917/모델_입력표_2025.csv (1차 스크립트 산출)
실행: .venv_pdf/bin/python scripts/관광소비_모델_업종분해.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "보고서/관광소비_기대치_모델_20260917"
P = pd.read_csv(OUT / "모델_입력표_2025.csv", index_col=0)

c = pd.read_csv(ROOT / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv").drop_duplicates()
c = c[c.BASE_DATE // 100 == 2025]
W = c.pivot_table(index="SGG_NM", columns="KTO_TOB_MCLS_NM", values="CNSM_AMT", aggfunc="sum").fillna(0) * 1000
W = W.reindex(P.index)

GROUP = {
    "외식": ["일반외식업", "제과음료업"],
    "대형쇼핑·면세": ["대형쇼핑몰", "면세점"],
    "기타쇼핑·뷰티": ["기타관광쇼핑", "레저용품쇼핑", "뷰티"],
    "운송": ["육상운송", "항공운송", "수상운송", "렌터카"],
    "숙박": ["호텔", "기타숙박", "콘도", "캠핑장/펜션"],
    "레저·체험": ["문화서비스", "관광유원시설", "기타레저", "골프장", "스키장", "여행업"],
}
G = pd.DataFrame({k: W[v].sum(1) for k, v in GROUP.items()})
assert np.allclose(G.sum(1), W["관광총소비"], rtol=1e-6)

Y = {
    "총소비": W["관광총소비"],
    "대형쇼핑·면세 제외": W["관광총소비"] - G["대형쇼핑·면세"],
    "쇼핑·운송 제외(현지 관광소비)": G["외식"] + G["숙박"] + G["레저·체험"],
}
CONT = ["log체류시간", "숙박객비중", "야간비중", "주말비중", "수도권비중", "log방문"]


def design(D):
    X = pd.DataFrame(index=D.index)
    X["log체류시간"] = np.log(D.체류시간)
    X["log방문"] = np.log(D.방문)
    for k in ["숙박객비중", "야간비중", "주말비중", "수도권비중"]:
        X[k] = D[k]
    X = X[CONT]
    X["군"] = D.군
    return X.join(pd.get_dummies(D.권역, prefix="권역", drop_first=True, dtype=float))


rows, coefs, gaps = [], [], {}
for name, spend in Y.items():
    D = P.copy()
    D["y"] = np.log(spend / D.방문)
    X = design(D)
    f = sm.OLS(D.y, sm.add_constant(X)).fit(cov_type="HC3")
    for k in CONT:
        coefs.append({"Y": name, "변수": k, "계수": f.params[k], "하한95": f.conf_int().loc[k, 0], "상한95": f.conf_int().loc[k, 1], "p값": f.pvalues[k]})
    Xa, ya = X.values.astype(float), D.y.values
    r2, mape = [], []
    for rep in range(20):
        p = np.zeros(len(ya)); b = np.zeros(len(ya))
        for tr, te in KFold(5, shuffle=True, random_state=rep).split(Xa):
            p[te] = LinearRegression().fit(Xa[tr], ya[tr]).predict(Xa[te]); b[te] = ya[tr].mean()
        r2.append(1 - ((ya - p) ** 2).sum() / ((ya - ya.mean()) ** 2).sum())
        mape.append(np.mean(np.abs(np.exp(ya) - np.exp(p)) / np.exp(ya)) * 100)
        if rep == 0:
            base_mape = np.mean(np.abs(np.exp(ya) - np.exp(b)) / np.exp(ya)) * 100
    loo = np.array([LinearRegression().fit(np.delete(Xa, i, 0), np.delete(ya, i)).predict(Xa[i:i + 1])[0] for i in range(len(ya))])
    gaps[name] = pd.Series((np.exp(ya - loo) - 1) * 100, index=D.index)
    rows.append({"Y": name, "adjR2": f.rsquared_adj, "CV_R2": np.mean(r2), "CV_MAPE_%": np.mean(mape), "평균예측_MAPE_%": base_mape,
                 "Y_중앙값_원": np.exp(ya).mean() if False else np.median(np.exp(ya)), "안동_격차_%": gaps[name]["안동시"]})

perf = pd.DataFrame(rows).round(3)
coef = pd.DataFrame(coefs).round(4)
gap = pd.DataFrame(gaps).round(1)
gap["순위_현지관광(낮은순)"] = gap["쇼핑·운송 제외(현지 관광소비)"].rank().astype(int)
perf.to_csv(OUT / "2차_Y별_성능.csv", index=False, encoding="utf-8-sig")
coef.to_csv(OUT / "2차_Y별_계수.csv", index=False, encoding="utf-8-sig")
gap.sort_values("쇼핑·운송 제외(현지 관광소비)").to_csv(OUT / "2차_Y별_지역격차.csv", encoding="utf-8-sig")

# ---------- 업종 분해: 조건이 가장 비슷한 15곳과 비교 ----------
Z = design(P)[CONT]
Z = (Z - Z.mean()) / Z.std()
PV = G.div(P.방문, axis=0)  # 업종별 방문당 소비(원)
TARGETS = ["안동시", "익산시", "경주시", "인제군", "태안군", "영주시"]
dec = []
for t in TARGETS:
    d = ((Z - Z.loc[t]) ** 2).sum(1).drop(t).nsmallest(15)
    peers = d.index
    for g in GROUP:
        dec.append({"지역": t, "업종": g, "지역_방문당(원)": PV.loc[t, g], "유사15곳_평균(원)": PV.loc[peers, g].mean(),
                    "차이(원)": PV.loc[t, g] - PV.loc[peers, g].mean()})
    dec.append({"지역": t, "업종": "합계", "지역_방문당(원)": PV.loc[t].sum(), "유사15곳_평균(원)": PV.loc[peers].sum(1).mean(),
                "차이(원)": PV.loc[t].sum() - PV.loc[peers].sum(1).mean()})
    dec.append({"지역": t, "업종": "비교지역", "지역_방문당(원)": np.nan, "유사15곳_평균(원)": np.nan, "차이(원)": np.nan, "비교지역": ", ".join(peers)})
DEC = pd.DataFrame(dec)
DEC.round(0).to_csv(OUT / "2차_업종분해_유사15곳.csv", index=False, encoding="utf-8-sig")

pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
print(perf.to_string())
print(coef.pivot(index="변수", columns="Y", values="계수").round(3))
print(coef.pivot(index="변수", columns="Y", values="p값").round(3))
print(gap.reindex(["안동시", "익산시", "경주시", "인제군", "태안군", "영주시", "충주시", "홍천군", "군산시", "여주시", "과천시"]))
print(gap.sort_values("쇼핑·운송 제외(현지 관광소비)").head(12))
for t in TARGETS:
    x = DEC[DEC.지역 == t]
    print("\n", t, x[x.업종 == "비교지역"]["비교지역"].values[0])
    print(x[x.업종 != "비교지역"][["업종", "지역_방문당(원)", "유사15곳_평균(원)", "차이(원)"]].round(0).to_string(index=False))
print("\n안동 업종별 방문당", PV.loc["안동시"].round(0).to_dict())
