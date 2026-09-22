import duckdb
import polars as pl
from pathlib import Path

root = Path("/Users/koyunseo/한국관광데이터분석")
out = Path("/tmp/buan_out")
out.mkdir(exist_ok=True)
con = duckdb.connect()
con.execute("SET threads=4")
FOCUS = "부안군"
COMP = ["부안군", "고창군", "태안군", "보령시", "서천군", "영광군", "인제군"]

pt = pl.read_csv(str(root / "보고서/지역별_문제유형_20260917.csv"))
pt = pt.rename({pt.columns[0]: "region"})
print("PT n", pt.height, "cols", pt.columns)
print("체험 q", [float(pt["체험(원)"].quantile(q)) for q in [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]])
ex = pt.sort("체험(원)").with_columns(pl.arange(1, pt.height + 1).alias("rank_low"))
print("부안 체험")
print(ex.filter(pl.col("region") == FOCUS).select(["region", "체험(원)", "식음(원)", "쇼핑(원)", "교통(원)", "rank_low", "방문당소비"]))
print("체험 bottom 15")
print(ex.head(15).select(["region", "체험(원)", "식음(원)", "교통(원)", "숙박객%", "문제태그"]))
print("체험/방문당소비")
pt2 = pt.with_columns((pl.col("체험(원)") / pl.col("방문당소비") * 100).alias("ex_share"))
print("ex_share q", [float(pt2["ex_share"].quantile(q)) for q in [0, 0.1, 0.25, 0.5]])
exs = pt2.sort("ex_share").with_columns(pl.arange(1, pt2.height + 1).alias("rank_low"))
print(exs.filter(pl.col("region") == FOCUS).select(["region", "ex_share", "rank_low"]))
print("ex_share bottom 10")
print(exs.head(10).select(["region", "ex_share", "체험(원)"]))

print("교통/방문당")
pt3 = pt.with_columns((pl.col("교통(원)") / pl.col("방문당소비") * 100).alias("tr_share"))
print("tr_share q", [float(pt3["tr_share"].quantile(q)) for q in [0, 0.25, 0.5, 0.75, 0.9, 1]])
trs = pt3.sort("tr_share", descending=True).with_columns(pl.arange(1, pt3.height + 1).alias("rank"))
print(trs.filter(pl.col("region") == FOCUS).select(["region", "tr_share", "교통(원)", "rank"]))
print("교통 상위 10")
print(trs.head(10).select(["region", "tr_share", "교통(원)"]))

st = pt.sort("숙박객p19-25").with_columns(pl.arange(1, pt.height + 1).alias("rank"))
print("숙박객비중변화 median/p25", float(pt["숙박객p19-25"].median()), float(pt["숙박객p19-25"].quantile(0.25)))
print(st.filter(pl.col("region") == FOCUS).select(["region", "숙박객%", "숙박객p19-25", "숙박객체류%19-25", "rank"]))
print("숙박이탈 bottom 12")
print(st.head(12).select(["region", "숙박객%", "숙박객p19-25", "숙박객체류%19-25"]))

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
print("수도권 median", float(pt["수도권%"].median()), "주말 median", float(pt["주말%"].median()), "성수3 median", float(pt["성수3개월%"].median()))
print(pt.filter(pl.col("region") == FOCUS).select(["region", "수도권%", "수도권p19-25", "주말%", "성수3개월%", "성수월", "문제태그", "종합순위"]))

