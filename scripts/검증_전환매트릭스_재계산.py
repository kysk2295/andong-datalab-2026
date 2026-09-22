import pandas as pd


def load_visits(year: int) -> pd.Series:
    path = f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv"
    totals: dict[str, float] = {}
    for chunk in pd.read_csv(
        path,
        chunksize=2_000_000,
        usecols=["R:기초단체", "R:기준연월", "C:방문자유형별", "C:시간대", "V:방문자 수"],
    ):
        chunk = chunk[(chunk["C:방문자유형별"] == "외지인(b)") & chunk["C:시간대"].notna()]
        chunk = chunk[(chunk["R:기준연월"] % 100).between(1, 8)]
        for name, value in chunk.groupby("R:기초단체")["V:방문자 수"].sum().items():
            totals[name] = totals.get(name, 0) + value
    return pd.Series(totals)


visits_2024 = load_visits(2024)
print("2024 시군 수:", len(visits_2024), flush=True)
visits_2026 = load_visits(2026)
print("2026 시군 수:", len(visits_2026), flush=True)

card = pd.read_csv(
    "data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv"
)
card = card[card["KTO_TOB_MCLS_NM"] == "관광총소비"].copy()
card["year"] = card["BASE_DATE"] // 100
card["month"] = card["BASE_DATE"] % 100
card = card[card["month"].between(1, 8)]
spend_2024 = card[card["year"] == 2024].groupby("SGG_NM")["CNSM_AMT"].sum()
spend_2026 = card[card["year"] == 2026].groupby("SGG_NM")["CNSM_AMT"].sum()

df = pd.DataFrame({"v24": visits_2024, "v26": visits_2026}).join(
    pd.DataFrame({"s24": spend_2024, "s26": spend_2026}), how="inner"
).dropna()
df["per_visit_24"] = df.s24 / df.v24
df["per_visit_26"] = df.s26 / df.v26
df["visit_chg"] = (df.v26 / df.v24 - 1) * 100
df["spend_chg"] = (df.per_visit_26 / df.per_visit_24 - 1) * 100

andong = df.loc["안동시"]
print("\n=== 안동 ===")
print(f"방문 {andong.v24:,.0f} -> {andong.v26:,.0f} ({andong.visit_chg:+.1f}%)")
print(f"방문당 소비 {andong.per_visit_24:,.0f} -> {andong.per_visit_26:,.0f}원 ({andong.spend_chg:+.1f}%)")

subset = df[df.v24 >= 1_000_000]
total = len(subset)
q1 = ((subset.visit_chg > 0) & (subset.spend_chg > 0)).sum()
q2 = ((subset.visit_chg > 0) & (subset.spend_chg <= 0)).sum()
q3 = ((subset.visit_chg <= 0) & (subset.spend_chg > 0)).sum()
q4 = ((subset.visit_chg <= 0) & (subset.spend_chg <= 0)).sum()
print(f"\n=== 방문 100만회 이상 {total}개 시군 ===")
print(f"방문↑소비↑ {q1} ({q1 / total * 100:.1f}%)")
print(f"방문↑소비↓ {q2} ({q2 / total * 100:.1f}%)")
print(f"방문↓소비↑ {q3} ({q3 / total * 100:.1f}%)")
print(f"방문↓소비↓ {q4} ({q4 / total * 100:.1f}%)")
print(f"중앙값 방문 {subset.visit_chg.median():+.1f}% / 방문당 소비 {subset.spend_chg.median():+.1f}%")
print(f"안동 소비 하위 백분위 {(subset.spend_chg < andong.spend_chg).mean() * 100:.1f}%")

print("\n=== 비교·동급 도시 ===")
for city in ["안동시", "경주시", "군산시", "포항시", "전주시", "문경시", "충주시", "강화군", "공주시", "부여군", "남원시"]:
    if city not in df.index:
        print(f"{city}: 집계 없음")
        continue
    row = df.loc[city]
    print(
        f"{city}: 방문 {row.visit_chg:+.1f}% / 방문당 소비 {row.spend_chg:+.1f}% "
        f"({row.per_visit_24:,.0f} -> {row.per_visit_26:,.0f}원)"
    )

df.to_csv("/tmp/matrix_recalc.csv")
print("\nDONE", flush=True)
