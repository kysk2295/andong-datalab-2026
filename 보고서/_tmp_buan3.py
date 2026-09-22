import duckdb
import polars as pl
from pathlib import Path

root = Path("/Users/koyunseo/한국관광데이터분석")
out = Path("/tmp/buan_out")
con = duckdb.connect()
con.execute("SET threads=4")
FOCUS = "부안군"

print("FEST 2024/2025")
for y in [2024, 2025]:
    df = pl.read_csv(str(root / f"data/축제_전체/문체부_{y}지역축제_개최계획_정제.csv"), infer_schema_length=20000)
    sub = df.filter(pl.col("시군구").str.contains("부안"))
    cols = [c for c in ["시군구", "축제명", "시작월", "종료월", "일수", "방문객_2024", "예산_합계", "유형"] if c in df.columns]
    print(y, sub.select(cols))

fest = pl.read_csv(str(root / "data/축제_전체/축제별_방문자_밀집_통합.csv"))
print("축제밀집 부안")
print(fest.filter(pl.col("SGG_NM").str.contains("부안")).select(["FSTV_REPS_NM", "BASE_YEAR", "TOT_OUT", "외지인소비", "외지인_방문당소비", "FSTV_PERD_CNT", "시작월"]))
info = pl.read_csv(str(root / "data/축제_전체/축제개최정보_getFesInfoList.csv"))
print("개최정보")
print(info.filter(pl.col("ADONG_NM2").str.contains("부안") | pl.col("FSTV_REPS_NM").str.contains("부안|변산|격포|채석")))

print("ORIGIN files")
for p in [
    root / "data/bdt/이동통신/출발지역별_방문자수_시군구_BDT_01_01_002_036_외지인b.csv",
    root / "data/bdt/이동통신/시군구_출발지역별_방문자수_상세_BDT_01_01_004_3_5_현지인a.csv",
    root / "data/api_region/유입지_기간별_LN_03_01_053.csv",
    root / "data/api_region/유입권역비중_전국_연도별_LN_03_01_053.csv",
]:
    try:
        df = pl.read_csv(str(p), n_rows=3, infer_schema_length=5000)
        print("FILE", p.name, df.columns)
        print(df)
    except Exception as e:
        print("FAIL", p.name, e)

print("유입권역 전국")
inf = pl.read_csv(str(root / "data/api_region/유입권역비중_전국_연도별_LN_03_01_053.csv"), infer_schema_length=20000)
print(inf.columns)
print(inf.filter(pl.col(inf.columns[0]).cast(pl.Utf8).str.contains("부안") | pl.concat_str([pl.col(c).cast(pl.Utf8) for c in inf.columns[:4]]).str.contains("부안")).head(20) if False else inf.head(2))
print(inf.head(8))
print("unique sample", inf.columns)

cap = pl.read_csv(str(root / "보고서/안동교통/32_수도권비중_숙박비율_변화_전국.csv"))
print("수도권파일", cap.columns)
print(cap.filter(pl.col(cap.columns[0]).cast(pl.Utf8).str.contains("부안") | pl.concat_str([pl.col(c).cast(pl.Utf8) for c in cap.columns[:3]]).str.contains("부안")).head(10))

