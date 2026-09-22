from pathlib import Path
import duckdb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path("/Users/koyunseo/한국관광데이터분석")
OUT = ROOT / "보고서/인제_체류_20260917"
OUT.mkdir(parents=True, exist_ok=True)

con = duckdb.connect()
con.execute("SET threads=4")
f1 = str(ROOT / "data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv")
f2 = str(ROOT / "data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1_202608추가.csv")

con.execute(f"""
CREATE OR REPLACE TABLE stay AS
SELECT * FROM read_csv_auto('{f1}')
UNION ALL
SELECT * FROM read_csv_auto('{f2}')
""")

con.execute("""
CREATE OR REPLACE TABLE stay_b AS
SELECT
  "R:기초단체" AS region,
  "R:광역단체" AS sido,
  CAST("R:기준연월" AS INTEGER) AS ym,
  CAST("R:기준연월" // 100 AS INTEGER) AS year,
  CAST("R:기준연월" % 100 AS INTEGER) AS month,
  "C:숙박일수" AS nights,
  "V:관광객수" AS vis,
  "V:숙박체류시간" AS stay_hours,
  CASE WHEN "C:숙박일수" = '무박' THEN 0 ELSE "V:관광객수" END AS overnight_vis,
  CASE WHEN "C:숙박일수" = '무박' THEN 0 ELSE "V:숙박체류시간" END AS overnight_hours,
  CASE WHEN "C:숙박일수" = '무박' THEN "V:관광객수" ELSE 0 END AS daytrip_vis,
  CASE WHEN "C:숙박일수" = '무박' THEN "V:숙박체류시간" ELSE 0 END AS daytrip_hours,
  CASE WHEN "C:숙박일수" IN ('1박') THEN "V:관광객수" ELSE 0 END AS n1,
  CASE WHEN "C:숙박일수" IN ('2박') THEN "V:관광객수" ELSE 0 END AS n2,
  CASE WHEN "C:숙박일수" IN ('3박','4박','5박','6박') THEN "V:관광객수" ELSE 0 END AS n3to6,
  CASE WHEN "C:숙박일수" = '7박이상' THEN "V:관광객수" ELSE 0 END AS n7p,
  CASE WHEN "C:숙박일수" IN ('7박이상','무박') THEN 0 ELSE "V:관광객수" END AS overnight_ex7_vis,
  CASE WHEN "C:숙박일수" IN ('7박이상','무박') THEN 0 ELSE "V:숙박체류시간" END AS overnight_ex7_hours
FROM stay
WHERE "C:방문자유형별" = '외지인(b)'
""")

sgg = con.execute("""
SELECT region, count(distinct sido) n_sido
FROM stay_b
GROUP BY 1
""").df()
keep = sgg[(sgg.region.str.match(r"^[^ ]+(시|군)$")) & (sgg.n_sido == 1)].region.tolist()
print("keep sgg", len(keep))


def agg_sql(where, group):
    return f"""
    SELECT {group},
           sum(vis) vis,
           sum(stay_hours) stay_hours,
           sum(overnight_vis) overnight_vis,
           sum(overnight_hours) overnight_hours,
           sum(daytrip_vis) daytrip_vis,
           sum(daytrip_hours) daytrip_hours,
           sum(n1) n1, sum(n2) n2, sum(n3to6) n3to6, sum(n7p) n7p,
           sum(overnight_ex7_vis) overnight_ex7_vis,
           sum(overnight_ex7_hours) overnight_ex7_hours
    FROM stay_b
    WHERE {where}
    GROUP BY {group}
    ORDER BY {group}
    """


def metrics(df):
    d = df.copy()
    d["avg_stay"] = d.stay_hours / d.vis
    d["daytrip_stay"] = d.daytrip_hours / d.daytrip_vis.replace(0, np.nan)
    d["overnight_stay"] = d.overnight_hours / d.overnight_vis.replace(0, np.nan)
    d["overnight_ex7_stay"] = d.overnight_ex7_hours / d.overnight_ex7_vis.replace(0, np.nan)
    d["daytrip_share"] = d.daytrip_vis / d.vis * 100
    d["overnight_share"] = d.overnight_vis / d.vis * 100
    d["n1_share_all"] = d.n1 / d.vis * 100
    d["n2_share_all"] = d.n2 / d.vis * 100
    d["n3to6_share_all"] = d.n3to6 / d.vis * 100
    d["n7_share_all"] = d.n7p / d.vis * 100
    d["n1_share_ovn"] = d.n1 / d.overnight_vis.replace(0, np.nan) * 100
    d["n2_share_ovn"] = d.n2 / d.overnight_vis.replace(0, np.nan) * 100
    d["n3to6_share_ovn"] = d.n3to6 / d.overnight_vis.replace(0, np.nan) * 100
    d["n7_share_ovn"] = d.n7p / d.overnight_vis.replace(0, np.nan) * 100
    return d


