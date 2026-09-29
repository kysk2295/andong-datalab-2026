"""Keep OSM footprints first; add non-overlapping GBA research footprints."""
import json,pathlib,datetime
from shapely.geometry import shape
from shapely.strtree import STRtree
root=pathlib.Path(__file__).resolve().parents[1];out=root/'public/data';base=json.loads((out/'map.json').read_text());d=json.loads((out/'district.json').read_text());raw=json.loads((root/'.cache/detail/gba-andong.json').read_text())
# Baseline is reproducible even if this script is rerun.
d['buildings']=[f for f in d['buildings'] if f['properties'].get('source')!='GlobalBuildingAtlas']
def geometries(fs):
 gs=[]
 for f in fs:
  g=shape(f['geometry'])
  gs.extend(list(g.geoms) if g.geom_type=='MultiPolygon' else [g])
 return [g for g in gs if g.is_valid and not g.is_empty]
existing=geometries(base['building'])+geometries(d['buildings']);tree=STRtree(existing)
added=[];local=[];bbox=d['bbox'];rejected=0
for f in raw['features']:
 g=shape(f['geometry'])
 if not g.is_valid or g.area<1e-10:continue
 duplicate=False
 for i in tree.query(g):
  other=existing[i]
  if g.intersection(other).area/min(g.area,other.area)>.2 or other.covers(g.centroid):duplicate=True;break
 if duplicate:rejected+=1;continue
 p=f['properties'];height=max(2.5,min(150,p['height']))
 feature={'type':'Feature','id':'gba-'+p['source']+p['id']+p['region'],'properties':{'source':'GlobalBuildingAtlas','height':height,'heightVariance':p['heightVariance'],'heightMethod':'satellite-derived estimate'},'geometry':f['geometry']}
 added.append(feature);x,y=g.centroid.coords[0]
 if bbox[0]<=x<=bbox[2] and bbox[1]<=y<=bbox[3]:local.append(feature)
metadata={'title':'GlobalBuildingAtlas, Zhu et al. (2025)','url':'https://github.com/zhu-xlab/GlobalBuildingAtlas','doi':'10.5194/essd-17-6647-2025','license':'CC BY-NC 4.0','downloaded':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':'위성 기반 건물·높이 추정. 현장 실측·최신 현황 보장 아님. 비상업 연구용. 표시 bbox는 행정경계와 다름.'}
(out/'buildings.json').write_text(json.dumps({'source':metadata,'features':added,'counts':{'downloaded':len(raw['features']),'added':len(added),'overlapRemoved':rejected}},ensure_ascii=False,separators=(',',':')))
d['buildings']+=local;d['counts']['gbaSupplement']=len(local);d['buildingResearchSource']=metadata
(out/'district.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
print({'overviewAdded':len(added),'districtAdded':len(local),'districtTotal':len(d['buildings']),'overlapRemoved':rejected})
