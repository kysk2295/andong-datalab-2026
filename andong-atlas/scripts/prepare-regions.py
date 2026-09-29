"""Create local, on-demand detail packs from real map footprints and elevation.

Run with the workspace Python (shapely, pillow). Raw responses are cached;
no generated building footprints or invented points of interest are introduced.
"""
import concurrent.futures as cf
import gzip
import io
import json
import math
import pathlib
import time
import urllib.request
import xml.etree.ElementTree as ET
from PIL import Image
from shapely.geometry import box, shape, mapping, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'public/data/regions'
CACHE = ROOT / '.cache/regions'
OUT.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)
load = lambda name: json.loads((ROOT / f'public/data/{name}.json').read_text())
base, extra, boundaries = load('map'), load('buildings'), load('boundaries')
named = [
    dict(id='station', name='안동역·터미널', bbox=[128.65,36.550,128.716,36.596], center=[128.675,36.5747], cars=240, people=400),
    dict(id='hahoe', name='하회마을·부용대', bbox=[128.501,36.525,128.543,36.555], center=[128.5208,36.5402], cars=80, people=360, heritage=True),
    dict(id='byeongsan', name='병산서원', bbox=[128.543,36.530,128.575,36.557], center=[128.5568,36.5421], cars=40, people=160, heritage=True),
    dict(id='dosan', name='도산서원', bbox=[128.827,36.712,128.858,36.742], center=[128.8433,36.7266], cars=40, people=180, heritage=True),
    dict(id='bongjeong', name='봉정사', bbox=[128.648,36.639,128.679,36.669], center=[128.6627,36.6533], cars=35, people=160, heritage=True),
]

def download(url, path):
    if path.exists():
        return path.read_bytes()
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'AndongAtlasResearch/1.5 (public map visualization)'})
            with urllib.request.urlopen(req, timeout=45) as res:
                raw = res.read()
            tmp = path.with_suffix(path.suffix + '.part')
            tmp.write_bytes(raw)
            tmp.replace(path)
            return raw
        except Exception as exc:
            last = exc
            time.sleep(attempt + 1)
    raise last

def osm(region):
    path = CACHE / (region['id'] + '.osm')
    try:
        raw = download('https://api.openstreetmap.org/api/0.6/map?bbox=' + ','.join(map(str,region['bbox'])), path)
        xml = ET.fromstring(raw)
    except Exception as exc:
        print('OSM fallback',region['id'],str(exc),flush=True)
        return [],[],[],[],[],str(exc)
    nodes = {n.get('id'):[float(n.get('lon')),float(n.get('lat'))] for n in xml.findall('node')}
    buildings,roads,areas,assets,rails = [],[],[],[],[]
    for w in xml.findall('way'):
        tags = {t.get('k'):t.get('v') for t in w.findall('tag')}
        refs = [n.get('ref') for n in w.findall('nd')]
        if not all(n in nodes for n in refs):
            continue
        coords = [nodes[n] for n in refs]
        if len(coords)<2:
            continue
        feature = dict(type='Feature',id='osm-'+w.get('id'),properties={**tags,'source':'OpenStreetMap API 0.6'},geometry=dict(type='LineString',coordinates=coords))
        if tags.get('railway') in ['rail','light_rail','narrow_gauge'] and tags.get('tunnel')!='yes':
            rails.append(feature)
        if tags.get('highway') and tags['highway'] not in ['proposed','construction','rest_area']:
            roads.append(feature)
        if len(coords)>3 and coords[0]==coords[-1]:
            f = {**feature,'geometry':dict(type='Polygon',coordinates=[coords])}
            if 'building' in tags:
                buildings.append(f)
            elif tags.get('leisure') in ['park','garden','playground','pitch'] or tags.get('landuse') in ['grass','recreation_ground'] or tags.get('amenity')=='parking':
                areas.append(f)
    for n in xml.findall('node'):
        tags = {t.get('k'):t.get('v') for t in n.findall('tag')}
        if tags.get('highway') in ['bus_stop','crossing']:
            assets.append(dict(id=n.get('id'),coordinates=nodes[n.get('id')],kind=tags['highway'],name=tags.get('name',''),source='OpenStreetMap'))
    return buildings,roads,areas,assets,rails,None

