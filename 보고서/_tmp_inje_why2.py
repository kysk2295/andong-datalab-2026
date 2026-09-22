from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

root = Path("/Users/koyunseo/한국관광데이터분석")
con = duckdb.connect()
con.execute("SET threads=4")

def slice_year(year, group_expr, alias):
    f = str(root / f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv")
    return con.execute(f"""
        SELECT {group_expr} AS {alias},
               SUM("V:방문자 수") AS visits
        FROM read_csv_auto(?)
        WHERE "R:기초단체"='인제군'
          AND "C:방문자유형별"='외지인(b)'
          AND "C:시간대" IS NOT NULL
          AND CAST("R:기준연월" % 100 AS INTEGER) <= 8
        GROUP BY 1
        ORDER BY 1
    """, [f]).df()

def month_year(year):
    f = str(root / f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv")
    return con.execute("""
        SELECT CAST("R:기준연월" % 100 AS INTEGER) AS month,
               SUM("V:방문자 수") AS visits
        FROM read_csv_auto(?)
        WHERE "R:기초단체"='인제군'
          AND "C:방문자유형별"='외지인(b)'
          AND "C:시간대" IS NOT NULL
          AND CAST("R:기준연월" % 100 AS INTEGER) <= 8
        GROUP BY 1 ORDER BY 1
    """, [f]).df()

# null check
print('NULLS 2026')
print(con.execute("""
SELECT
  SUM(CASE WHEN "C:성별" IS NULL THEN 1 ELSE 0 END) sex_null,
  SUM(CASE WHEN "C:연령별" IS NULL THEN 1 ELSE 0 END) age_null,
  SUM(CASE WHEN "C:요일" IS NULL THEN 1 ELSE 0 END) dow_null,
  SUM(CASE WHEN "C:시간대" IS NULL THEN 1 ELSE 0 END) tod_null,
  COUNT(*) n
FROM read_csv_auto(?)
WHERE "R:기초단체"='인제군' AND "C:방문자유형별"='외지인(b)'
  AND CAST("R:기준연월"%100 AS INTEGER)<=8
""", [str(root/"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_2026.csv")]).df())

for dim, col in [("age",'"C:연령별"'), ("dow",'"C:요일"'), ("tod",'"C:시간대"'), ("sex",'"C:성별"')]:
    a = slice_year(2024, col, dim).rename(columns={"visits":"v24"})
    b = slice_year(2025, col, dim).rename(columns={"visits":"v25"})
    c = slice_year(2026, col, dim).rename(columns={"visits":"v26"})
    m = a.merge(b, on=dim).merge(c, on=dim)
    m["s24"] = m.v24 / m.v24.sum() * 100
    m["s25"] = m.v25 / m.v25.sum() * 100
    m["s26"] = m.v26 / m.v26.sum() * 100
    m["yoy25"] = (m.v25/m.v24-1)*100
    m["yoy26"] = (m.v26/m.v25-1)*100
    print("\n====", dim)
    print(m.to_string(index=False))

print("\n==== month")
ma, mb, mc = month_year(2024), month_year(2025), month_year(2026)
mm = ma.rename(columns={"visits":"v24"}).merge(mb.rename(columns={"visits":"v25"}), on="month").merge(mc.rename(columns={"visits":"v26"}), on="month")
mm["yoy25"]=(mm.v25/mm.v24-1)*100
mm["yoy26"]=(mm.v26/mm.v25-1)*100
mm["s25"]=mm.v25/mm.v25.sum()*100
mm["s26"]=mm.v26/mm.v26.sum()*100
print(mm.to_string(index=False))
print("contrib to 2026 visit increase")
mm["delta"]=mm.v26-mm.v25
print(mm[["month","delta"]].assign(share=lambda d: d.delta/d.delta.sum()*100).to_string(index=False))