card_files = [
    str(root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv"),
    str(root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv"),
    str(root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv"),
]
card = pl.concat([pl.read_csv(f).unique() for f in card_files]).unique()
card = card.with_columns([
    (pl.col("BASE_DATE") // 100).alias("year"),
    (pl.col("BASE_DATE") % 100).alias("month"),
    (pl.col("CNSM_AMT") * 1000).alias("spend"),
])

ind = (
    card.filter((pl.col("SGG_NM").is_in(COMP)) & (pl.col("month") <= 8) & (pl.col("KTO_TOB_MCLS_NM") != "관광총소비"))
    .group_by(["SGG_NM", "year", "KTO_TOB_MCLS_NM"])
    .agg(pl.col("spend").sum())
)
ind.write_csv(out / "industry_ytd.csv")
buan_ind = ind.filter(pl.col("SGG_NM") == FOCUS).sort(["year", "KTO_TOB_MCLS_NM"])
print("BUAN INDUSTRY YTD")
pv = buan_ind.pivot(values="spend", index="KTO_TOB_MCLS_NM", on="year")
print(pv)

def ytd_ind(year):
    sub = card.filter((pl.col("SGG_NM") == FOCUS) & (pl.col("year") == year) & (pl.col("month") <= 8) & (pl.col("KTO_TOB_MCLS_NM") != "관광총소비"))
    g = sub.group_by("KTO_TOB_MCLS_NM").agg(pl.col("spend").sum())
    tot = float(g["spend"].sum())
    return g.with_columns((pl.col("spend") / tot * 100).alias("share")).sort("spend", descending=True)

for y in [2019, 2024, 2025, 2026]:
    print("SHARE", y)
    print(ytd_ind(y))

print("COMPARE 2025 experience and condo")
cmp25 = (
    card.filter((pl.col("SGG_NM").is_in(COMP)) & (pl.col("year") == 2025) & (pl.col("month") <= 8) & (pl.col("KTO_TOB_MCLS_NM") != "관광총소비"))
    .group_by(["SGG_NM", "KTO_TOB_MCLS_NM"])
    .agg(pl.col("spend").sum())
)
tot25 = cmp25.group_by("SGG_NM").agg(pl.col("spend").sum().alias("tot"))
cmp25s = cmp25.join(tot25, on="SGG_NM").with_columns((pl.col("spend") / pl.col("tot") * 100).alias("share"))
for cat in ["기타레저", "문화서비스", "콘도", "캠핑장/펜션", "기타숙박", "호텔", "육상운송", "일반외식업", "기타관광쇼핑"]:
    print("CAT", cat)
    print(cmp25s.filter(pl.col("KTO_TOB_MCLS_NM") == cat).select(["SGG_NM", "spend", "share"]).sort("share", descending=True))

print("CONDO 24 vs 26")
condo = (
    card.filter((pl.col("SGG_NM").is_in(COMP)) & (pl.col("month") <= 8) & (pl.col("KTO_TOB_MCLS_NM") == "콘도") & (pl.col("year").is_in([2024, 2026])))
    .group_by(["SGG_NM", "year"])
    .agg(pl.col("spend").sum())
    .pivot(values="spend", index="SGG_NM", on="year")
)
print(condo)

stay_files = [
    str(root / "data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv"),
    str(root / "data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1_202608추가.csv"),
]
stay = pl.concat([pl.read_csv(f) for f in stay_files]).unique()
stay = stay.with_columns([
    (pl.col("R:기준연월") // 100).alias("year"),
    (pl.col("R:기준연월") % 100).alias("month"),
])
print("STAY years", sorted(stay["year"].unique().to_list()), "types", stay["C:방문자유형별"].unique().to_list(), "nights", stay["C:숙박일수"].unique().to_list())

def stay_ytd(region):
    rows = []
    for y in range(2019, 2027):
        sub = stay.filter((pl.col("R:기초단체") == region) & (pl.col("C:방문자유형별") == "외지인(b)") & (pl.col("year") == y) & (pl.col("month") <= 8))
        if sub.height == 0:
            continue
        tot = float(sub["V:관광객수"].sum())
        day = float(sub.filter(pl.col("C:숙박일수") == "무박")["V:관광객수"].sum())
        stayn = tot - day
        stay_hours_num = float(sub.filter(pl.col("C:숙박일수") != "무박")["V:숙박체류시간"].sum())
        stay_cnt = float(sub.filter(pl.col("C:숙박일수") != "무박")["V:관광객수"].sum())
        rows.append({
            "region": region,
            "year": y,
            "months": int(sub["month"].n_unique()),
            "tot": tot,
            "daytrip": day,
            "overnight": stayn,
            "day_share": 100 * day / tot if tot else None,
            "stay_share": 100 * stayn / tot if tot else None,
            "stay_hours_per": stay_hours_num / stay_cnt if stay_cnt else None,
        })
    return pl.DataFrame(rows)

print("STAY BUAN")
print(stay_ytd(FOCUS))
for r in ["고창군", "태안군", "보령시"]:
    print("STAY", r)
    print(stay_ytd(r))

monthly = pl.read_csv("/tmp/buan_out/monthly.csv")
bm = monthly.filter((pl.col("region") == FOCUS) & (pl.col("month") <= 8) & (pl.col("year").is_in([2024, 2025, 2026])))
print("MONTHLY BUAN")
print(bm.sort(["year", "month"]))

w = (
    bm.filter(pl.col("year").is_in([2025, 2026]))
    .select(["year", "month", "visits", "spend", "spv"])
)
w25 = w.filter(pl.col("year") == 2025).rename({"visits": "v25", "spend": "s25", "spv": "spv25"}).drop("year")
w26 = w.filter(pl.col("year") == 2026).rename({"visits": "v26", "spend": "s26", "spv": "spv26"}).drop("year")
ww = w25.join(w26, on="month")
spv25 = float(ww["s25"].sum() / ww["v25"].sum())
spv26 = float(ww["s26"].sum() / ww["v26"].sum())
cf = float((ww["v26"] * ww["spv25"]).sum() / ww["v26"].sum())
print("SPV25", spv25, "SPV26", spv26, "change%", (spv26 / spv25 - 1) * 100)
print("mix cf", cf, "mix%", (cf / spv25 - 1) * 100, "within%", (spv26 / cf - 1) * 100)
print(ww.with_columns([
    ((pl.col("v26") / pl.col("v25") - 1) * 100).alias("v_yoy"),
    ((pl.col("s26") / pl.col("s25") - 1) * 100).alias("s_yoy"),
    ((pl.col("spv26") / pl.col("spv25") - 1) * 100).alias("spv_yoy"),
]))

