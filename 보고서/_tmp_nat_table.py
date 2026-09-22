import pandas as pd
from pathlib import Path
root = Path("/Users/koyunseo/한국관광데이터분석")
df = pd.read_csv(root / "data/api/방한외래관광객_국적_성별_월별_2021-202608.csv")
df["BASE_DATE"] = df["BASE_DATE"].astype(str)
nat = df[(df.SEX_CD == "전체") & (df.R_LEV == 3) & df.BASE_DATE.str.fullmatch(r"\d{6}")].copy()
nat["year"] = nat.BASE_DATE.str[:4].astype(int)
nat["month"] = nat.BASE_DATE.str[4:6].astype(int)
ytd = nat[nat.month <= 8].groupby(["year", "NAT_NM", "CTNN_NM"], as_index=False)["QTY"].sum()
top = ytd[ytd.year == 2026].sort_values("QTY", ascending=False)
print("top 2026")
print(top.head(15).to_string(index=False))
print("year totals")
print(ytd.groupby("year").QTY.sum().to_string())
wide = ytd.pivot_table(index=["CTNN_NM", "NAT_NM"], columns="year", values="QTY", aggfunc="sum").reset_index()
out = root / "data/api/방한외래관광객_국적_1-8월_2021-2026.csv"
wide.to_csv(out, index=False, encoding="utf-8-sig")
print("saved", out, "rows", len(wide))
md = root / "보고서/인제_국적데이터_수집결과_20260917.md"
md.write_text(
    """# 인제 방문객 국적 데이터 수집 결과 (2026-09-17)

## 결론

인제군 방문객을 국적별로 나눈 공식 시계열은 공개 API에 없다. 받아온 국적 표는 한국 전체 입국(방한 외래관광객)이다. 인제 방문당 소비 분석의 분모(외지인 통신 연인원)와 합치면 안 된다.

## 받은 것

- 한국관광 데이터랩 TS_01_16_005_New: 전국 월 국적 성별 -> data/api/방한외래관광객_국적_성별_월별_2021-202608.csv
- 위 자료를 1-8월 합산 -> data/api/방한외래관광객_국적_1-8월_2021-2026.csv
- 기존 SKT 외국인 방문자: 시군 월 외국인 합계(국적 없음)

시도: TS_01_16_009/010은 국적 코드 없이 빈 응답. TourAPI는 서비스키 없이 거부. 시군 국적 오픈API는 확인되지 않음.

## 인제 한계

- 통신 외지인(b) = 국내 다른 지역 거주자. 국적 없음.
- 통신 외국인(c) = 인제 외국인 방문 합계만. 2026년 1-8월 9.99만 명, 외지인 803만의 약 1.2%.
- 전국 입국 국적 구성이 바뀌어도 인제 거점 방문 구성이 같다고 쓸 수 없음.

국적이 필요하면 출입국·지자체 정보공개(관광지 입장 국적) 또는 현장 설문이다.
""",
    encoding="utf-8",
)
print("md written")
