"""Enrich named heritage packs with the already downloaded OSM source geometry.

No network calls. Wall gaps, tree locations and named buildings retain source
coordinates. Roof materials and visitor activity remain display interpretations.
"""
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def enrich():
    for name in ['hahoe', 'byeongsan', 'dosan', 'bongjeong']:
        path = ROOT / f'public/data/regions/{name}.json'
        data = json.loads(path.read_text())
        xml = ET.fromstring((ROOT / f'.cache/regions/{name}.osm').read_bytes())
        nodes = {n.get('id'): [float(n.get('lon')), float(n.get('lat'))] for n in xml.findall('node')}
        walls, groves, trees, sites, courtyards = [], [], [], [], []
        for el in xml:
            tags = {t.get('k'): t.get('v') for t in el.findall('tag')}
            props = {**tags, 'source': 'OpenStreetMap API 0.6'}
            source_id = 'osm-' + el.get('id', '')
            if el.tag == 'node':
                c = nodes[el.get('id')]
                if tags.get('natural') == 'tree':
                    trees.append({'id': source_id, 'coordinates': c, 'name': tags.get('name', ''), 'source': props['source']})
                if tags.get('name') and (tags.get('historic') or tags.get('natural') == 'tree'):
                    sites.append({'id': source_id, 'name': tags.get('name:ko', tags['name']), 'coordinates': c, 'source': props['source']})
                continue
            if el.tag != 'way':
                continue
            refs = [n.get('ref') for n in el.findall('nd')]
            if len(refs) < 2 or not all(n in nodes for n in refs):
                continue
            coords = [nodes[n] for n in refs]
            f = {'type': 'Feature', 'id': source_id, 'properties': props, 'geometry': {'type': 'LineString', 'coordinates': coords}}
            if tags.get('barrier') in ['wall', 'retaining_wall', 'fence']:
                walls.append(f)
            if len(coords) > 3 and coords[0] == coords[-1]:
                polygon = {**f, 'geometry': {'type': 'Polygon', 'coordinates': [coords]}}
                if tags.get('natural') == 'wood':
                    groves.append(polygon)
                if tags.get('historic') == 'archaeological_site':
                    courtyards.append(polygon)
                if tags.get('name') and (tags.get('building') or tags.get('historic')):
                    # A focus point only; the building footprint is not altered.
                    c = [sum(p[k] for p in coords[:-1]) / (len(coords)-1) for k in [0, 1]]
                    sites.append({'id': source_id, 'name': tags['name'], 'coordinates': c, 'source': props['source']})
        data['heritageDetail'] = {'walls': walls, 'groves': groves, 'trees': trees, 'sites': sites, 'courtyards': courtyards,
            'note': '담장·숲 경계·명명된 지점은 OSM 좌표. 담장 높이·재질, 지붕 구분, 숲 안 나무 배치와 방문객은 미니어처 해석.'}
        if name == 'hahoe':
            data['activityCenter'] = [128.5177, 36.5389]
        else:
            site = next((s for s in sites if s['name'] == {'byeongsan':'병산서원','dosan':'도산서원','bongjeong':'대웅전'}[name]), None)
            if site:
                data['activityCenter'] = site['coordinates']
        raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
        path.write_bytes(raw)
        path.with_suffix('.json.gz').write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
        print(name, 'walls', len(walls), 'groves', len(groves), 'sites', len(sites))

if __name__ == '__main__':
    enrich()
