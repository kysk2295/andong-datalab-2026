"""안동관광 온라인 설문(2026-09-23~24, 103명) 1차 분석.

입력 data/설문/안동관광온라인설문_응답_정제.csv (scripts/설문_정제.py)
출력 data/설문/설문_집계.json · 설문_문항별_집계.csv

비율은 문항 응답자(빈칸 제외) 기준, 95% 구간은 Wilson.
의향 문항은 '행동'이 아니다 — 보정 없이 참여율·전환율로 쓰지 않는다.
"""
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/설문"
df = pd.read_csv(D / "안동관광온라인설문_응답_정제.csv")

# 5점 척도 통일(띄어쓰기·괄호 설명 차이 제거)
LIKERT = {"매우있다": 5, "매우 있다": 5, "있다": 4, "보통이다": 3, "별로없다": 2, "별로 없다": 2,
          "별로없다(자차/렌터카 이용 등)": 2, "전혀없다": 1, "전혀 없다": 1}
Q9MAP = {"충분하다": "충분", "보통이다": "보통", "부족했다": "부족", "매우부족했다": "매우 부족"}
Q4_OPTS = {
    "외곽 관광지(하회·도산)": "하회마을, 도산서원 같은 외곽 관광지",
    "야간 명소(월영교)": "월영교 같은 밤에 가기 좋은 야간 명소",
    "원도심 밤 가게·식당": "찜닭골목, 중앙시장 같은 원도심의 밤 가게/식당",
    "없음": "없음 (가고 싶던 곳 모두 방문함)",
}


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def share(mask, base):
    k, n = int(mask[base].sum()), int(base.sum())
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "pct": round(100 * k / n, 1) if n else None, "ci95": [lo, hi]}


visit = df["Q1_3년내_방문"].eq("예")
answered = lambda c: df[c].notna()
for c in ["Q6_영수증_체험쿠폰_의향", "Q8_야간택시셔틀_의향", "Q10_야간팝업포차_의향", "Q12_영수증_축제혜택_의향"]:
    df[c + "_점수"] = df[c].map(LIKERT)
top2 = lambda c: df[c + "_점수"] >= 4
top1 = lambda c: df[c + "_점수"] == 5

car = df["Q2_주_이동수단"].eq("자가용 / 렌터카")
bus = df["Q2_주_이동수단"].eq("대중교통 (시내버스 등)")
nocar = df["Q2_주_이동수단"].isin(["대중교통 (시내버스 등)", "도보", "기타 (택시 및 안동관광택시 등)"])

R = {"표본": {"응답": len(df), "3년내_방문_예": int(visit.sum()), "아니오": int((~visit).sum()),
             "기간": "2026-09-23 02:00 ~ 09-24 21:42", "방식": "구글폼 온라인, 편의 표본, 인구통계 문항 없음",
             "주의": "'아니오' 응답자도 뒤 문항에 답함(건너뛰기 없음) → 경험 문항은 방문자 기준으로 센다"}}

# 경험 문항(방문자 72명 기준)
R["Q2_이동수단_방문자"] = df.loc[visit, "Q2_주_이동수단"].value_counts().to_dict()
R["Q3_버스불편_버스이용방문자"] = share(df["Q3_대중교통_불편"].eq("불편했다"), visit & bus)
R["Q3_버스불편_버스타본방문자"] = share(df["Q3_대중교통_불편"].eq("불편했다"),
                                visit & df["Q3_대중교통_불편"].isin(["불편했다", "불편하지 않았다"]))
q4 = df["Q4_이동불편_포기한곳"].fillna("")
R["Q4_포기한곳_방문자"] = {k: share(q4.str.contains(v, regex=False), visit & answered("Q4_이동불편_포기한곳"))
                        for k, v in Q4_OPTS.items()}
R["Q4_포기한곳_있음_방문자"] = share(q4.str.contains("|".join(list(Q4_OPTS.values())[:3]), regex=True),
                              visit & answered("Q4_이동불편_포기한곳"))
q5 = df["Q5_원도심_식사후_이동"]
R["Q5_식사후_이동_방문자"] = q5[visit].value_counts().to_dict()
R["Q5_식사후_월영교_방문자"] = share(q5.str.contains("야경", na=False), visit & answered("Q5_원도심_식사후_이동"))
R["Q5_식사후_체험관광지없이_귀가휴식"] = share(q5.isin(["카페에 갔다가 집/역으로 이동", "숙소로 이동해서 휴식"]),
                                    visit & answered("Q5_원도심_식사후_이동"))
q9 = df["Q9_월영교_밤_식당편의"].map(Q9MAP)
R["Q9_월영교밤_부족_방문자"] = share(q9.isin(["부족", "매우 부족"]), visit & q9.notna())
R["Q9_월영교밤_충분_방문자"] = share(q9.eq("충분"), visit & q9.notna())
R["Q13_귀가시간대_방문자"] = df.loc[visit, "Q13_귀가_교통_시간대"].value_counts().to_dict()
q13 = df["Q13_귀가_교통_시간대"]
R["Q13_당일귀가자중_20~22시"] = share(q13.str.startswith("20시", na=False),
                                visit & q13.notna() & ~q13.str.startswith("당일 귀가 안 함", na=False))

