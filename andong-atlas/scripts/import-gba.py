"""Stream the official GBA research release; retain Andong only. CC BY-NC 4.0."""
import json,math,pathlib,requests,ijson,time
root=pathlib.Path(__file__).resolve().parents[1];cache=root/'.cache/detail'
cache.mkdir(parents=True,exist_ok=True)
bbox=json.loads((root/'public/data/terrain.json').read_text())['bbox']
merc=lambda x,y:(x*20037508.342789244/180,math.log(math.tan((90+y)*math.pi/360))*20037508.342789244/math.pi)
a=merc(bbox[0],bbox[1]);b=merc(bbox[2],bbox[3]);features=[]
url='https://huggingface.co/datasets/zhu-xlab/GBA.LoD1/resolve/main/Polygon/asiaeast/e125_n40_e130_n35.geojson'
out=cache/'gba-andong.json'
if out.exists():features=json.loads(out.read_text())['features']
else:
 with requests.get(url,stream=True,timeout=120) as response:
  response.raise_for_status();response.raw.decode_content=True
  for i,f in enumerate(ijson.items(response.raw,'features.item',use_float=True)):
   coords=f['geometry']['coordinates'];ring=coords[0] if f['geometry']['type']=='Polygon' else coords[0][0];x,y=ring[0]
   if a[0]<=x<=b[0] and a[1]<=y<=b[1]:
    def transform(c):
     if isinstance(c[0],(int,float)):return [round(c[0]*180/20037508.342789244,7),round(math.atan(math.exp(c[1]*math.pi/20037508.342789244))*360/math.pi-90,7)]
     return [transform(v) for v in c]
    f['geometry']['coordinates']=transform(coords);features.append(f)
   if i%100000==0:print('read',i,'Andong',len(features),flush=True)
 out.write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')))
print('polygons',len(features),flush=True)
ids={f['properties']['source']+f['properties']['id']+f['properties']['region']:f for f in features}
url='https://huggingface.co/datasets/zhu-xlab/GBA.LoD1/resolve/main/LoD1/asiaeast/e125_n40_e130_n35.json'
matched=0
with requests.get(url,stream=True,timeout=120) as response:
 response.raise_for_status();response.raw.decode_content=True
 for key,value in ijson.kvitems(response.raw,'',use_float=True):
  if key in ids:
   ids[key]['properties'].update({'height':round(value['height'],2),'heightVariance':round(value['var'],2)});matched+=1
out.write_text(json.dumps({'type':'FeatureCollection','source':'GlobalBuildingAtlas — Zhu et al. 2025, CC BY-NC 4.0','features':features},separators=(',',':')))
print('finished',len(features),'heights',matched,flush=True)
