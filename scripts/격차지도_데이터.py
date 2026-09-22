"""GIS 지도용 데이터: 시군 경계 단순화 + 현지 관광소비 모델 결과 JSON"""
import json, re, io, contextlib, importlib.util
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "보고서/관광소비_기대치_모델_20260917"
spec = importlib.util.spec_from_file_location("m", ROOT / "scripts/관광소비_모델_업종분해.py")
m = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(m)
P, G = m.P, m.G
local = G["외식"] + G["숙박"] + G["레저·체험"]
X = m.design(P); y = np.log(local / P.방문)
Xa, ya = X.values.astype(float), y.values
loo = np.array([LinearRegression().fit(np.delete(Xa, i, 0), np.delete(ya, i)).predict(Xa[i:i+1])[0] for i in range(len(ya))])
fit = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HC3")
gap = (np.exp(ya - loo) - 1) * 100
rank = pd.Series(gap, index=P.index).rank().astype(int)
Z = X[m.CONT]; Z = (Z - Z.mean()) / Z.std()
PV = G.div(P.방문, axis=0)
regions = {}
for i, r in enumerate(P.index):
    peers = ((Z - Z.loc[r]) ** 2).sum(axis=1).drop(r).nsmallest(15).index
    regions[r] = {
        "sido": P.loc[r, "권역"], "visits": round(P.loc[r, "방문"] / 1e4, 1),
        "actual": round(float(np.exp(ya[i]))), "pred": round(float(np.exp(loo[i]))), "gap": round(float(gap[i]), 1), "rank": int(rank[r]),
        "stayRatio": round(P.loc[r, "숙박객비중"], 1), "night": round(P.loc[r, "야간비중"], 1), "weekend": round(P.loc[r, "주말비중"], 1), "metro": round(P.loc[r, "수도권비중"], 1),
        "cat": {k: [round(PV.loc[r, k]), round(PV.loc[peers, k].mean())] for k in ["외식", "숙박", "레저·체험", "기타쇼핑·뷰티", "대형쇼핑·면세", "운송"]},
        "peers": list(peers),
    }
meta = {"n": len(P), "cvR2": 0.589, "mape": 19.9, "baseMape": 32.3,
        "stayCoef": round(float(fit.params["숙박객비중"]) * 100, 1), "stayLo": round(float(fit.conf_int().loc["숙박객비중", 0]) * 100, 1), "stayHi": round(float(fit.conf_int().loc["숙박객비중", 1]) * 100, 1),
        "stayTimeP": round(float(fit.pvalues["log체류시간"]), 2)}

SIDO = {"11": "서울", "21": "부산", "22": "대구", "23": "인천", "24": "광주", "25": "대전", "26": "울산", "29": "세종", "31": "경기", "32": "강원", "33": "충북", "34": "충남", "35": "전북", "36": "전남", "37": "경북", "38": "경남", "39": "제주"}

def dp(pts, eps):
    if len(pts) < 3: return pts
    a, b = np.array(pts[0]), np.array(pts[-1]); ab = b - a; L = np.hypot(*ab)
    P_ = np.array(pts[1:-1])
    d = np.abs(ab[0] * (P_[:, 1] - a[1]) - ab[1] * (P_[:, 0] - a[0])) / L if L > 0 else np.hypot(*(P_ - a).T)
    k = int(np.argmax(d))
    if d[k] > eps:
        return dp(pts[:k + 2], eps)[:-1] + dp(pts[k + 1:], eps)
    return [pts[0], pts[-1]]

def area(r):
    x, y_ = np.array(r).T; return 0.5 * abs(np.dot(x, np.roll(y_, 1)) - np.dot(y_, np.roll(x, 1)))

import sys; sys.setrecursionlimit(10000)
g = json.load(open(ROOT / "data/external/경계/skorea-municipalities-2018-geo.json"))
feats = []
for f in g["features"]:
    nm, code = f["properties"]["name"], f["properties"]["code"]
    mm = re.match(r"^(.+?시)(.+구)$", nm)
    key = mm.group(1) if mm else nm
    polys = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
    rings = []
    for poly in polys:
        outer = poly[0]
        if area(outer) < 2e-5: continue
        s = dp([tuple(p) for p in outer], 0.004)
        if len(s) >= 4:
            rings.append([v for p in s for v in (round(p[0], 3), round(p[1], 3))])
    if not rings:
        big = max((p[0] for p in polys), key=area)
        s = dp([tuple(p) for p in big], 0.002)
        rings.append([v for p in s for v in (round(p[0], 3), round(p[1], 3))])
    feats.append({"n": nm, "k": key, "s": SIDO.get(code[:2], ""), "r": rings})
data = {"meta": meta, "regions": regions, "features": feats}
s = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
(OUT / "격차지도_데이터.json").write_text(s)
print(len(s) / 1e6, "MB", len(feats), "features", sum(f["k"] in regions for f in feats), "matched polys", len({f["k"] for f in feats} & set(regions)), "matched regions of", len(regions))
print(sorted(set(regions) - {f["k"] for f in feats}))
print(meta)