print("CONDO MONTHLY")
card_files = [
    str(root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv"),
    str(root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv"),
    str(root / "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv"),
]
card = pl.concat([pl.read_csv(f).unique() for f in card_files]).unique()
card = card.with_columns([(pl.col("BASE_DATE") // 100).alias("year"), (pl.col("BASE_DATE") % 100).alias("month"), (pl.col("CNSM_AMT") * 1000).alias("spend")])
condo = card.filter((pl.col("SGG_NM") == FOCUS) & (pl.col("KTO_TOB_MCLS_NM") == "콘도") & (pl.col("month") <= 8) & (pl.col("year").is_in([2019, 2023, 2024, 2025, 2026])))
print(condo.select(["year", "month", "spend"]).sort(["year", "month"]))
print("CONDO YTD")
print(condo.group_by("year").agg(pl.col("spend").sum()).sort("year"))

lodging_cats = ["콘도", "캠핑장/펜션", "기타숙박", "호텔"]
lod = card.filter((pl.col("SGG_NM") == FOCUS) & (pl.col("KTO_TOB_MCLS_NM").is_in(lodging_cats)) & (pl.col("month") <= 8) & (pl.col("year").is_in([2019, 2024, 2025, 2026])))
print("LODGING TOTAL")
print(lod.group_by(["year", "KTO_TOB_MCLS_NM"]).agg(pl.col("spend").sum()).sort(["year", "KTO_TOB_MCLS_NM"]))
print(lod.group_by("year").agg(pl.col("spend").sum().alias("lodging")).sort("year"))

print("EXPERIENCE CATS")
exp_cats = ["기타레저", "문화서비스", "관광유원시설", "골프장"]
exp = card.filter((pl.col("SGG_NM") == FOCUS) & (pl.col("KTO_TOB_MCLS_NM").is_in(exp_cats)) & (pl.col("month") <= 8) & (pl.col("year").is_in([2019, 2024, 2025, 2026])))
print(exp.group_by(["year", "KTO_TOB_MCLS_NM"]).agg(pl.col("spend").sum()).sort(["year", "KTO_TOB_MCLS_NM"]))

print("NAV SEARCH")
nav = pl.read_csv(str(root / "data/bdt/내비게이션/시군구별_검색건수_연도별_BDT_03_01_003_1.csv"))
print(nav.filter(pl.col("SGG_NM") == FOCUS))

print("NAV category 전북")
navc = pl.read_csv(str(root / "data/bdt/내비게이션/시도x중분류_월별시계열_연도별_BDT_03_01_001_4.csv"), n_rows=5)
print(navc.columns, navc)

print("2차 격차 전체에서 호남 해안")
gap2 = pl.read_csv(str(root / "보고서/관광소비_기대치_모델_20260917/2차_Y별_지역격차.csv"))
gap2 = gap2.rename({gap2.columns[0]: "region"})
print(gap2.filter(pl.col("region").is_in(["부안군", "고창군", "태안군", "보령시", "서천군", "영광군", "군산시", "신안군", "해남군", "완도군", "남해군"])))
g1 = pl.read_csv(str(root / "보고서/관광소비_기대치_모델_20260917/지역별_조건대비_격차_2025.csv"))
g1 = g1.rename({g1.columns[0]: "region"})
print("1차 격차 호남해안")
print(g1.filter(pl.col("region").is_in(["부안군", "고창군", "태안군", "보령시", "서천군", "영광군", "군산시"])))

print("VISIT mix age/dow/tod")

def slice_year(year, group_expr, alias):
    f = str(root / f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv")
    q = (
        "SELECT " + group_expr + " AS " + alias + ", SUM(\"V:방문자 수\") AS visits "
        "FROM read_csv_auto(?) WHERE \"R:기초단체\"='부안군' AND \"C:방문자유형별\"='외지인(b)' "
        "AND \"C:시간대\" IS NOT NULL AND CAST(\"R:기준연월\" % 100 AS INTEGER) <= 8 GROUP BY 1 ORDER BY 1"
    )
    return con.execute(q, [f]).pl()

for dim, col in [("age", '"C:연령별"'), ("dow", '"C:요일"'), ("tod", '"C:시간대"'), ("sex", '"C:성별"')]:
    a = slice_year(2019, col, dim).rename({"visits": "v19"})
    b = slice_year(2024, col, dim).rename({"visits": "v24"})
    c = slice_year(2025, col, dim).rename({"visits": "v25"})
    d = slice_year(2026, col, dim).rename({"visits": "v26"})
    m = a.join(b, on=dim, how="full", coalesce=True).join(c, on=dim, how="full", coalesce=True).join(d, on=dim, how="full", coalesce=True)
    m = m.with_columns([
        (pl.col("v19") / pl.col("v19").sum() * 100).alias("s19"),
        (pl.col("v24") / pl.col("v24").sum() * 100).alias("s24"),
        (pl.col("v25") / pl.col("v25").sum() * 100).alias("s25"),
        (pl.col("v26") / pl.col("v26").sum() * 100).alias("s26"),
    ])
    print("DIM", dim)
    print(m)

print("STAY NIGHT mix 2019 vs 2025 vs 2026")
stay_files = [
    str(root / "data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv"),
    str(root / "data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1_202608추가.csv"),
]
stay = pl.concat([pl.read_csv(f) for f in stay_files]).unique()
stay = stay.with_columns([(pl.col("R:기준연월") // 100).alias("year"), (pl.col("R:기준연월") % 100).alias("month")])
sub = stay.filter((pl.col("R:기초단체") == FOCUS) & (pl.col("C:방문자유형별") == "외지인(b)") & (pl.col("month") <= 8) & (pl.col("year").is_in([2019, 2024, 2025, 2026])))
mix = sub.group_by(["year", "C:숙박일수"]).agg(pl.col("V:관광객수").sum().alias("n"))
tot = mix.group_by("year").agg(pl.col("n").sum().alias("tot"))
print(mix.join(tot, on="year").with_columns((pl.col("n") / pl.col("tot") * 100).alias("share")).sort(["year", "C:숙박일수"]))

