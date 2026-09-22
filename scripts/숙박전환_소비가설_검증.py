import csv, collections, math, statistics as st
MOB='data/bdt/이동통신/숙박일수별_관광객_숙박자_체류시간_BDT_01_01_006_1.csv'
CARD='data/bdt/신용카드/시군구별_업종중분류_월별_외지인지출액_BDT_02_01_003_35.csv'
LODGE={'호텔','캠핑장/펜션','기타숙박','콘도'}

mob=collections.defaultdict(lambda:[0.0,0.0,0.0]); nm=collections.defaultdict(set)
for x in csv.DictReader(open(MOB,encoding='utf-8-sig')):
    if x['C:방문자유형별']!='외지인(b)': continue
    n,ym=x['R:기초단체'],x['R:기준연월']; nm[n].add(x['R:광역단체'])
    v=float(x['V:관광객수'] or 0); d=mob[(n,ym)]
    d[0]+=v; d[2]+=float(x['V:숙박체류시간'] or 0)
    if x['C:숙박일수']!='무박': d[1]+=v
dup={n for n,s in nm.items() if len(s)>1}
card=collections.defaultdict(lambda:[0.0,0.0])
for x in csv.DictReader(open(CARD,encoding='utf-8-sig')):
    k=(x['SGG_NM'],x['BASE_DATE']); a=float(x['CNSM_AMT'] or 0)*1000  # 천원->원
    c=x['KTO_TOB_MCLS_NM']
    if c=='관광총소비': card[k][0]+=a
    elif c in LODGE: card[k][1]+=a

P=[]
for k,(tot,stay,hrs) in mob.items():
    if k[0] in dup or k not in card: continue
    csm,lod=card[k]
    if tot<20000 or csm<=0: continue
    P.append((k[0],k[1],stay/tot*100,hrs/tot,csm/tot,(csm-lod)/tot))
print(f"패널: {len({p[0] for p in P})}개 시군구 × {len({p[1] for p in P})}개월 = {len(P):,} 관측치 (2018.01~2026.07)\n")

def corr(xs,ys):
    n=len(xs); mx,my=sum(xs)/n,sum(ys)/n
    cv=sum((a-mx)*(b-my) for a,b in zip(xs,ys))
    sx=math.sqrt(sum((a-mx)**2 for a in xs)); sy=math.sqrt(sum((b-my)**2 for b in ys))
    return cv/(sx*sy) if sx*sy else float('nan')
def slope(xs,ys):
    n=len(xs); mx,my=sum(xs)/n,sum(ys)/n
    d=sum((a-mx)**2 for a in xs)
    return sum((a-mx)*(b-my) for a,b in zip(xs,ys))/d if d else float('nan')

X=[p[2] for p in P]; H=[p[3] for p in P]; Y=[p[4] for p in P]; Z=[p[5] for p in P]
print("① 단순 상관 (Pooled, 교란요인 미통제)")
print(f"   숙박객비중 → 1인당 총소비   r={corr(X,Y):+.3f}   기울기 {slope(X,Y):+,.0f}원/%p")
print(f"   숙박객비중 → 1인당 비숙박소비 r={corr(X,Z):+.3f}   기울기 {slope(X,Z):+,.0f}원/%p")

# within transformation (지역+연월 이중 demean)
def demean(vals, keys):
    m=collections.defaultdict(list)
    for v,k in zip(vals,keys): m[k].append(v)
    mu={k:sum(v)/len(v) for k,v in m.items()}
    return [v-mu[k] for v,k in zip(vals,keys)]
reg=[p[0] for p in P]; ym=[p[1] for p in P]
def twoway(v):
    v=demean(v,reg); v=demean(v,ym); return demean(v,reg)
Xw,Yw,Zw,Hw=twoway(X),twoway(Y),twoway(Z),twoway(H)
print("\n② 지역·시점 이중 고정효과 (같은 지역 안에서의 변동만)")
print(f"   숙박객비중 → 1인당 총소비   r={corr(Xw,Yw):+.3f}   기울기 {slope(Xw,Yw):+,.0f}원/%p")
print(f"   숙박객비중 → 1인당 비숙박소비 r={corr(Xw,Zw):+.3f}   기울기 {slope(Xw,Zw):+,.0f}원/%p")
print(f"   1인당체류시간 → 1인당 비숙박소비 r={corr(Hw,Zw):+.3f}  기울기 {slope(Hw,Zw):+,.0f}원/시간")

# 2025 횡단면 5분위 (단위 수정본)
A=collections.defaultdict(lambda:[0.0,0.0,0.0,0.0])
for n,y,s,h,sp,nz in P:
    if y[:4]!='2025': continue
    t=mob[(n,y)][0]; a=A[n]
    a[0]+=mob[(n,y)][1]; a[1]+=t; a[2]+=card[(n,y)][0]; a[3]+=card[(n,y)][0]-card[(n,y)][1]
R=[(n,a[0]/a[1]*100,a[2]/a[1],a[3]/a[1]) for n,a in A.items() if a[1]>200000]
R.sort(key=lambda r:r[1]); q=len(R)//5
print(f"\n③ 2025년 숙박객비중 5분위별 1인당 소비 ({len(R)}개 시군구)")
print(f"   {'분위':<5}{'숙박객비중':>9}{'1인당총소비':>13}{'1인당비숙박':>13}")
for i in range(5):
    g=R[i*q:(i+1)*q] if i<4 else R[4*q:]
    print(f"   Q{i+1:<4}{st.mean(r[1] for r in g):>8.1f}%{st.mean(r[2] for r in g):>12,.0f}원{st.mean(r[3] for r in g):>12,.0f}원")
d={r[0]:r for r in R}
print("\n④ 관심지역 (2025)")
for n in ['안동시','경주시','전주시','강릉시','여수시','속초시','서귀포시','남원시','영주시','통영시']:
    if n in d:
        r=d[n]; k=sorted(R,key=lambda z:-z[1]).index(r)+1
        print(f"   {n:<5} 숙박객비중 {r[1]:5.1f}% ({k:>3}/{len(R)}위)  1인당총소비 {r[2]:>7,.0f}원  비숙박 {r[3]:>7,.0f}원")