# Named destinations retain raw OSM road/building attributes. Other rural tiles
# reuse the full existing downloaded vector snapshot, including footpaths.
with cf.ThreadPoolExecutor(max_workers=2) as pool:
    raw_named = dict(zip([r['id'] for r in named], pool.map(osm,named)))
district_shapes=[(f['properties']['adm_nm'].split()[-1],shape(f['geometry']).buffer(0)) for f in boundaries['features']]
city = unary_union([g for _,g in district_shapes])
regions = list(named)
west,south,east,north = load('terrain')['bbox']
dx,dy = .055,.045
for x in range(math.ceil((east-west)/dx)):
    for y in range(math.ceil((north-south)/dy)):
        b = [west+x*dx,south+y*dy,min(east,west+(x+1)*dx),min(north,south+(y+1)*dy)]
        if city.intersects(box(*b)):
            district_name=max(district_shapes,key=lambda item:item[1].intersection(box(*b)).area)[0]
            regions.append(dict(id=f'area-{x}-{y}',name=district_name+' 주변' ,bbox=b,center=[(b[0]+b[2])/2,(b[1]+b[3])/2],cars=100,people=160))

def xy(lon,lat):
    return (lon+180)/360*8192,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*8192
tiles = set()
for r in regions:
    b=r['bbox']; a=xy(b[0],b[3]); z=xy(b[2],b[1])
    tiles.update((x,y) for x in range(int(a[0]),int(z[0])+1) for y in range(int(a[1]),int(z[1])+1))
