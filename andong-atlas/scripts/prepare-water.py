import json,pathlib
from shapely.geometry import shape,mapping,box
from shapely.ops import unary_union
root=pathlib.Path(__file__).resolve().parents[1];d=json.loads((root/'public/data/district.json').read_text());m=json.loads((root/'public/data/map.json').read_text());clip=box(*d['bbox']);water=[]
for f in m['water']:
 g=shape(f['geometry'])
 if g.intersects(clip):water.append(g.buffer(0).intersection(clip))
g=unary_union(water);ps=list(g.geoms) if g.geom_type=='MultiPolygon' else [g];out=[]
for p in ps:
 if p.geom_type!='Polygon' or p.area<1e-9:continue
 out.append({'type':'Feature','geometry':mapping(p),'properties':{'center':list(p.representative_point().coords[0])}})
d['water']=out;(root/'public/data/district.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')));print('water bodies',len(out))
