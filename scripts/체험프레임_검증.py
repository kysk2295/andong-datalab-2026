# -*- coding: utf-8 -*-
"""'안동은 모으고 재우는 데 성공했고, 안 팔리는 건 체험이다' 프레임 전수 검증 (2026-09-18).

검증 대상 6개 주장
  ① 방문당 숙박 소비 전국 상위 18%      ② 외식 상위 39%
  ③ 유사 15곳 체험 811원 vs 안동 525원   ④ 유료 관광시설 방문당 0.1원, 159곳 중 하위 3.5%
  ⑤ 관심관광지 검색 역사유적지 26.4%(경주 18.4%)
결론은 보고서/체험프레임_검증_20260918.md 참조.

데이터 규칙: 카드는 외지인 touDiv1, 방문 연인원은 D1(BDT_01_01_006), 시·군만·이름중복 제외.
"""
import pandas as pd, numpy as np, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
CACHE = Path(os.environ.get("TMPDIR", "/tmp")) / "andong_visits.pkl"

SIM15 = ['서산시','진주시','군산시','영주시','홍성군','동해시','구미시','당진시',
         '예천군','충주시','삼척시','익산시','정읍시','김천시','경산시']  # 기대치 모델 2차 산출
GRP = {
    "숙박": ["호텔","콘도","기타숙박","캠핑장/펜션"],
    "외식": ["일반외식업","제과음료업"],
    "레저·체험": ["문화서비스","관광유원시설","기타레저","골프장","스키장","여행업"],
    "유료관광시설(관광유원시설)": ["관광유원시설"],
    "문화서비스": ["문화서비스"],
    "기타레저": ["기타레저"],
}
EXP_ALL = GRP["레저·체험"]
EXP_NOGOLF = ["문화서비스","관광유원시설","기타레저","여행업"]


def visits(year, months=None):
    """D1 외지인 방문 연인원 (시간대 교차표 합)"""
    t = {}
    f = f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv"
    for ch in pd.read_csv(f, chunksize=2_000_000,
                          usecols=["R:기초단체","R:기준연월","C:방문자유형별","C:시간대","V:방문자 수"]):
        ch = ch[(ch["C:방문자유형별"] == "외지인(b)") & ch["C:시간대"].notna()]
        if months is not None:
            ch = ch[(ch["R:기준연월"] % 100).isin(months)]
        for k, v in ch.groupby("R:기초단체")["V:방문자 수"].sum().items():
            t[k] = t.get(k, 0) + v
    return pd.Series(t)


