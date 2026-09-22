#!/usr/bin/env python3
"""팀원 취합 원본(data/팀원취합) → 분석용 정제본(data/external/팀원취합_정제).
원본은 건드리지 않음. 필요 패키지: pandas openpyxl xlrd pyproj holidays"""
import pathlib, re, datetime as dt, warnings
import pandas as pd, holidays
from pyproj import Transformer
warnings.filterwarnings("ignore")
SRC = pathlib.Path("data/팀원취합"); OUT = pathlib.Path("data/external/팀원취합_정제"); OUT.mkdir(parents=True, exist_ok=True)
save = lambda df, name: (df.to_csv(OUT / name, index=False, encoding="utf-8-sig"), print(f"✔ {name}: {len(df):,}행"))

# 1) 일반음식점 인허가 → 영업중만, 좌표 EPSG:5174(중부원점 Bessel) → WGS84
f = pd.read_excel(SRC / "식품_일반음식점_경북안동시.csv.xlsx")
f = f[f["영업상태명"] == "영업/정상"].copy()
lon, lat = Transformer.from_crs("EPSG:5174", "EPSG:4326", always_xy=True).transform(f["좌표정보(X)"].values, f["좌표정보(Y)"].values)
f["경도"], f["위도"] = lon, lat
cols = ["관리번호", "사업장명", "업태구분명", "인허가일자", "소재지면적", "시설총규모", "남성종사자수", "여성종사자수",
        "전통업소주된음식", "도로명주소", "지번주소", "전화번호", "경도", "위도", "데이터갱신시점"]
save(f[cols].sort_values("인허가일자"), "안동_일반음식점_영업중.csv")

# 2) 상권정보: '_음식점업' 파일 Sheet1 = 경북 원본과 동일, Sheet2 = 팀원이 고른 안동 음식 일부(1,612/3,254, 기준 불명)
#    → 경북 원본에서 안동·음식 전체를 뽑고 Sheet2 포함 여부만 표시
m = pd.read_excel(SRC / "소상공인시장진흥공단_상가(상권)정보_20260630_경북.xlsx")
a = m[(m["시군구명"] == "안동시") & (m["상권업종대분류명"] == "음식")].copy()
s = pd.read_excel(SRC / "소상공인시장진흥공단_상가(상권)정보_20260630_경북_음식점업.xlsx", sheet_name="Sheet2", usecols=["상가업소번호"])
a["팀원Sheet2포함"] = a["상가업소번호"].isin(s["상가업소번호"])
save(a.drop(columns=["동정보", "호정보"]), "안동_상권_음식점_20260630.csv")

# 3) 안동역 승하차: 요일×시간대 '기간 누적' 표 → long + 일평균(해당 기간 일수로 나눔)
raw = pd.read_excel(SRC / "안동역 승하차 인원 자료(2024.1.1.~2026.8.31.).xlsx", header=None)
start, end = dt.date(2024, 1, 1), dt.date(2026, 8, 31)
hol = holidays.KR(years=range(2024, 2027))
days = pd.date_range(start, end).date
wd = "월화수목금토일"
def 구분(d):  # 명절 = 설·추석 연휴일(대체휴일 포함), 공휴일 = 그 외 법정·임시공휴일
    n = hol.get(d)
    if n and ("설날" in n or "추석" in n): return "명절대수송"
    if n: return "공휴일"
    return "평일" if d.weekday() < 5 else "주말"
cnt = pd.Series([(구분(d), wd[d.weekday()]) for d in days]).value_counts()
groups = [("평일", "월화수목금"), ("주말", "토일"), ("공휴일", wd), ("명절대수송", wd)]
colmap = [(g, w) for g, ws in groups for w in ws]  # 엑셀 C~W열 순서
rows = []
for kind, r0 in (("승차", 7), ("하차", 37)):
    for r in range(r0, r0 + 24):
        for j, (g, w) in enumerate(colmap):
            n = int(cnt.get((g, w), 0)); v = int(raw.iat[r, 2 + j])
            # 명절대수송은 코레일 특별수송기간(연휴 앞뒤 포함) 기준이라 연휴일수로 나누면 과대 → 일평균 미산출
            ok = n and g != "명절대수송"
            rows.append({"승하차": kind, "구분": g, "요일": w, "시간대": raw.iat[r, 1], "기간누적": v, "해당일수": n if ok else None,
                         "일평균": round(v / n, 1) if ok else None})
st = pd.DataFrame(rows)
save(st, "안동역_승하차_시간대별_long.csv")
save(pd.DataFrame([{"구분": g, "요일": w, "일수": int(cnt.get((g, w), 0))} for g, w in colmap]), "안동역_승하차_구분별_일수.csv")

# 4) 2023 고택 통합: 제목행 제거, 전화번호 열 삭제(개인정보), 이름 괄호 별칭 분리, 지정 표기 통일
g = pd.read_excel(SRC / "고택리스트/2023_안동시_고택_리스트.xlsx", sheet_name="통합", header=2).dropna(subset=["고택명"])
g = g.drop(columns=[c for c in g.columns if "전화" in str(c)])
clean = lambda x: re.sub(r"\s+", " ", str(x)).strip() if pd.notna(x) else x
for c in g.columns: g[c] = g[c].map(clean)
m = g["고택명"].str.extract(r"^(.*?)\s*\((.*)\)$")
g["별칭"] = m[1]; g["고택명"] = m[0].fillna(g["고택명"])
g["문화재 지정"] = g["문화재 지정"].replace({"x": "비지정"})
g["숙박 여부"] = g["숙박 여부"].map({"o": "O", "x": "X"})
g["중복의심"] = g.duplicated(["고택명", "법정동/리"], keep=False)
save(g, "안동_고택_2023_정제.csv")
