#!/usr/bin/env python3
"""KTX 도착(부전→안동, 2026.09 시간표) × 도산서원 급행3 출발(안동역·터미널) → 환승 대기시간.
출처: train.asamaru.net 부전→안동 시간표 / tourandong.com 도산서원 대중교통 안내."""
import csv, statistics as st, pathlib
ktx = {"07:53":"KTX-이음","10:00":"KTX-이음","10:11":"ITX-마음","11:05":"KTX-이음","12:00":"KTX-이음","14:02":"KTX-이음",
       "15:18":"KTX-이음","16:42":"KTX-이음","18:12":"KTX-이음","18:21":"ITX-마음"}
bus = ["08:15","09:35","12:15","13:15","16:15"]
m = lambda s: int(s[:2])*60+int(s[3:])
rows=[]
for a,t in ktx.items():
    nxt=[b for b in bus if m(b)>=m(a)+5]   # 역→정류장 도보 5분
    rows.append({"도착":a,"열차":t,"다음 급행3":nxt[0] if nxt else "없음","대기(분)":m(nxt[0])-m(a) if nxt else None})
w=[r["대기(분)"] for r in rows if r["열차"]=="KTX-이음" and r["대기(분)"] is not None]
k=[r for r in rows if r["열차"]=="KTX-이음"]
for r in rows: print(r)
print(f"KTX-이음 {len(k)}회 중 당일 도산서원행 가능 {len(w)}회, 불가 {len(k)-len(w)}회 | 대기 평균 {st.mean(w):.0f}분, 중앙값 {st.median(w):.0f}분, 최대 {max(w)}분")
out=pathlib.Path("보고서/안동교통/38_KTX도착_도산서원_환승대기.csv")
with out.open("w",encoding="utf-8-sig",newline="") as f:
    wr=csv.DictWriter(f,fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
# 효과 시나리오
arr=470562; share=0.5; spend=180000
for c in (0.03,0.05,0.10):
    n=arr*share*c; print(f"1박 전환 {c:.0%}: {n:,.0f}명 × 18만 = {n*spend/1e8:.1f}억 (비용 8억 대비 {n*spend/8e8:.1f}배)")
