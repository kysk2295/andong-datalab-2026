import pandas as pd, numpy as np, os
S="/private/tmp/claude-501/-Users-koyunseo----------/2f66678e-8b4f-4bd7-bfc8-7be71aab031d/scratchpad"
def load(year):
    t={}
    for ch in pd.read_csv(f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv",chunksize=2_000_000,usecols=["R:기초단체","R:기준연월","C:방문자유형별","C:시간대","V:방문자 수"]):
        ch=ch[(ch["C:방문자유형별"]=="외지인(b)")&ch["C:시간대"].notna()]
        for k,v in ch.groupby("R:기초단체")["V:방문자 수"].sum().items(): t[k]=t.get(k,0)+v
    return pd.Series(t)
P=f"{S}/v1925.pkl"
if os.path.exists(P): v19,v25=pd.read_pickle(P)
else: v19,v25=load(2019),load(2025); pd.to_pickle((v19,v25),P)
c=pd.read_csv("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2019·2020·2025_BDT_02_01_003_35.csv").drop_duplicates()
c["y"]=c.BASE_DATE//100
dup=c[(c.BASE_DATE==201901)&(c.KTO_TOB_MCLS_NM=="관광총소비")].SGG_NM.value_counts(); dup=set(dup[dup>1].index)
p=c.pivot_table(index=["SGG_NM","y"],columns="KTO_TOB_MCLS_NM",values="CNSM_AMT",aggfunc="sum").fillna(0)
LODGE=["호텔","캠핑장/펜션","기타숙박","콘도"]; EXP=["문화서비스","관광유원시설","기타레저"]
p["숙박"]=p[LODGE].sum(1); p["체험"]=p[EXP].sum(1); p["외식"]=p[["일반외식업","제과음료업"]].sum(1)
t19,t25=p.xs(2019,level="y"),p.xs(2025,level="y")
m=pd.read_csv(f"{S}/m1.csv",index_col=0)
s=pd.read_csv("data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv")
s=s[s["C:방문자유형별"]=="외지인(b)"]; s["y"]=s["R:기준연월"]//100; s["숙"]=np.where(s["C:숙박일수"]=="무박",0,s["V:관광객수"])
g=s.groupby(["R:기초단체","y"])[["V:관광객수","V:숙박체류시간","숙"]].sum()
g["체류"]=g["V:숙박체류시간"]/g["V:관광객수"]; g["숙박객비중"]=g["숙"]/g["V:관광객수"]*100
dup_s=s.groupby("R:기초단체")["R:광역단체"].nunique(); dup|=set(dup_s[dup_s>1].index)
st19,st25=g.xs(2019,level="y"),g.xs(2025,level="y")
f=pd.read_csv("data/축제_전체/축제별_방문자_밀집_통합.csv"); f=f[f.BASE_YEAR==2025]
fb=f.sort_values("TOTAL_COL",ascending=False).groupby("SGG_NM").agg(대표축제=("FSTV_REPS_NM","first"),축제방문=("TOTAL_COL","first"),축제외지인비율=("OUT_TOU_NUM_RAT","first"),축제수=("FSTV_ID","nunique"))
D=pd.DataFrame(index=sorted(set(v25.index)&set(t25.index)&set(st25.index)))
D=D[D.index.str.match(r"^[^ ]+(시|군)$")&~D.index.isin(dup)]
D["방문25(만)"]=v25/1e4
D["방문%19-25"]=(v25/v19-1)*100
D["방문당소비25"]=t25["관광총소비"]*1000/v25
D["방문당소비%19-25"]=((t25["관광총소비"]/v25)/(t19["관광총소비"]/v19)-1)*100
D["방문당소비%24-26"]=m["방문당소비%"]; D["방문%24-26"]=m["방문%"]
D["체류시간25"]=st25["체류"]; D["체류%19-25"]=(st25["체류"]/st19["체류"]-1)*100
D["숙박객비중25"]=st25["숙박객비중"]; D["숙박객비중p19-25"]=st25["숙박객비중"]-st19["숙박객비중"]
D["숙박소비%"]=t25["숙박"]/t25["관광총소비"]*100; D["체험소비%"]=t25["체험"]/t25["관광총소비"]*100; D["외식소비%"]=t25["외식"]/t25["관광총소비"]*100
D=D.join(fb)
D=D[(D["방문25(만)"]>=500)].dropna(subset=["방문%19-25","방문당소비%19-25","체류%19-25"])
D.to_csv(f"{S}/panel.csv")
print(len(D)); print(D.loc["안동시"].round(2))
print(D.describe().T[["50%"]].round(2))
