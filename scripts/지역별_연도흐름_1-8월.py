"""관광지 시·군 66곳 1~8월 방문·방문당 소비 연도 흐름(2019·2023~2026) + 흐름 유형 (9/17)"""
import pandas as pd, glob
S="/private/tmp/claude-501/-Users-koyunseo----------/2f66678e-8b4f-4bd7-bfc8-7be71aab031d/scratchpad"
V=pd.read_pickle(f"{S}/v18.pkl"); Y=[2019,2023,2024,2025,2026]
X=pd.read_csv("보고서/지역별_문제유형_20260917.csv",index_col=0)
c=pd.concat(pd.read_csv(f) for f in glob.glob("data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_touDiv1_*_BDT_02_01_003_35.csv")).drop_duplicates()
c=c[(c.KTO_TOB_MCLS_NM=="관광총소비")&(c.BASE_DATE%100<=8)]; c["y"]=c.BASE_DATE//100
sp=c.groupby(["SGG_NM","y"]).CNSM_AMT.sum().unstack()*1000
R=pd.DataFrame(index=X.index)
for y in Y:
    R[f"방문{y}(만)"]=V[y]/1e4; R[f"방문당{y}"]=sp[y]/V[y]
for a,b in [(2023,2024),(2024,2025),(2025,2026)]:
    R[f"방문%{str(a)[2:]}→{str(b)[2:]}"]=(V[b]/V[a]-1)*100
    R[f"방문당%{str(a)[2:]}→{str(b)[2:]}"]=(R[f"방문당{b}"]/R[f"방문당{a}"]-1)*100
R["방문당%19→26"]=(R["방문당2026"]/R["방문당2019"]-1)*100
R["방문당%23→26"]=(R["방문당2026"]/R["방문당2023"]-1)*100
s=R[["방문당%23→24","방문당%24→25","방문당%25→26"]]
def kind(r):
    a,b,c_=r["방문당%23→24"],r["방문당%24→25"],r["방문당%25→26"]
    neg=sum(v<0 for v in (a,b,c_))
    if neg==3: return "3년 연속 하락"
    if c_<0 and b<0: return "최근 2년 하락"
    if c_<0: return "최근 꺾임"
    if b<0 and c_>0 and r["방문당2026"]<r["방문당2024"]: return "급락 후 회복중(미회복)"
    if b<0 and c_>0: return "급락 후 회복완료"
    return "개선·유지"
R["흐름"]=R.apply(kind,axis=1)
R["문제태그"]=X["문제태그"]
R.to_csv("보고서/지역별_연도흐름_1-8월_20260917.csv")
