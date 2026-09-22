# -*- coding: utf-8 -*-
"""'체류 공간의 파편화 / 야간 콘텐츠 부재 → 1박 고착' 프레임 검증 (2026-09-18).

검증 대상
  ① 고택·숙박 소비 증가 추세          ② 야간 활동 공간과 소비 상권의 분산
  ③ 야간 대표 콘텐츠 부재             ④ 평균 숙박일수 3.07일·전국 하위 15%
  ⑤ 대부분의 숙박이 1박 단박 체류형
결론은 보고서/야간체류프레임_검증_20260918.md 참조.

주의: 숙박일수 지표가 셋이고 값이 다르다 —
  LN_02_01_013 AVG_LODG_DAYS 3.07일 / LN_03_01_052 분포 가중평균 1.79박 / BDT_01_01_006_1 2.44일.
  같은 문단에서 섞어 쓰면 산술 모순이 된다.
"""
import pandas as pd, numpy as np, os
os.chdir("/Users/koyunseo/한국관광데이터분석")
pd.set_option("display.width", 200)

print("="*78); print("[주장5] 평균 숙박일수 3.07일 vs '대부분 1박' — 산술적으로 양립하는가")
s = pd.read_csv("data/datalab_추가/숙박일수분포_월별_LN_03_01_052.csv")
s["y"] = s.BASE_YM//100
a = s[(s.조회_지역=="경상북도 안동시") & (s.y.isin([2024,2025,2026]))]
cols = ["D1","D2","D3","D4","D5","D6","D7"]
for y,g in a.groupby("y"):
    w = g[cols].mean()
    # D7 = 7박 이상으로 가정하여 하한 평균 숙박일수
    mean_lo = sum(w[f"D{i}"]*i for i in range(1,8))/w.sum()
    print(f"  {y}: " + " ".join(f"{c} {w[c]:.1f}%" for c in cols) + f"  → 가중평균 숙박일수 하한 {mean_lo:.2f}박")

l = pd.read_csv("data/api_region/월별_숙박비율_평균숙박일수_LN_02_01_013.csv")
l["y"]=l.BASE_YM//100
la = l[(l.SGG_NM=="경상북도 안동시")&(l.y.isin([2024,2025]))].groupby("y")[["LODG_TOU_NUM_RATE","AVG_LODG_DAYS"]].mean()
print("\n  LN_02_01_013 안동:"); print(la.round(2).to_string())

print("\n  → 1박 63~66%인 분포에서 나올 수 있는 평균은 약 1.9박. 3.07은 같은 '박'이 아니다.")

print("\n" + "="*78); print("[주장4] 평균 숙박일수 전국 순위 (LN_02_01_013, 2025)")
l25 = l[l.y==2025].groupby(["SGG_NM"])[["LODG_TOU_NUM_RATE","AVG_LODG_DAYS"]].mean()
l25 = l25[l25.index.str.match(r"^\S+\s+\S+(시|군)$")]   # 시·군만
v = l25.AVG_LODG_DAYS; av = v["경상북도 안동시"]
print(f"  안동 {av:.3f}일 / 전국중앙 {v.median():.3f} / 낮은순 {int((v<av).sum())+1}위 = 하위 {((v<av).sum()+1)/len(v)*100:.1f}% (n={len(v)})")
r = l25.LODG_TOU_NUM_RATE; ar = r["경상북도 안동시"]
print(f"  숙박객 비율 {ar:.1f}% / 전국중앙 {r.median():.1f} / 상위 {((r>ar).sum()+1)/len(r)*100:.1f}%")

print("\n" + "="*78); print("[주장5b] 1박 비중 — 유사군 7곳 비교 (LN_03_01_052, 2025)")
s25 = s[s.y==2025].groupby("조회_지역")[cols].mean()
print(s25.round(1).to_string())
print(f"\n  안동 D1 {s25.loc['경상북도 안동시','D1']:.1f}% / 7곳 중앙 {s25.D1.median():.1f}%")