def cards(path, year, months=None):
    """외지인 카드소비 피벗(원). 같은 이름이 여러 광역에 있는 시군구는 dup으로 반환."""
    c = pd.read_csv(path).drop_duplicates()
    c = c[c.BASE_DATE // 100 == year]
    if months is not None:
        c = c[(c.BASE_DATE % 100).isin(months)]
    n = c[c.KTO_TOB_MCLS_NM == "관광총소비"].groupby(["SGG_NM", "BASE_DATE"]).size()
    dup = set(n[n > 1].index.get_level_values(0))
    W = c.pivot_table(index="SGG_NM", columns="KTO_TOB_MCLS_NM",
                      values="CNSM_AMT", aggfunc="sum").fillna(0) * 1000
    return W, dup


def per_visit(W, v, dup):
    """방문당 소비 표. 시·군만 남기고 이름 중복 제외."""
    idx = sorted(set(W.index) & set(v.index))
    PV = W.loc[idx].div(v.reindex(idx), axis=0)
    return PV[PV.index.str.match(r"^[^ ]+(시|군)$") & ~PV.index.isin(dup)]


def rank_table(PV, label):
    print(f"\n{'='*78}\n[{label}] 대상 시·군 {len(PV)}곳 — 방문당 소비(원)와 전국 순위")
    rows = []
    for g, cols in list(GRP.items()) + [("관광총소비", ["관광총소비"])]:
        s = PV[[c for c in cols if c in PV.columns]].sum(axis=1)
        a = s["안동시"]; higher = int((s > a).sum())
        rows.append({"지표": g, "안동": round(a, 1), "전국중앙": round(s.median(), 1),
                     "순위(높은순)": higher + 1, "상위%": round((higher + 1) / len(s) * 100, 1)})
    print(pd.DataFrame(rows).to_string(index=False))


def decompose(PV):
    print(f"\n{'='*78}\n[④ 핵심] 레저·체험 격차 −285원은 어느 업종에서 오는가 (2025)")
    t = pd.DataFrame({"안동": PV.loc["안동시", EXP_ALL],
                      "유사15곳_평균": PV.loc[SIM15, EXP_ALL].mean(),
                      "유사15곳_중앙": PV.loc[SIM15, EXP_ALL].median(),
                      "전국중앙": PV[EXP_ALL].median()})
    t["차이(평균대비)"] = t["안동"] - t["유사15곳_평균"]
    t.loc["합계"] = t.sum()
    print(t.round(1).to_string())

    print(f"\n{'='*78}\n[골프장·스키장을 뺀 '체험' 재계산]")
    a = PV.loc["안동시", EXP_NOGOLF].sum()
    s = PV.loc[SIM15, EXP_NOGOLF].sum(axis=1)
    nat = PV[EXP_NOGOLF].sum(axis=1)
    print(f"  안동 {a:.1f}원 / 유사15곳 평균 {s.mean():.1f} · 중앙 {s.median():.1f}"
          f" → 평균 대비 {(a/s.mean()-1)*100:+.1f}%, 중앙 대비 {(a/s.median()-1)*100:+.1f}%")
    print(f"  전국 {len(nat)}곳 중앙 {nat.median():.1f}원 · 안동 순위 {int((nat>a).sum())+1}"
          f" = 상위 {((nat>a).sum()+1)/len(nat)*100:.1f}%")

    print(f"\n{'='*78}\n['관광유원시설' 업종이 지표로 쓸 수 있는 상태인가]")
    S = PV["관광유원시설"]
    print(f"  0원 {int((S==0).sum())}곳 / 1원 미만 {int((S<1).sum())}곳 / "
          f"10원 미만 {int((S<10).sum())}곳 / n={len(S)}  (안동 {S['안동시']:.2f}원)")
    print(f"  0원인 시·군: {sorted(S[S==0].index)}")


def search_share():
    print(f"\n{'='*78}\n[⑤ 관심관광지 검색 중 역사유적지 비중]")
    d = pd.read_csv("data/api_region/관광지검색Top100_기간별_LN_03_01_037.csv")
    for reg in ["경상북도 안동시", "경상북도 경주시"]:
        g = d[d.Q_SGG_NM == reg]
        r = g.groupby("PERIOD").apply(
            lambda x: x[x.KTO_CATE_NAME_B == "역사유적지"].SRCH_CNT.sum() / x.SRCH_CNT.sum() * 100,
            include_groups=False)
        print(f"  {reg}: {r.round(1).to_dict()}")
    b = pd.read_csv("data/datalab_추가/관심관광지_외지인_LN_03_01_038_2026_1-8.csv")
    share = b[b.KTO_CATE_NAME_B == "역사유적지"].SRCH_CNT.sum() / b.SRCH_CNT.sum() * 100
    print(f"  ※ 같은 기간 LN_03_01_038(관심관광지 외지인) 기준은 {share:.1f}% — 지표에 따라 3.4%p 차이")


if __name__ == "__main__":
    if CACHE.exists():
        v25, v26 = pd.read_pickle(CACHE)
    else:
        v25, v26 = visits(2025), visits(2026, range(1, 9))
        pd.to_pickle((v25, v26), CACHE)

    W25, d25 = cards("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv", 2025)
    W26, d26 = cards("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv", 2026, range(1, 9))
    PV25, PV26 = per_visit(W25, v25, d25), per_visit(W26, v26, d26)

    rank_table(PV25, "2025년 전체")
    rank_table(PV26, "2026년 1~8월")
    decompose(PV25)
    search_share()
