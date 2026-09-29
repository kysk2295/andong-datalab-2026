"""Save official BIS route variants, geometry and origin departures independently.

Run --refresh to retrieve the public endpoints used by the BIS website.
No inferred intermediate-stop times or live vehicle positions are exported.
"""
import argparse
import concurrent.futures
import datetime
import json
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
CACHE = APP/'.cache/visitor-update'
CACHE.mkdir(parents=True, exist_ok=True)
refresh = argparse.ArgumentParser()
refresh.add_argument('--refresh', action='store_true')
refresh = refresh.parse_args().refresh
BASE = 'https://bus.andong.go.kr'

def get(name, endpoint):
    path = CACHE/(name+'.json')
    if refresh or not path.exists():
        with urllib.request.urlopen(BASE+endpoint, timeout=25) as response:
            value = json.load(response)
        if not isinstance(value, list):
            raise ValueError('Unexpected BIS response')
        path.write_text(json.dumps(value, ensure_ascii=False))
    return json.loads(path.read_text())

routes = [r for r in get('routes', '/api/hp/busRoute') if r['routeNum'] in ['112', '210']]
times = get('timetable', '/api/hp/busTimetable')

def build(r):
    rid = r['routeId']
    stops = sorted(get(f'{rid}-stops', f'/api/bus/routes/{rid}/stops?locale=ko'), key=lambda x: x['routeOrd'])
    vertices = get(f'{rid}-vertices', f'/api/bus/selectBusVertex?routeId={rid}')
    return {
        'id': str(rid), 'number': r['routeNum'], 'name': r['routeNm'],
        'origin': r['stStationNm'], 'destination': r['edStationNm'],
        'source': f'{BASE}/route?routeId={rid}',
        'coordinates': [[v['lng'], v['lat']] for v in vertices],
        'stops': [{'id': str(v['stopId']), 'name': v['stopName'], 'order': v['routeOrd'], 'coordinates': [v['lng'],v['lat']]} for v in stops],
        'schedules': [{'dayCode': str(t['holidayType']), 'origin': t['stStationNm'], 'times': [f'{int(x.split(":")[0]):02}:{int(x.split(":")[1]):02}' for x in t['strtTm'].split(',') if x.strip()]} for t in times if t['routeId']==rid],
    }

result = {'version': 1, 'checkedAt': datetime.date.today().isoformat(), 'provider': '안동시 버스정보시스템',
          'timeBasis': 'origin-departure', 'live': False, 'source': BASE+'/timetable',
          'guideSource': 'https://www.tourandong.com/public/sub5/sub1_2.cshtml',
          'routes': list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(build, routes))}
# With a cached rebuild retain the actual capture date, rather than claiming a refresh.
out = APP/'public/data/transport.json'
if not refresh and out.exists():
    result['checkedAt'] = json.loads(out.read_text())['checkedAt']
out.write_text(json.dumps(result, ensure_ascii=False, separators=(',',':'))+'\n')
print('Official route variants:', len(result['routes']))
