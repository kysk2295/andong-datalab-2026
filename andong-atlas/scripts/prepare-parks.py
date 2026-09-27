"""Extract mapped parks, lawns, pitches and surveyed tree nodes from the saved OSM response."""
import json,pathlib,xml.etree.ElementTree as ET
from shapely.geometry import Polygon,box,mapping
root=pathlib.Path(__file__).resolve().parents[1];path=root/'public/data/district.json';d=json.loads(path.read_text());xml=ET.parse(root/'.cache/detail/osm.xml').getroot()
nodes={n.attrib['id']:[float(n.attrib['lon']),float(n.attrib['lat'])] for n in xml.findall('node')};features=[];bounds=box(*d['bbox'])
for way in xml.findall('way'):
 tags={x.attrib['k']:x.attrib['v'] for x in way.findall('tag')}
 if tags.get('leisure') not in ['park','garden','playground','pitch'] and tags.get('landuse') not in ['grass','recreation_ground']:continue
 refs=[n.attrib['ref'] for n in way.findall('nd')]
 if len(refs)<4 or refs[0]!=refs[-1] or not all(i in nodes for i in refs):continue
 poly=Polygon([nodes[i] for i in refs])
 if not poly.is_valid:poly=poly.buffer(0)
 poly=poly.intersection(bounds)
 if poly.is_empty or poly.geom_type not in ['Polygon','MultiPolygon']:continue
 center=poly.representative_point();features.append({'type':'Feature','id':way.attrib['id'],'geometry':mapping(poly),'properties':{k:v for k,v in tags.items() if k in ['name','name:en','leisure','landuse','sport']}})
d['parks']=features;d['parkSource']={'source':'OpenStreetMap API 0.6','license':'ODbL 1.0','note':'공원·잔디·운동장 경계는 공개 지도 원본. 수목·벤치·화단의 상세 배치는 미니어처 연출.'}
d['mappedTrees']=[{'coordinates':nodes[n.attrib['id']],'source':'OSM','id':n.attrib['id']} for n in xml.findall('node') if any(t.attrib['k']=='natural' and t.attrib['v']=='tree' for t in n.findall('tag')) and bounds.covers(__import__('shapely').geometry.Point(nodes[n.attrib['id']]))]
path.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')));print('park / lawn / pitch polygons',len(features),'mapped trees',len(d['mappedTrees']))
