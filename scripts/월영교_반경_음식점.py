"""월영교·원도심 반경별 음식점 공급 재계산 (2026-09-19)

`보고서/안동_공간군집_동선단절_20260918.md`의 반경별 음식점 수에 스크립트가 없어 재현용으로 작성.
0.5km·1km는 거리식(haversine / 등거리근사)과 무관하게 동일하게 나온다. 2km는 ±4곳 흔들리므로 쓰지 않는다.

좌표 출처 : data/datalab_추가/중심x연관관광지_LN_03_01_042_2026_1-8.csv (CNTRL_POI_X/Y_COORD)
음식점 출처: data/external/팀원취합_정제/안동_상권_음식점_20260630.csv
            = 소상공인시장진흥공단 상가(상권)정보 2026-06-30 경북 중 안동시 음식업종 3,254곳 (좌표 결측 0)
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
기준점 = ['월영교', '안동구시장', '안동역', '안동하회마을', '도산서원', '유교랜드']
반경 = [0.5, 1.0]                      # 2km는 재현 불안정 → 제외


def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2 - lon1)
    return 2 * R * np.arcsin(np.sqrt(np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2))


def load():
    poi = pd.read_csv(ROOT / 'data/datalab_추가/중심x연관관광지_LN_03_01_042_2026_1-8.csv')
    f = pd.read_csv(ROOT / 'data/external/팀원취합_정제/안동_상권_음식점_20260630.csv')
    return poi, f.dropna(subset=['경도', '위도'])


def 반경별_개수(poi, f):
    rows = []
    for nm in 기준점:
        r = poi[poi.CNTRL_TAR_NM == nm]
        if r.empty:
            continue
        x, y = r.iloc[0].CNTRL_POI_X_COORD, r.iloc[0].CNTRL_POI_Y_COORD
        d = haversine(x, y, f['경도'].values, f['위도'].values)
        rows.append({'기준점': nm, '경도': x, '위도': y,
                     **{f'{t}km': int((d <= t).sum()) for t in 반경}})
    return pd.DataFrame(rows)


def 업종구성(poi, f, 기준='월영교', 비교='안동구시장', km=1.0):
    out = {}
    for nm in (기준, 비교):
        r = poi[poi.CNTRL_TAR_NM == nm].iloc[0]
        d = haversine(r.CNTRL_POI_X_COORD, r.CNTRL_POI_Y_COORD, f['경도'].values, f['위도'].values)
        out[nm] = f[d <= km]['상권업종중분류명'].value_counts()
    t = pd.DataFrame(out).fillna(0).astype(int)
    for c in t.columns:
        t[f'{c} %'] = (t[c] / t[c].sum() * 100).round(1)
    return t


if __name__ == '__main__':
    poi, f = load()
    print(f'음식점 {len(f):,}곳 (좌표 있는 것)\n')
    print('■ 반경별 개수');  print(반경별_개수(poi, f).to_string(index=False))
    print('\n■ 1km 이내 업종 구성 (월영교 vs 안동구시장)');  print(업종구성(poi, f).to_string())
