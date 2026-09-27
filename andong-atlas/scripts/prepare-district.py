import pathlib,json,xml.etree.ElementTree as E,datetime
p=pathlib.Path(__file__).resolve().parents[1];r=E.parse(p/'.cache/detail/osm.xml').getroot();ns={n.get('id'):[float(n.get('lon')),float(n.get('lat'))] for n in r.findall('node')};box=[128.716,36.555,128.774,36.586]
inside=lambda c:box[0]<=c[0]<=box[2] and box[1]<=c[1]<=box[3]
buildings=[];roads=[]
for w in r.findall('way'):
 t={v.get('k'):v.get('v') for v in w.findall('tag')};c=[ns[n.get('ref')] for n in w.findall('nd') if n.get('ref') in ns]
 if len(c)<2:continue
 if 'building'in t and len(c)>=4 and c[0]==c[-1] and any(map(inside,c)):
  buildings.append({'type':'Feature','id':w.get('id'),'properties':t,'geometry':{'type':'Polygon','coordinates':[c]}})
 if 'highway'in t and t['highway']not in ['construction','proposed','rest_area']:
  run=[]
  for pt in c:
   if inside(pt):run.append(pt)
   else:
    if len(run)>1:roads.append({'type':'Feature','id':w.get('id'),'properties':t,'geometry':{'type':'LineString','coordinates':run}})
    run=[]
  if len(run)>1:roads.append({'type':'Feature','id':w.get('id'),'properties':t,'geometry':{'type':'LineString','coordinates':run}})
# Retain tile footprints not represented by the raw OSM extract; do not invent buildings.
m=json.loads((p/'public/data/map.json').read_text());centers=[]
def center(c):return [sum(a[0] for a in c)/len(c),sum(a[1] for a in c)/len(c)]
for f in buildings:centers.append(center(f['geometry']['coordinates'][0]))
added=0
for f in m['building']:
 polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
 for poly in polys:
  c=center(poly[0])
  if not inside(c) or any(((c[0]-d[0])*.803)**2+(c[1]-d[1])**2<(.00014)**2 for d in centers):continue
  buildings.append({'type':'Feature','properties':{**f['properties'],'source':'OpenFreeMap 2026-09-13'},'geometry':{'type':'Polygon','coordinates':poly}});centers.append(c);added+=1
out={'bbox':box,'source':'OpenStreetMap API 0.6 + OpenFreeMap 2026-09-13','downloaded':datetime.datetime.now(datetime.timezone.utc).isoformat(),'buildings':buildings,'roads':roads,'counts':{'osmBuildings':len(buildings)-added,'tileSupplement':added,'roads':len(roads)},'note':'차선·보도·가로등·보행자·교통량은 원본에 없는 경우 시각화용 추정. 실제 도로시설·운행 정보 아님.'}
(p/'public/data/district.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')));print(out['counts'])
