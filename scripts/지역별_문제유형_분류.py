"""관광지 시·군 66곳 문제 유형 분류 (9/17). 입력: 지역선택_스크리닝 + 방문 원본 집계(scratch pkl)"""
import pandas as pd, numpy as np
S="/private/tmp/claude-501/-Users-koyunseo----------/2f66678e-8b4f-4bd7-bfc8-7be71aab031d/scratchpad"
T=pd.read_csv("보고서/지역선택_스크리닝_20260916.csv",index_col=0)
D=pd.read_csv(f"{S}/panel.csv",index_col=0)
v19,v25=pd.read_pickle(f"{S}/v1925.pkl"); hour=pd.read_pickle(f"{S}/hour.pkl"); M,A=pd.read_pickle(f"{S}/month_age.pkl")
idx=T.index
# 업종별 방문당 소비
c=pd.read_csv("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv").drop_duplicates()
G={"숙박":["호텔","캠핑장/펜션","기타숙박","콘도"],"식음":["일반외식업","제과음료업"],"체험":["문화서비스","관광유원시설","기타레저","골프장","스키장"],"쇼핑":["면세점","대형쇼핑몰","레저용품쇼핑","기타관광쇼핑"],"교통":["육상운송","수상운송","항공운송","렌터카","여행업"]}
mp={k:g for g,ks in G.items() for k in ks}; c["g"]=c.KTO_TOB_MCLS_NM.map(mp); c=c[c.g.notna()&(c.BASE_DATE//100==2025)]
pv=(c.pivot_table(index="SGG_NM",columns="g",values="CNSM_AMT",aggfunc="sum")*1000).div(v25,axis=0)
X=pd.DataFrame(index=idx)
X["방문25(만)"]=T["방문25(만)"]; X["방문%19-25"]=T["방문%19-25"]; X["방문%24-26"]=T["방문%24-26"]
X["방문당소비"]=T["방문당소비25"]; X["소비%19-25"]=T["방문당소비%19-25"]; X["소비%24-26"]=T["방문당소비%24-26"]
for g in ["식음","체험","쇼핑","교통"]: X[f"{g}(원)"]=pv[g]
X["체류지수"]=D["체류시간25"]; X["체류당소비"]=X["방문당소비"]/X["체류지수"]
X["숙박객%"]=T["숙박객비중25"]; X["숙박객p19-25"]=T["숙박객비중p19-25"]; X["숙박객체류%19-25"]=T["숙박객체류%19-25"]
h=hour[2025]; hh=h.groupby(level=[0,1]).sum().unstack(); ww=h.groupby(level=[0,2]).sum().unstack(); tot=hh.sum(axis=1)
X["야간%"]=((hh["21~24시"]+hh["00~06시"])/tot*100); X["주말%"]=((ww["토요일"]+ww["일요일"])/tot*100)
mm=M.unstack(); mm=mm.div(mm.sum(axis=1),axis=0)*100
X["성수3개월%"]=mm.apply(lambda r:r.nlargest(3).sum(),axis=1); X["성수월"]=mm.apply(lambda r:",".join(str(int(m)%100) for m in r.nlargest(3).index),axis=1)
aa=A.unstack(); aa=aa.div(aa.sum(axis=1),axis=0)*100
X["2030%"]=aa["20~29세"]+aa["30~39세"]; X["60+%"]=aa["60~69세"]+aa["70세 이상"]
k=pd.read_csv("보고서/안동교통/32_수도권비중_숙박비율_변화_전국.csv"); k["n"]=k.SGG_NM.str.split().str[-1]
k=k.drop_duplicates("n",keep=False).set_index("n"); X["수도권%"]=k["수도권_2025"]; X["수도권p19-25"]=k["수도권_2025"]-k["수도권_2019"]
X["대표축제"]=T["대표축제"]
X=X.loc[idx]
q=lambda col,p: X[col].quantile(p); med=X.median(numeric_only=True)
tags={}
def tag(name,mask):
    for r in X.index[mask.fillna(False)]: tags.setdefault(r,[]).append(name)
tag("소비하락",(X["소비%19-25"]<0)&(X["소비%24-26"]<0))
tag("방문↑소비↓",(X["방문%19-25"]>med["방문%19-25"])&(X["소비%19-25"]<q("소비%19-25",.25)))
tag("거쳐가기",(X["체류지수"]<q("체류지수",.25))&(X["식음(원)"]<med["식음(원)"]))
tag("쓸곳부족",(X["식음(원)"]<.8*med["식음(원)"])&(X["체험(원)"]<.8*med["체험(원)"])&(X["쇼핑(원)"]<.8*med["쇼핑(원)"]))
tag("체험공백",(X["체험(원)"]<.5*med["체험(원)"])&(X["식음(원)"]>=.9*med["식음(원)"]))
tag("머무는데안씀",(X["체류지수"]>=med["체류지수"])&(X["체류당소비"]<q("체류당소비",.25)))
tag("야간공백",X["야간%"]<q("야간%",.25))
tag("숙박이탈",(X["숙박객p19-25"]<q("숙박객p19-25",.25))|(X["숙박객체류%19-25"]<q("숙박객체류%19-25",.25)))
tag("계절쏠림",X["성수3개월%"]>q("성수3개월%",.75))
tag("주말쏠림",X["주말%"]>q("주말%",.75))
tag("업무체류의심",(X["주말%"]<q("주말%",.25))&(X["체류지수"]>=med["체류지수"]))
tag("고령화",X["60+%"]>q("60+%",.75))
X["문제태그"]=pd.Series({k:" · ".join(v) for k,v in tags.items()})
X["태그수"]=X["문제태그"].fillna("").apply(lambda s: 0 if not s else s.count("·")+1)
X["종합순위"]=T["기본순위"]
X.sort_values("종합순위").to_csv("보고서/지역별_문제유형_20260917.csv")
pd.set_option("display.width",300); pd.set_option("display.max_colwidth",80)
print(X.median(numeric_only=True).round(1).to_string())
print(X.sort_values("종합순위")[["종합순위","방문25(만)","방문당소비","체류지수","야간%","주말%","성수3개월%","성수월","수도권%","문제태그"]].round(1).to_string())
print(pd.Series([t for v in tags.values() for t in v]).value_counts())
