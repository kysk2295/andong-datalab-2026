from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

root = Path("/Users/koyunseo/한국관광데이터분석")
con = duckdb.connect()
con.execute("SET threads=4")

def visit_break(year, extra_where=""):
    f = str(root / f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv")
    return con.execute(f"""
        SELECT *
        FROM read_csv_auto(?)
        WHERE "R:기초단체"='인제군'
          AND "C:방문자유형별"='외지인(b)'
          AND CAST("R:기준연월"%100 AS INTEGER) <= 8
          {extra_where}
    """, [f]).df()

# schema sample
print(con.execute("""
SELECT "C:성별","C:연령별","C:요일","C:시간대", SUM("V:방문자 수") v
FROM read_csv_auto(?)
WHERE "R:기초단체"='인제군' AND "C:방문자유형별"='외지인(b)'
GROUP BY 1,2,3,4 LIMIT 20
""", [str(root/"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_2026.csv")]).df())

print('--- unique dims 2026 ---')
df26 = con.execute("""
SELECT DISTINCT "C:성별" sex, "C:연령별" age, "C:요일" dow, "C:시간대" tod
FROM read_csv_auto(?)
WHERE "R:기초단체"='인제군' AND "C:방문자유형별"='외지인(b)'
""", [str(root/"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_2026.csv")]).df()
print('sex', df26.sex.unique())
print('age', df26.age.unique())
print('dow', df26.dow.unique())
print('tod', df26.tod.unique())