def terrain_tile(t):
    x,y=t
    old=ROOT/f'.cache/detail/e-13-{x}-{y}.png'
    raw=old.read_bytes() if old.exists() else download(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/13/{x}/{y}.png', CACHE/f'e-13-{x}-{y}.png')
    return t,Image.open(io.BytesIO(raw)).convert('RGB')
with cf.ThreadPoolExecutor(max_workers=5) as pool:
    images=dict(pool.map(terrain_tile, sorted(tiles)))
print('terrain tiles',len(images),'regions',len(regions),flush=True)

def explode(features,kind):
    result=[]
    for i,f in enumerate(features):
        g=shape(f['geometry'])
        if not g.is_valid: g=g.buffer(0)
        parts=list(g.geoms) if hasattr(g,'geoms') else [g]
        for j,p in enumerate(parts):
            if p.geom_type==kind and not p.is_empty:
                result.append(({**f,'id':str(f.get('id',f'base-{i}'))+f'-{j}','geometry':mapping(p)},p))
    return result
building_records=explode(base['building']+extra['features'],'Polygon')
road_records=explode(base['transportation'],'LineString')
water_records=explode(base['water'],'Polygon')
land_records=explode(base['landcover'],'Polygon')
trees=[STRtree([g for _,g in r]) for r in [building_records,road_records,water_records,land_records]]
def select(records,tree,bounds):
    return [records[i] for i in tree.query(bounds) if records[i][1].intersects(bounds)]
def clipped(records,bounds,kind):
    out=[]
    for f,g in records:
        q=g.intersection(bounds)
        for j,p in enumerate(list(q.geoms) if hasattr(q,'geoms') else [q]):
            if p.geom_type==kind and not p.is_empty:
                out.append({**f,'id':str(f.get('id',''))+f'c{j}','geometry':mapping(p)})
    return out

index=[]
for r in regions:
    b=r['bbox']; bounds=box(*b)
    ob,orr,areas,assets,rails,error=raw_named.get(r['id'],([],[],[],[],[],None))
    bs=select(building_records,trees[0],bounds)
    existing=explode(ob,'Polygon'); et=STRtree([g for _,g in existing])
    buildings=[f for f in ob if bounds.covers(shape(f['geometry']).centroid)]
    for f,g in bs:
        if not bounds.covers(g.centroid): continue
        if existing and any(g.intersection(existing[i][1]).area/max(1e-15,min(g.area,existing[i][1].area))>.2 for i in et.query(g)): continue
        buildings.append(f)
    road_map={'minor':'residential','path':'path','track':'track','service':'service','motorway':'motorway','trunk':'trunk','primary':'primary','secondary':'secondary','tertiary':'tertiary'}
    fallback_roads=[]
    for f,g in select(road_records,trees[1],bounds):
        p=f['properties']; highway=road_map.get(p.get('class'))
        if highway: fallback_roads.append(({**f,'properties':{**p,'highway':highway,'bridge':'yes' if p.get('brunnel')=='bridge' else 'no','source':'OpenFreeMap vector snapshot'}},g))
    roads=clipped(explode(orr,'LineString') if orr else fallback_roads,bounds,'LineString')
    railways=clipped(explode(rails,'LineString') if rails else [(f,g) for f,g in select(road_records,trees[1],bounds) if f['properties'].get('class')=='rail' and f['properties'].get('brunnel')!='tunnel'],bounds,'LineString')
    water=clipped(select(water_records,trees[2],bounds),bounds,'Polygon')
    for f in water:
        f['properties']={**f['properties'],'center':list(shape(f['geometry']).representative_point().coords[0])}
    land=clipped(select(land_records,trees[3],bounds),bounds,'Polygon')
    parks=clipped(explode(areas,'Polygon'),bounds,'Polygon')
    if r.get('heritage'):
        for f in buildings:
            c=shape(f['geometry']).centroid
            dist=math.hypot((c.x-r['center'][0])*89500,(c.y-r['center'][1])*111320)
            # Style interpretation only, stored separately from source tags.
            if dist<650 and shape(f['geometry']).area<1e-7:
                f['properties']={**f['properties'],'visualRoof':'traditional','visualStyleNote':'전통 지붕 유형을 참고한 미니어처, 실제 외관 복원 아님'}
    kmx=111320*math.cos(math.radians((b[1]+b[3])/2))
    cols=math.ceil((b[2]-b[0])*kmx/18)+1; rows=math.ceil((b[3]-b[1])*111320/18)+1
    heights=[]
    for j in range(rows):
        for i in range(cols):
            tx,ty=xy(b[0]+i/(cols-1)*(b[2]-b[0]),b[3]-j/(rows-1)*(b[3]-b[1]))
            red,green,blue=images[int(tx),int(ty)].getpixel((min(255,int(tx%1*256)),min(255,int(ty%1*256))))
            heights.append(max(0,round(red*256+green+blue/256-32768)))
    payload={**r,'terrain':dict(bbox=b,cols=cols,rows=rows,heights=heights,source='AWS Terrain Tiles Terrarium z13; ~18m display grid'),'buildings':buildings,'roads':roads,'railways':railways,'water':water,'landcover':land,'parks':parks,'mappedTrees':[],'streetAssets':[a for a in assets if bounds.covers(Point(a['coordinates']))],'source':'OpenStreetMap / OpenFreeMap + GlobalBuildingAtlas + AWS Terrain Tiles','note':'위치·윤곽은 공개 지도. 높이·색·지붕·가로시설·이동 밀도는 자료 또는 미니어처 추정. 실측 교통량·건축 복원 아님.'}
    raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
    (OUT/(r['id']+'.json')).write_bytes(raw)
    (OUT/(r['id']+'.json.gz')).write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
    index.append({**r,'url':'/data/regions/'+r['id']+'.json','counts':dict(buildings=len(buildings),roads=len(roads),railways=len(railways),parks=len(parks),terrain=len(heights)),'osmDetail':bool(orr),'sourceWarning':error})
    print(r['id'],len(buildings),len(roads),len(heights),flush=True)
(ROOT/'public/data/regions.json').write_text(json.dumps({'regions':index,'source':'OpenStreetMap ODbL 1.0; GlobalBuildingAtlas CC BY-NC 4.0; AWS Terrain Tiles','generated':time.strftime('%Y-%m-%d'),'note':'상세 지역을 필요할 때 불러옴. 윤곽 수는 실제 고유 건물 수와 다름.'},ensure_ascii=False,separators=(',',':')))

# Enrich the named packs from the same cached source snapshot.
from runpy import run_path
run_path(str(ROOT / "scripts/prepare-heritage.py"))["enrich"]()