print("\n" + "="*78); print("[주장2] 야간에 모이는 곳 vs 야간에 쓰는 곳 — 안동 읍면동 (2026 1~8)")
nv = pd.read_csv("data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_001_009.csv")
nc = pd.read_csv("data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_002_009.csv")
print("  기간:", sorted(nv.조회기간.unique()), "| 방문 구분:", nv.LRFRN_DIV_NM.unique(), "| 소비 구분:", nc.LRFRN_DIV_NM.unique())
per = "2026_1-8"
V = nv[(nv.SGG_NM=="안동시")&(nv.조회기간==per)&(nv.LRFRN_DIV_NM=="내국인")].groupby("ADONG_NM")[["NIGHT_TOU_NUM","TOU_NUM"]].sum()
C = nc[(nc.SGG_NM=="안동시")&(nc.조회기간==per)].groupby(["ADONG_NM","LRFRN_DIV_NM"])[["NIGHT_CNSM_AMT","CNSM_AMT"]].sum()
print(f"\n  야간 방문 절대량 상위 8개 동 (n={len(V)}개 동)")
V["야간비율%"]=V.NIGHT_TOU_NUM/V.TOU_NUM*100
V["야간방문_점유%"]=V.NIGHT_TOU_NUM/V.NIGHT_TOU_NUM.sum()*100
print(V.sort_values("NIGHT_TOU_NUM",ascending=False).head(8).round(1).to_string())
if len(C):
    C2 = C.reset_index(); 
    for div,g in C2.groupby("LRFRN_DIV_NM"):
        g=g.set_index("ADONG_NM"); g["야간소비_점유%"]=g.NIGHT_CNSM_AMT/g.NIGHT_CNSM_AMT.sum()*100
        g["야간비율%"]=g.NIGHT_CNSM_AMT/g.CNSM_AMT*100
        print(f"\n  야간 소비 절대량 상위 8개 동 [{div}]")
        print(g.sort_values("NIGHT_CNSM_AMT",ascending=False).head(8)[["NIGHT_CNSM_AMT","야간비율%","야간소비_점유%"]].round(1).to_string())
# -*- coding: utf-8 -*-


print("="*78); print("[주장1] 숙박 소비 증가 추세 — 안동 외지인 숙박 카드소비")
LODGE=["호텔","콘도","기타숙박","캠핑장/펜션"]
def load(p, yrs, months=None):
    c=pd.read_csv(p).drop_duplicates(); c=c[c.SGG_NM=="안동시"]
    if months: c=c[(c.BASE_DATE%100).isin(months)]
    c["y"]=c.BASE_DATE//100
    return c[c.y.isin(yrs)].pivot_table(index="y",columns="KTO_TOB_MCLS_NM",values="CNSM_AMT",aggfunc="sum").fillna(0)
A=load("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv",[2019,2025])
B=load("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2021-2023_BDT_02_01_003_35.csv",[2021,2022,2023])
C=load("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv",[2024,2025,2026])
full=pd.concat([A,B,C[C.index.isin([2024])]]).sort_index()
t=pd.DataFrame({"숙박(백만원)":full.reindex(columns=LODGE).fillna(0).sum(1)/1e3,"관광총소비(백만원)":full["관광총소비"]/1e3})
t["숙박비중%"]=t["숙박(백만원)"]/t["관광총소비(백만원)"]*100
print("  ※ 연간(2019~2024) · 2025는 아래 1~8월 표와 별도")
print(t.round(1).to_string())
print("\n  1~8월 동기 비교 (2024·2025·2026)")
D=load("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv",[2024,2025,2026],range(1,9))
u=pd.DataFrame({"숙박(백만원)":D.reindex(columns=LODGE).fillna(0).sum(1)/1e3,"관광총소비(백만원)":D["관광총소비"]/1e3})
u["숙박비중%"]=u["숙박(백만원)"]/u["관광총소비(백만원)"]*100
u["숙박 전년비%"]=u["숙박(백만원)"].pct_change()*100
print(u.round(1).to_string())

print("\n" + "="*78); print("[주장3] 야간 콘텐츠 — 경북 야간 검색 상위 관광지에 안동이 있는가 (2026 1~8)")
for f,lab in [("003_005","야간 검색 관광지"),("003_006","야간 검색 음식/기타")]:
    d=pd.read_csv(f"data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_{f}.csv")
    d=d[d.조회기간=="2026_1-8"].sort_values("RNK")
    top=d.head(20)[["RNK","SGG_NM","ITS_BRO_NM","KTO_CATE_SCLS_NM","NIGHT_SRCH_CNT"]]
    print(f"\n  [{lab}] 상위 20 중 안동 {int((top.SGG_NM=='안동시').sum())}건 / 전체 {len(d)}행 중 안동 {int((d.SGG_NM=='안동시').sum())}건")
    print(top.to_string(index=False))
    ad=d[d.SGG_NM=="안동시"]
    if len(ad): print("  안동 항목:"); print(ad[["RNK","ITS_BRO_NM","KTO_CATE_SCLS_NM","NIGHT_SRCH_CNT"]].head(10).to_string(index=False))

print("\n" + "="*78); print("[주장2b] 안동 야간 방문 비율 추세와 경북 내 위치")
nv=pd.read_csv("data/datalab_추가/야간관광_BY_TH_NIGHT_TOUR_001_009.csv")
nv=nv[nv.LRFRN_DIV_NM=="내국인"]
for per in ["2024_1-8","2025","2026_1-8"]:
    g=nv[nv.조회기간==per]
    ad=g[g.SGG_NM=="안동시"]
    print(f"  {per}: 경북 공개 동 {len(g)}개 · 안동 {len(ad)}개 " + " / ".join(f"{r.ADONG_NM} {r.RATE_NUM:.1f}%(경북 {int(r.RNK)}위)" for r in ad.itertuples()))
