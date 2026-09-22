import pandas as pd
def load(year):
    t={}
    for ch in pd.read_csv(f"data/bdt/이동통신/방문자수_성별연령요일시간대_교차표_BDT_01_01_006_{year}.csv",chunksize=2_000_000,usecols=["R:기초단체","R:기준연월","C:방문자유형별","C:시간대","V:방문자 수"]):
        ch=ch[(ch["C:방문자유형별"]=="외지인(b)")&ch["C:시간대"].notna()&(ch["R:기준연월"]%100).between(1,8)]
        for k,v in ch.groupby("R:기초단체")["V:방문자 수"].sum().items(): t[k]=t.get(k,0)+v
    return pd.Series(t)
import os
if os.path.exists(SP:="/tmp/m1_visits.pkl"): v24,v26=pd.read_pickle(SP)
else:
    v24,v26=load(2024),load(2026); pd.to_pickle((v24,v26),SP)
c=pd.read_csv("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_2024-2026_1-8월_BDT_02_01_003_35.csv")
c=c[(c.KTO_TOB_MCLS_NM=="관光총소비".replace("光","광"))&(c.BASE_DATE%100).between(1,8)].drop_duplicates()
dup=c[c.BASE_DATE==202401].SGG_NM.value_counts(); dup=set(dup[dup>1].index)
s24=c[c.BASE_DATE//100==2024].groupby("SGG_NM").CNSM_AMT.sum(); s26=c[c.BASE_DATE//100==2026].groupby("SGG_NM").CNSM_AMT.sum()
df=pd.DataFrame({"v24":v24,"v26":v26}).join(pd.DataFrame({"s24":s24,"s26":s26}),how="inner").dropna()
df=df[~df.index.isin(dup)]
df["pv24"]=df.s24/df.v24; df["pv26"]=df.s26/df.v26
df["방문%"]=(df.v26/df.v24-1)*100; df["방문당소비%"]=(df.pv26/df.pv24-1)*100
df["방문당소비26"]=df.pv26
sub=df[df.v24>=1_000_000].copy()
print("중복이름 제외:",sorted(dup)); print("대상",len(sub),"중앙 방문",round(sub["방문%"].median(),1),"방문당소비",round(sub["방문당소비%"].median(),1))
q0=sub[(sub["방문%"]>0)&(sub["방문당소비%"]<0)]
print("방문↑소비↓",len(q0))
sub["격차"]=(sub["방문%"]-sub["방문%"].median())-(sub["방문당소비%"]-sub["방문당소비%"].median())
sub["소비순위(낮은순)"]=sub["방문당소비%"].rank()
q=sub[(sub["방문%"]>0)&(sub["방문당소비%"]<0)]
cols=["v24","방문%","방문당소비%","방문당소비26","격차","소비순위(낮은순)"]
pd.set_option("display.width",200)
print("\n방문↑소비↓ 중 방문당소비 하락 큰 순 top25"); print(q.sort_values("방문당소비%")[cols].head(25).round(1))
print("\n안동"); print(sub.loc[["안동시"]][cols].round(1))
print("안동 방문당소비 하락 순위",int(sub.loc["안동시","소비순위(낮은순)"]),"/",len(sub), "q내 순위", int(q["방문당소비%"].rank()["안동시"]),"/",len(q))
sub.to_csv("보고서/M1_방문소비_매트릭스_초벌.csv")
