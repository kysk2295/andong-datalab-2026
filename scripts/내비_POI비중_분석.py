# -*- coding: utf-8 -*-
"""내비 목적지 검색을 시군 전체 통행량으로 정규화해 관광지 POI의 상대 위상을 본다 (2026-09-19).

핵심: LN_03_01_037/038(관심관광지)은 이미 T맵 목적지 검색이다. 새로 붙인 분모는
BDT_03_01_003_1(시군구별 내비 검색건수 연도별) — 그 시군으로 향한 전체 목적지 검색.

결론: POI 비중 하락 −32~37%는 전국 공통 추세. 하회마을 −54.8%만 유별나다.
      Top100 합계 비중은 고정 100개 절단 효과가 섞이므로 근거로 쓰지 않는다.
"""
import pandas as pd, os
os.chdir("/Users/koyunseo/한국관광데이터분석"); pd.set_option("display.width",200)
nav=pd.read_csv("data/bdt/내비게이션/시군구별_검색건수_연도별_BDT_03_01_003_1.csv")
d=pd.read_csv("data/api_region/관광지검색Top100_기간별_LN_03_01_037.csv")
yr=[str(y) for y in range(2018,2026)]; yi=[int(y) for y in yr]

print("="*90); print("[Top100 비중은 절단 효과가 섞인다 — 6개 도시 비교]")
rows=[]
for reg,sgg in [("경상북도 안동시","안동시"),("경상북도 경주시","경주시"),("경상북도 영주시","영주시"),
                ("전북특별자치도 군산시","군산시")]:
    a=d[d.Q_SGG_NM==reg]; n=nav[nav.SGG_NM==sgg].set_index("_YEAR").SRCH_CNT
    top=a[a.PERIOD.isin(yr)].groupby("PERIOD").SRCH_CNT.sum().reindex(yr).values
    tot=n.reindex(yi).values
    rows.append({"지역":sgg,"전체18":int(tot[0]),"전체25":int(tot[-1]),"전체증감%":round((tot[-1]/tot[0]-1)*100,1),
                 "Top100비중18":round(top[0]/tot[0]*100,1),"Top100비중25":round(top[-1]/tot[-1]*100,1)})
print(pd.DataFrame(rows).to_string(index=False))
print("  → 전체가 커지면 고정 100개의 비중은 기계적으로 떨어진다. 이 줄은 근거로 쓰지 않는다.")

print("\n" + "="*90); print("[개별 POI 비중은 절단 영향 없음 — 대표 관광지 비교]")
tgt=[("경상북도 안동시","안동시","월영교"),("경상북도 안동시","안동시","안동하회마을"),
     ("경상북도 안동시","안동시","도산서원"),("경상북도 안동시","안동시","안동구시장"),
     ("경상북도 경주시","경주시","불국사"),("경상북도 경주시","경주시","동궁과월지"),
     ("경상북도 경주시","경주시","경주월드"),("전북특별자치도 군산시","군산시","경암동철길마을"),
     ("경상북도 영주시","영주시","부석사")]
out=[]
for reg,sgg,nm in tgt:
    a=d[(d.Q_SGG_NM==reg)&(d.ITS_BRO_NM==nm)&d.PERIOD.isin(yr)].set_index("PERIOD").SRCH_CNT
    n=nav[nav.SGG_NM==sgg].set_index("_YEAR").SRCH_CNT
    sh=(a.reindex(yr).values/n.reindex(yi).values*100)
    if pd.isna(sh[0]) or pd.isna(sh[-1]): continue
    out.append({"지역":sgg,"POI":nm,"2018":round(sh[0],2),"2021":round(sh[3],2),"2023":round(sh[5],2),
                "2025":round(sh[-1],2),"18→25변화%p":round(sh[-1]-sh[0],2),"상대변화%":round((sh[-1]/sh[0]-1)*100,1)})
o=pd.DataFrame(out)
print(o.to_string(index=False))
print("\n  ※ 값 = 그 POI 검색수 ÷ 그 시군 전체 내비 목적지 검색수 × 100")
