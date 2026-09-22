from pathlib import Path
import duckdb
import pandas as pd

root = Path("/Users/koyunseo/한국관광데이터분석")
con = duckdb.connect()
con.execute("SET threads=4")
years = list(range(2021, 2027))
vframes = []
for year in years:
    f = str(root / f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv")
    df = con.execute(
        """
        SELECT CAST("R:기준연월" // 100 AS INTEGER) AS year,
               CAST("R:기준연월" % 100 AS INTEGER) AS month,
               SUM("V:방문자 수") AS visits
        FROM read_csv_auto(?)
        WHERE "R:기초단체" = '인제군'
          AND "C:방문자유형별" = '외지인(b)'
          AND "C:시간대" IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 2
        """,
        [f],
    ).df()
    print("VISIT", year, "months", df.month.tolist(), "sum", float(df.visits.sum()) if len(df) else 0)
    vframes.append(df)
vis = pd.concat(vframes, ignore_index=True)

card_files = [
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv",
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv",
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv",
]
cards = []
for cf in card_files:
    d = pd.read_csv(cf).drop_duplicates()
    d = d[d["SGG_NM"] == "인제군"]
    cards.append(d)
card = pd.concat(cards, ignore_index=True).drop_duplicates()
print("CARD COLS", list(card.columns))
print("CARD years", sorted((card.BASE_DATE // 100).unique().tolist()))

tot = card[card.KTO_TOB_MCLS_NM == "관광총소비"].copy()
tot["year"] = tot.BASE_DATE // 100
tot["month"] = tot.BASE_DATE % 100
tot["spend"] = tot.CNSM_AMT * 1000
print("dup months", tot.groupby(["year", "month"]).size().value_counts().to_dict())

def ytd(df, val, years=range(2021, 2027)):
    out = []
    for y in years:
        sub = df[(df.year == y) & (df.month <= 8)]
        out.append({"year": y, "months": int(sub.month.nunique()), val: float(sub[val].sum())})
    return pd.DataFrame(out)

tab = ytd(vis, "visits").merge(ytd(tot, "spend"), on="year")
tab["spend_per_visit"] = tab.spend / tab.visits
tab["visits_yoy"] = tab.visits.pct_change() * 100
tab["spend_yoy"] = tab.spend.pct_change() * 100
tab["spv_yoy"] = tab.spend_per_visit.pct_change() * 100
print("YTD JAN-AUG")
print(tab.to_string(index=False))

def full(df, val, years=range(2021, 2027)):
    out = []
    for y in years:
        sub = df[df.year == y]
        out.append({"year": y, "months": int(sub.month.nunique()), val: float(sub[val].sum())})
    return pd.DataFrame(out)

tabf = full(vis, "visits").merge(full(tot, "spend"), on="year")
tabf["spend_per_visit"] = tabf.spend / tabf.visits
print("FULL YEAR AVAILABLE")
print(tabf.to_string(index=False))

ind = card[card.KTO_TOB_MCLS_NM != "관광총소비"].copy()
ind["year"] = ind.BASE_DATE // 100
ind["month"] = ind.BASE_DATE % 100
ind = ind[ind.month <= 8]
g = ind.groupby(["year", "KTO_TOB_MCLS_NM"], as_index=False)["CNSM_AMT"].sum()
pv = g.pivot(index="KTO_TOB_MCLS_NM", columns="year", values="CNSM_AMT")
print("INDUSTRY JAN-AUG (천원)")
print(pv.to_string())
tab.to_csv("/tmp/inje_ytd.csv", index=False)
tabf.to_csv("/tmp/inje_full.csv", index=False)
pv.to_csv("/tmp/inje_ind.csv")