inje_m = metrics(con.execute(agg_sql("region='인제군'", "year, month")).df())
inje_m.to_csv(OUT / "인제_월별_체류.csv", index=False)

inje_y = metrics(con.execute(agg_sql("region='인제군'", "year")).df())
inje_y["scope"] = "full"
inje_ytd = metrics(con.execute(agg_sql("region='인제군' AND month<=8", "year")).df())
inje_ytd["scope"] = "jan_aug"
inje_y.to_csv(OUT / "인제_연간_체류.csv", index=False)
inje_ytd.to_csv(OUT / "인제_1-8월_체류.csv", index=False)

cols = [
    "year", "vis", "avg_stay", "daytrip_stay", "overnight_stay",
    "overnight_ex7_stay", "daytrip_share", "overnight_share",
    "n1_share_ovn", "n2_share_ovn", "n7_share_ovn",
]
print("INJE JAN-AUG")
print(inje_ytd[cols].round(2).to_string(index=False))
print("INJE FULL")
print(inje_y[cols].round(2).to_string(index=False))

keep_list = ",".join("'" + x.replace("'", "''") + "'" for x in keep)
nat_ytd = metrics(con.execute(agg_sql(f"region IN ({keep_list}) AND month<=8", "region, year")).df())
nat_full = metrics(con.execute(agg_sql(f"region IN ({keep_list}) AND year<=2025", "region, year")).df())


def median_table(df, years, metrics_cols):
    rows = []
    for y in years:
        sub = df[df.year == y]
        row = {"year": y, "n": len(sub)}
        for c in metrics_cols:
            row[c] = float(sub[c].median())
            row[c + "_p25"] = float(sub[c].quantile(0.25))
            row[c + "_p75"] = float(sub[c].quantile(0.75))
        rows.append(row)
    return pd.DataFrame(rows)


mcols = [
    "avg_stay", "daytrip_stay", "overnight_stay", "overnight_ex7_stay",
    "daytrip_share", "overnight_share", "n1_share_ovn", "n7_share_ovn",
]
nat_ytd_med = median_table(nat_ytd, range(2018, 2027), mcols)
nat_full_med = median_table(nat_full, range(2018, 2026), mcols)
nat_ytd_med.to_csv(OUT / "전국시군_1-8월_체류중앙값.csv", index=False)
nat_full_med.to_csv(OUT / "전국시군_연간_체류중앙값.csv", index=False)
print("NATIONAL JAN-AUG median")
print(nat_ytd_med[["year", "n", "avg_stay", "daytrip_share", "overnight_stay"]].round(2).to_string(index=False))

ranks = []
for y in range(2018, 2027):
    sub = nat_ytd[nat_ytd.year == y].copy()
    if "인제군" not in set(sub.region):
        continue
    inj = sub[sub.region == "인제군"].iloc[0]
    n = len(sub)

    def rk(col, ascending=True):
        return int(sub[col].rank(method="min", ascending=ascending).loc[sub.region == "인제군"].iloc[0])

    ranks.append({
        "year": y,
        "n": n,
        "avg_stay": inj.avg_stay,
        "avg_stay_rank_low": rk("avg_stay", True),
        "daytrip_share": inj.daytrip_share,
        "daytrip_rank_high": rk("daytrip_share", False),
        "overnight_stay": inj.overnight_stay,
        "overnight_stay_rank_low": rk("overnight_stay", True),
        "overnight_ex7_stay": inj.overnight_ex7_stay,
        "n7_share_ovn": inj.n7_share_ovn,
        "n7_rank_high": rk("n7_share_ovn", False),
    })
rank_df = pd.DataFrame(ranks)
rank_df.to_csv(OUT / "인제_1-8월_전국순위.csv", index=False)
print("RANKS")
print(rank_df.round(2).to_string(index=False))

NEAR = [
    "인제군", "홍천군", "양양군", "속초시", "평창군", "철원군",
    "춘천시", "가평군", "정선군", "영월군", "삼척시",
]
near_ytd = nat_ytd[nat_ytd.region.isin(NEAR)].copy()
print("near present", sorted(near_ytd.region.unique().tolist()))
near_ytd.to_csv(OUT / "비교지역_1-8월_체류.csv", index=False)

mix = con.execute("""
SELECT year, nights, sum(vis) vis, sum(stay_hours) stay_hours,
       sum(stay_hours)/sum(vis) stay_pp
FROM stay_b
WHERE region='인제군' AND month<=8
GROUP BY 1,2
ORDER BY 1,2
""").df()
mix.to_csv(OUT / "인제_1-8월_숙박일수별.csv", index=False)