# 의향 문항(전체 응답자, 방문자 따로)
for c, name in [("Q6_영수증_체험쿠폰_의향", "Q6_영수증→체험쿠폰"), ("Q8_야간택시셔틀_의향", "Q8_야간택시셔틀"),
                ("Q10_야간팝업포차_의향", "Q10_야간팝업포차"), ("Q12_영수증_축제혜택_의향", "Q12_영수증→축제혜택")]:
    base = answered(c)
    R[name] = {"전체_top2": share(top2(c), base), "전체_매우": share(top1(c), base),
               "방문자_top2": share(top2(c), base & visit), "방문자_매우": share(top1(c), base & visit),
               "평균점수_5점": round(df.loc[base, c + "_점수"].mean(), 2)}
R["Q8_야간택시셔틀"]["차없는방문자_top2"] = share(top2("Q8_야간택시셔틀_의향"), answered("Q8_야간택시셔틀_의향") & visit & nocar)
R["Q8_야간택시셔틀"]["자차방문자_top2"] = share(top2("Q8_야간택시셔틀_의향"), answered("Q8_야간택시셔틀_의향") & visit & car)
R["Q7_가장좋은혜택"] = df["Q7_가장좋은_혜택"].value_counts().to_dict()
R["Q7_20%이상_할인"] = share(df["Q7_가장좋은_혜택"].str.contains("20% ~ 30%|30% 넘는", na=False), answered("Q7_가장좋은_혜택"))
R["Q11_유료체험_망설임"] = df["Q11_유료체험_망설임"].value_counts().to_dict()
q11 = df["Q11_유료체험_망설임"]
base11 = answered("Q11_유료체험_망설임")
R["Q11_비가격_이유"] = share(q11.isin(["체험 정보가 부족해서", "줄을 오래 서거나 예약하기 불편해서",
                                    "다음 장소로 이동할 시간이 부족해서"]), base11)
R["Q11_가격_이유"] = share(q11.eq("가격이 부담스러워서"), base11)

# 교차: 식사 후 이미 월영교로 가는 사람 vs 아닌 사람의 셔틀 의향 (연결 수요가 새로 생기는지)
yw = q5.str.contains("야경", na=False)
R["교차_Q5월영교아님_셔틀top2"] = share(top2("Q8_야간택시셔틀_의향"), visit & ~yw & q5.notna() & answered("Q8_야간택시셔틀_의향"))
R["교차_Q5월영교_셔틀top2"] = share(top2("Q8_야간택시셔틀_의향"), visit & yw & answered("Q8_야간택시셔틀_의향"))
R["교차_Q9부족_팝업top2"] = share(top2("Q10_야간팝업포차_의향"), q9.isin(["부족", "매우 부족"]) & answered("Q10_야간팝업포차_의향"))
R["교차_Q9보통이상_팝업top2"] = share(top2("Q10_야간팝업포차_의향"), q9.isin(["보통", "충분"]) & answered("Q10_야간팝업포차_의향"))
R["교차_Q4월영교포기_셔틀top2"] = share(top2("Q8_야간택시셔틀_의향"),
                                q4.str.contains("월영교", regex=False) & visit & answered("Q8_야간택시셔틀_의향"))

(D / "설문_집계.json").write_text(json.dumps(R, ensure_ascii=False, indent=1))

rows = []
for c in [c for c in df.columns if c.startswith("Q") and not c.endswith("_점수")]:
    for base_name, base in [("전체", df.index == df.index), ("방문자", visit)]:
        vc = df.loc[base, c].fillna("(빈칸)").value_counts()
        for v, k in vc.items():
            rows.append({"문항": c, "기준": base_name, "응답": v, "명": int(k), "기준_n": int(base.sum())})
pd.DataFrame(rows).to_csv(D / "설문_문항별_집계.csv", index=False, encoding="utf-8-sig")
print(json.dumps(R, ensure_ascii=False, indent=1))

# 사후 가중: 표본은 차 없는 방문자가 많다(방문자 중 약 46%). 철도공사 SKT 추정 유입(철도 9.1+버스 1.4 = 10.5%, 2022.4~6)에 맞춰
# 방문자 의향을 다시 가중한다. 모집단 비중 자체가 추정값이라 참고값으로만 쓴다.
W_NOCAR = 0.105
wt = {}
for c in ["Q6_영수증_체험쿠폰_의향", "Q8_야간택시셔틀_의향", "Q10_야간팝업포차_의향", "Q12_영수증_축제혜택_의향"]:
    b = answered(c) & visit
    pn = top2(c)[b & nocar].mean()
    pc = top2(c)[b & car].mean()
    wt[c] = {"차없음_top2": round(100 * pn, 1), "자차_top2": round(100 * pc, 1),
             "가중_top2": round(100 * (W_NOCAR * pn + (1 - W_NOCAR) * pc), 1),
             "n_차없음": int((b & nocar).sum()), "n_자차": int((b & car).sum())}
R["이동수단_가중_방문자"] = {"차없음_비중_가정": W_NOCAR, **wt}
(D / "설문_집계.json").write_text(json.dumps(R, ensure_ascii=False, indent=1))
print(json.dumps(R["이동수단_가중_방문자"], ensure_ascii=False, indent=1))
