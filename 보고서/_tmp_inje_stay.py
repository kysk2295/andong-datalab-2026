from pathlib import Path
import duckdb
root = Path("/Users/koyunseo/한국관광데이터분석")
con = duckdb.connect()
for f in [
    root/"data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv",
    root/"data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1_202608추가.csv",
]:
    print("FILE", f.name)
    print(con.execute("""
    SELECT CAST("R:기준연월"//100 AS INT) y,
           SUM(CASE WHEN "C:숙박일수"='무박' THEN "V:관광객수" ELSE 0 END) daytrip,
           SUM("V:관광객수") tot
    FROM read_csv_auto(?)
    WHERE "R:기초단체"='인제군' AND "C:방문자유형별"='외지인(b)'
      AND CAST("R:기준연월"%100 AS INT)<=8
    GROUP BY 1 ORDER BY 1
    """, [str(f)]).df())