lod = pd.read_csv(ROOT / "data/api_region/월별_숙박비율_평균숙박일수_LN_02_01_013.csv")
lod = lod[lod.SGG_NM == "강원특별자치도 인제군"].copy()
lod["year"] = lod.BASE_YM // 100
lod["month"] = lod.BASE_YM % 100
lod.to_csv(OUT / "인제_월별_숙박비율_평균숙박일수_LN.csv", index=False)


def lod_agg(df, months=None):
    rows = []
    for y, sub in df.groupby("year"):
        s = sub if months is None else sub[sub.month.isin(months)]
        if s.empty:
            continue
        rows.append({
            "year": int(y),
            "months": int(s.month.nunique()),
            "숙박비율_월평균": float(s.LODG_TOU_NUM_RATE.mean()),
            "평균숙박일수_월평균": float(s.AVG_LODG_DAYS.mean()),
        })
    return pd.DataFrame(rows)


lod_ytd = lod_agg(lod, range(1, 9))
print("LN JAN-AUG")
print(lod_ytd.round(2).to_string(index=False))

lod_all = pd.read_csv(ROOT / "data/api_region/월별_숙박비율_평균숙박일수_LN_02_01_013.csv")
lod_all["region"] = lod_all.SGG_NM.str.split().str[-1]
lod_all["year"] = lod_all.BASE_YM // 100
lod_all["month"] = lod_all.BASE_YM % 100
lod_all = lod_all[lod_all.month <= 8]
dup_reg = lod_all.groupby("region").SGG_CD.nunique()
lod_sgg = lod_all[
    lod_all.region.str.match(r"^(.*시|.*군)$")
    & ~lod_all.region.isin(dup_reg[dup_reg > 1].index)
]
nat_lod = []
for y, sub in lod_sgg.groupby("year"):
    g = sub.groupby("region")[["LODG_TOU_NUM_RATE", "AVG_LODG_DAYS"]].mean()
    nat_lod.append({
        "year": int(y),
        "n": len(g),
        "숙박비율_중앙": float(g.LODG_TOU_NUM_RATE.median()),
        "평균숙박일수_중앙": float(g.AVG_LODG_DAYS.median()),
    })
nat_lod = pd.DataFrame(nat_lod)
print("LN NAT")
print(nat_lod.round(2).to_string(index=False))

mon = pd.read_csv(ROOT / "보고서/지역주제_재탐색_20260917/월별_방문소비.csv")
im = mon[mon.region == "인제군"].copy()
im = im[im.month <= 8]
spv = (
    im.groupby("year")
    .apply(
        lambda s: pd.Series({
            "visits_006": s.visits.sum(),
            "spend": s.spend.sum(),
            "spv": s.spend.sum() / s.visits.sum(),
        }),
        include_groups=False,
    )
    .reset_index()
)

cmp = inje_ytd.merge(spv, on="year", how="left")
cmp["vis_vs_006"] = cmp.vis / cmp.visits_006
print("stay vis vs 006 vis")
print(cmp[["year", "vis", "visits_006", "vis_vs_006", "avg_stay", "spv"]].round(3).to_string(index=False))


def yoy(df, col, y0, y1):
    a = float(df.loc[df.year == y0, col].iloc[0])
    b = float(df.loc[df.year == y1, col].iloc[0])
    return a, b, (b / a - 1) * 100 if a else np.nan


print("=== YOY JAN-AUG 2025-2026 ===")
for col in [
    "vis", "avg_stay", "daytrip_stay", "overnight_stay",
    "overnight_ex7_stay", "daytrip_share", "overnight_share",
]:
    a, b, p = yoy(inje_ytd, col, 2025, 2026)
    print(f"{col:22s} {a:12.3f} -> {b:12.3f}  {p:+7.2f}%")

print("=== YOY JAN-AUG 2022-2026 ===")
for col in [
    "vis", "avg_stay", "daytrip_stay", "overnight_stay",
    "overnight_ex7_stay", "daytrip_share", "overnight_share",
]:
    a, b, p = yoy(inje_ytd, col, 2022, 2026)
    print(f"{col:22s} {a:12.3f} -> {b:12.3f}  {p:+7.2f}%")

inj26 = inje_ytd[inje_ytd.year == 2026].iloc[0]
med26 = nat_ytd_med[nat_ytd_med.year == 2026].iloc[0]
print("2026 vs national median")
for c in ["avg_stay", "daytrip_stay", "overnight_stay", "daytrip_share"]:
    print(c, inj26[c], "nat", med26[c], "gap", inj26[c] - med26[c])

print("MONTHLY 2024-26")
w = inje_m[inje_m.year.isin([2024, 2025, 2026])][
    ["year", "month", "vis", "avg_stay", "daytrip_share", "overnight_stay", "daytrip_stay"]
]
print(w.round(2).to_string(index=False))

