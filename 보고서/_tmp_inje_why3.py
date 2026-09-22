from pathlib import Path
import pandas as pd
import numpy as np

root = Path("/Users/koyunseo/한국관광데이터분석")
card_files = [
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv",
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv",
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv",
]
card = pd.concat([pd.read_csv(f).drop_duplicates() for f in card_files], ignore_index=True).drop_duplicates()
card = card[card.SGG_NM=="인제군"].copy()
card["year"] = card.BASE_DATE // 100
card["month"] = card.BASE_DATE % 100
card = card[card.month<=8]

# monthly total spend
tot = card[card.KTO_TOB_MCLS_NM=="관광총소비"][["year","month","CNSM_AMT"]].drop_duplicates()
tot["spend"]=tot.CNSM_AMT*1000
pv = tot.pivot(index="month", columns="year", values="spend")
print("MONTHLY SPEND")
print(pv.to_string())

# join visits from previous ytd monthly if we recompute from csv monthly_방문소비
mon = pd.read_csv(root/"보고서/지역주제_재탐색_20260917/월별_방문소비.csv")
im = mon[mon.region=="인제군"].copy()
print("monthly file years", im.year.unique(), "cols", im.columns.tolist())
im = im[im.month<=8]
imp = im.pivot(index="month", columns="year", values=["visits","spend"])
print(imp.to_string())

# SPV by month
for y in [2024,2025,2026]:
    sub=im[im.year==y]
    print(y, "spv", (sub.spend.sum()/sub.visits.sum()))

wide=[]
for m in range(1,9):
    row={"month":m}
    for y in [2024,2025,2026]:
        s=im[(im.year==y)&(im.month==m)].iloc[0]
        row[f"v{y}"]=s.visits
        row[f"s{y}"]=s.spend
        row[f"spv{y}"]=s.spend/s.visits
    wide.append(row)
w=pd.DataFrame(wide)
w["v_yoy"]= (w.v2026/w.v2025-1)*100
w["s_yoy"]= (w.s2026/w.s2025-1)*100
w["spv_yoy"]=(w.spv2026/w.spv2025-1)*100
w["visit_share_of_increase"]=(w.v2026-w.v2025)/(w.v2026.sum()-w.v2025.sum())*100
# contribution to SPV change: accounting
# SPV26-SPV25 = mix + intensity
print("MONTH TABLE")
print(w.to_string(index=False))

# How much of SPV drop is mix vs within-month intensity
spv25 = w.s2025.sum()/w.v2025.sum()
spv26 = w.s2026.sum()/w.v2026.sum()
# counterfactual: 2026 visit mix with 2025 month SPV
cf_spend = (w.v2026 * w.spv2025).sum()
cf_spv = cf_spend / w.v2026.sum()
print("SPV25", spv25, "SPV26", spv26, "change", (spv26/spv25-1)*100)
print("2026 mix x 2025 monthly SPV =>", cf_spv, "vs actual 26", spv26)
print("mix effect % of old", (cf_spv/spv25-1)*100)
print("within-month intensity", (spv26/cf_spv-1)*100)

# industry 25 vs 26
ind = card[card.KTO_TOB_MCLS_NM!="관광총소비"].groupby(["year","KTO_TOB_MCLS_NM"], as_index=False)["CNSM_AMT"].sum()
p=ind.pivot(index="KTO_TOB_MCLS_NM", columns="year", values="CNSM_AMT")
p=p[[2024,2025,2026]]
p["yoy26"]=(p[2026]/p[2025]-1)*100
p["share25"]=p[2025]/p[2025].sum()*100
p["share26"]=p[2026]/p[2026].sum()*100
p["delta"]=p[2026]-p[2025]
print("INDUSTRY")
print(p.sort_values("yoy26").to_string())
print("total spend 천원", p[2025].sum(), p[2026].sum(), (p[2026].sum()/p[2025].sum()-1)*100)

# stay data if exists
stay = pd.read_csv(root/"data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1_202608추가.csv", nrows=5)
print("STAY COLS", stay.columns.tolist())
print(stay.head())
