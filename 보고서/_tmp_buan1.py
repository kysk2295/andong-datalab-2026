import duckdb
import polars as pl
from pathlib import Path

root = Path("/Users/koyunseo/한국관광데이터분석")
out = Path("/tmp/buan_out")
out.mkdir(exist_ok=True)
con = duckdb.connect()
con.execute("SET threads=4")

REGIONS = ["부안군", "고창군", "태안군", "보령시", "서천군", "영광군", "인제군", "안동시"]
FOCUS = "부안군"

card_files = [
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv",
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv",
    root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv",
]
card = pl.concat([pl.read_csv(str(f)).unique() for f in card_files]).unique()
card = card.with_columns([
    (pl.col("BASE_DATE") // 100).alias("year"),
    (pl.col("BASE_DATE") % 100).alias("month"),
    (pl.col("CNSM_AMT") * 1000).alias("spend"),
])
print("CARD years", sorted(card["year"].unique().to_list()), "n_region", card["SGG_NM"].n_unique())

def visit_month(year, regions):
    f = str(root / f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv")
    regs = ",".join(["'" + r + "'" for r in regions])
    q = (
        "SELECT \"R:기초단체\" AS region, "
        "CAST(\"R:기준연월\" // 100 AS INT) AS year, "
        "CAST(\"R:기준연월\" % 100 AS INT) AS month, "
        "SUM(\"V:방문자 수\") AS visits "
        "FROM read_csv_auto(?) "
        "WHERE \"R:기초단체\" IN (" + regs + ") "
        "AND \"C:방문자유형별\" = '외지인(b)' "
        "AND \"C:시간대\" IS NOT NULL "
        "GROUP BY 1,2,3 ORDER BY 1,2,3"
    )
    return con.execute(q, [f]).pl()

vis = pl.concat([visit_month(y, REGIONS) for y in range(2019, 2027)])
print("VISIT years", vis["year"].unique().sort().to_list(), vis.shape)

tot = (
    card.filter(pl.col("KTO_TOB_MCLS_NM") == "관광총소비")
    .select(["SGG_NM", "year", "month", "spend"])
    .unique()
    .rename({"SGG_NM": "region"})
)
monthly = vis.join(tot, on=["region", "year", "month"], how="left")
monthly = monthly.with_columns((pl.col("spend") / pl.col("visits")).alias("spv"))
monthly.write_csv(out / "monthly.csv")

rows = []
for r in REGIONS:
    for y in range(2019, 2027):
        sub = monthly.filter((pl.col("region") == r) & (pl.col("year") == y) & (pl.col("month") <= 8))
        if sub.height == 0:
            continue
        visits = float(sub["visits"].sum())
        spend = float(sub["spend"].sum())
        rows.append({
            "region": r,
            "year": y,
            "months": int(sub["month"].n_unique()),
            "visits": visits,
            "spend": spend,
            "spv": spend / visits if visits else None,
        })
tab = pl.DataFrame(rows)
tab.write_csv(out / "ytd.csv")
print("YTD FOCUS")
print(tab.filter(pl.col("region") == FOCUS))
print(tab)

nat = pl.read_csv(str(root / "보고서/지역주제_재탐색_20260917/연도별_1월8월_추세.csv"))
chg = nat.filter(pl.col("year") == 2026)
print("SPV 25to26 median", float(chg["per_visit_yoy"].median()), "p10", float(chg["per_visit_yoy"].quantile(0.1)), "p90", float(chg["per_visit_yoy"].quantile(0.9)))
print("visit 25to26 median", float(chg["visits_yoy"].median()))
print("spend 25to26 median", float(chg["spend_yoy"].median()))
recalc = pl.read_csv(str(root / "보고서/지역주제_재탐색_20260917/전국_시군_방문소비_재계산.csv"))
print("24to26 SPV median", float(recalc["per_visit_change"].median()), "visit", float(recalc["visit_change"].median()), "spend", float(recalc["spend_change"].median()))
print("n", recalc.height)

def rank_of(df, col, region, descending=True):
    rnk = df.sort(col, descending=descending).with_columns(pl.arange(1, df.height + 1).alias("rank"))
    return rnk.filter(pl.col("region") == region).select(["region", col, "rank"])

print("부안 rank SPV 24-26")
print(rank_of(recalc, "per_visit_change", FOCUS, True))
print(rank_of(recalc, "visit_change", FOCUS, True))
print(rank_of(recalc, "spend_change", FOCUS, True))

pt = pl.read_csv(str(root / "보고서/지역별_문제유형_20260917.csv")).rename({"Unnamed: 0": "region"})
print("n66", pt.height)
print("체험 q", [float(pt["체험(원)"].quantile(q)) for q in [0, 0.25, 0.5, 0.75, 1]])
ex = pt.sort("체험(원)").with_columns(pl.arange(1, pt.height + 1).alias("rank_low"))
print("부안 체험")
print(ex.filter(pl.col("region") == FOCUS).select(["region", "체험(원)", "식음(원)", "쇼핑(원)", "교통(원)", "rank_low"]))
print("체험 bottom 12")
print(ex.head(12).select(["region", "체험(원)", "식음(원)", "교통(원)", "문제태그"]))

st = pt.sort("숙박객p19-25").with_columns(pl.arange(1, pt.height + 1).alias("rank"))
print("숙박객비중변화 median", float(pt["숙박객p19-25"].median()), "p25", float(pt["숙박객p19-25"].quantile(0.25)))
print(st.filter(pl.col("region") == FOCUS).select(["region", "숙박객%", "숙박객p19-25", "rank"]))
print("숙박이탈 bottom 10")
print(st.head(10).select(["region", "숙박객%", "숙박객p19-25"]))

print("체류 median/p25", float(pt["체류지수"].median()), float(pt["체류지수"].quantile(0.25)))
ct = pt.sort("체류지수").with_columns(pl.arange(1, pt.height + 1).alias("rank"))
print(ct.filter(pl.col("region") == FOCUS).select(["region", "체류지수", "rank"]))

print("체류당소비 median", float(pt["체류당소비"].median()))
cs = pt.sort("체류당소비", descending=True).with_columns(pl.arange(1, pt.height + 1).alias("rank"))
print(cs.filter(pl.col("region") == FOCUS).select(["region", "체류당소비", "rank"]))

print("60+ median/p75", float(pt["60+%"].median()), float(pt["60+%"].quantile(0.75)))
ag = pt.sort("60+%", descending=True).with_columns(pl.arange(1, pt.height + 1).alias("rank"))
print(ag.filter(pl.col("region") == FOCUS).select(["region", "60+%", "2030%", "rank"]))

print("야간 median/p25", float(pt["야간%"].median()), float(pt["야간%"].quantile(0.25)))
ng = pt.sort("야간%").with_columns(pl.arange(1, pt.height + 1).alias("rank_low"))
print(ng.filter(pl.col("region") == FOCUS).select(["region", "야간%", "rank_low"]))

print("수도권 median", float(pt["수도권%"].median()))
print(pt.filter(pl.col("region") == FOCUS).select(["region", "수도권%", "수도권p19-25", "주말%", "성수3개월%", "성수월"]))