five = inje_ytd[inje_ytd.year.between(2022, 2026)][[
    "year", "vis", "avg_stay", "daytrip_stay", "overnight_stay", "overnight_ex7_stay",
    "daytrip_share", "overnight_share", "n1_share_ovn", "n2_share_ovn", "n7_share_ovn",
]].copy()
five = five.merge(
    nat_ytd_med[["year", "avg_stay", "daytrip_stay", "overnight_stay", "daytrip_share"]].rename(columns={
        "avg_stay": "전국중앙_평균체류",
        "daytrip_stay": "전국중앙_무박체류",
        "overnight_stay": "전국중앙_숙박객체류",
        "daytrip_share": "전국중앙_무박비중",
    }),
    on="year",
)
five = five.merge(
    lod_ytd.rename(columns={"숙박비율_월평균": "LN숙박비율", "평균숙박일수_월평균": "LN평균숙박일"}),
    on="year",
    how="left",
)
five = five.merge(
    nat_lod.rename(columns={"숙박비율_중앙": "전국중앙_LN숙박비율", "평균숙박일수_중앙": "전국중앙_LN평균숙박일"}),
    on="year",
    how="left",
)
five = five.merge(rank_df[["year", "avg_stay_rank_low", "daytrip_rank_high", "n"]], on="year")
for c in ["avg_stay", "daytrip_stay", "overnight_stay", "overnight_ex7_stay", "daytrip_share", "overnight_share"]:
    five[c + "_yoy"] = five[c].pct_change() * 100
five.to_csv(OUT / "인제_5년_1-8월_체류요약.csv", index=False)
print("FIVE YEAR TABLE")
print(five.round(2).to_string(index=False))

candidates = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/AppleGothic.ttf",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
]
for fp in candidates:
    if Path(fp).exists():
        font_manager.fontManager.addfont(fp)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=fp).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

fig, axes = plt.subplots(2, 2, figsize=(11, 8.2))
years = five.year.tolist()
ax = axes[0, 0]
ax.plot(years, five.avg_stay, "o-", color="#1d4ed8", label="인제 평균 체류시간")
ax.plot(years, five["전국중앙_평균체류"], "s--", color="#64748b", label="전국 시·군 중앙값")
ax.set_title("1~8월 방문당 평균 체류시간")
ax.set_ylabel("시간")
ax.legend(frameon=False)
ax.set_xticks(years)

ax = axes[0, 1]
ax.plot(years, five.daytrip_share, "o-", color="#b45309", label="인제 무박 비중")
ax.plot(years, five["전국중앙_무박비중"], "s--", color="#64748b", label="전국 시·군 중앙값")
ax.set_title("1~8월 무박 비중")
ax.set_ylabel("%")
ax.legend(frameon=False)
ax.set_xticks(years)

ax = axes[1, 0]
ax.plot(years, five.daytrip_stay, "o-", color="#0f766e", label="인제 무박 체류")
ax.plot(years, five.overnight_stay, "o-", color="#7c2d12", label="인제 숙박객 체류")
ax.plot(years, five.overnight_ex7_stay, "o--", color="#c2410c", label="인제 숙박객(7박이상 제외)")
ax.set_title("무박 vs 숙박객 체류시간")
ax.set_ylabel("시간")
ax.legend(frameon=False, fontsize=8)
ax.set_xticks(years)

ax = axes[1, 1]
m26 = inje_m[inje_m.year == 2026]
m25 = inje_m[inje_m.year == 2025]
m24 = inje_m[inje_m.year == 2024]
ax.plot(m24.month, m24.avg_stay, "o--", color="#94a3b8", label="2024")
ax.plot(m25.month, m25.avg_stay, "s--", color="#64748b", label="2025")
ax.plot(m26.month, m26.avg_stay, "o-", color="#1d4ed8", label="2026")
ax.set_title("월별 평균 체류시간")
ax.set_xlabel("월")
ax.set_ylabel("시간")
ax.set_xticks(range(1, 13))
ax.legend(frameon=False)

fig.suptitle("인제 체류시간 5년치 (외지인, BDT_01_01_006_1)", fontsize=13)
fig.tight_layout()
fig.savefig(OUT / "인제_체류_5년.png", dpi=150)
print("saved chart")

snap = near_ytd[near_ytd.year == 2026][[
    "region", "vis", "avg_stay", "daytrip_stay", "overnight_stay",
    "daytrip_share", "overnight_share", "n7_share_ovn",
]].sort_values("avg_stay")
print("NEAR 2026")
print(snap.round(2).to_string(index=False))
snap.to_csv(OUT / "비교지역_2026_1-8월.csv", index=False)

print("NIGHT MIX")
for y in [2022, 2025, 2026]:
    sub = mix[mix.year == y].copy()
    sub["share"] = sub.vis / sub.vis.sum() * 100
    print(y)
    print(sub[["nights", "vis", "share", "stay_pp"]].round(2).to_string(index=False))
