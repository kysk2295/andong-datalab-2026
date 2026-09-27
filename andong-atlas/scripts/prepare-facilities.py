import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'andong-atlas/public/data'
def csv_rows(path):
    with (ROOT / path).open(encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))

shops = csv_rows('data/external/팀원취합_정제/안동_상권_음식점_20260630.csv')
survey = csv_rows('조사/16_월영교_1km_음식점.csv')
features = []
for item in survey:
    candidates = [shop for shop in shops if shop['상호명'].replace(' ', '') == item['상호명'].replace(' ', '')]
    if not candidates:
        candidates = [shop for shop in shops if (shop['상호명'] + shop['지점명']).replace(' ', '') == item['상호명'].replace(' ', '')]
    candidates = [shop for shop in candidates if 128.74 < float(shop['경도']) < 128.78 and 36.56 < float(shop['위도']) < 36.60]
    if len(candidates) == 1:
        shop = candidates[0]
        features.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [float(shop['경도']), float(shop['위도'])]}, 'properties': {key: item[key] for key in ['상호명', '상태', '영업종료', '확인일', '출처']}})
data = {'type': 'FeatureCollection', 'features': features, 'source': '팀 취합 상가정보 2026.06.30 좌표 · 2026.09.19 현장 종료 시각', 'unmatched': [item['상호명'] for item in survey if not any(f['properties']['상호명'] == item['상호명'] for f in features)]}
(OUT / 'facilities.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
print(f'시설 좌표 연결: {len(features)}/{len(survey)}. 미매칭은 지도에 임의 배치하지 않음.')
