"""Build a source-labelled place catalogue and routable public-map graph.
No private user data, inferred opening hours, or invented official services.
"""
import csv, json, math, re, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'andong-atlas/public/data'
def read(n): return json.loads((OUT/(n+'.json')).read_text())
def rows(p):
 with (ROOT/p).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def norm(s):return re.sub(r'\s|[()·-]','',s)
def distance(a,b):return math.hypot((a[0]-b[0])*89300,(a[1]-b[1])*111320)
m=read('map');detail=read('district'); shops=rows('data/external/팀원취합_정제/안동_상권_음식점_20260630.csv')
root=ET.parse(ROOT/'andong-atlas/.cache/detail/osm.xml').getroot()
rawpois=[{'name':t.get('name'),'coordinates':[float(e.get('lon')),float(e.get('lat'))]} for e in root.findall('node') if (t:={x.get('k'):x.get('v') for x in e.findall('tag')}).get('name')]
pois=[{'name':f['properties'].get('name',''),'coordinates':f['geometry']['coordinates']} for f in m['poi']]+rawpois
catalog=[]
def place(id,name,kind,c,**kw):
 p={'id':id,'name':name,'kind':kind,'coordinates':c,'source':'공개 지도·팀 수집 자료 2026.09','proposed':False,**kw};catalog.append(p);return p
place('station','안동역 · KTX 하차','origin',[128.6748256,36.5742363],source='OpenStreetMap 안동역 출입구 · node 13065380449',description='역 하차 이후의 여행을 재생합니다. 역 내부는 재현하지 않습니다.')
place('terminal','안동터미널','origin',[128.675968,36.57444],source='OpenStreetMap 정류장 위치')
place('hahoe','하회마을 입구','origin',[128.520824,36.540239],source='OpenStreetMap 하회마을 정류장')
place('downtown','원도심 · 안동구시장','origin',[128.728,36.5655],source='팀 원도심 분석 기준점')
place('workshop','원도심 공예체험 거점','experience',[128.728,36.5655],proposed=True,address='안동구시장 권역 · 설치 지점 미확정',description='식음 영수증 인증과 공예 체험 10% 할인을 연결하는 제안입니다.',hours='17:00–21:00 (여행 시연 가정)',open=1020,close=1260,duration=30,price=None,priceText='체험 가격 미확정',reservation='운영·예약 방식 미확정')
place('craft','안동공예문화전시관','experience',[128.761325,36.580373],source='OSM 368898277 · 체험 조사 2026.09.22',address='안동시 석주로 245',hours='09:00–18:00 (수집 자료)',open=540,close=1080,duration=30,description='도자기·한지·천연염색 등 공예 체험. 30분은 여행 계산 가정입니다.',price=None,priceText='프로그램별 요금 확인 필요',reservation='체험 예약·휴무 확인 필요',url='https://www.tourandong.com/public/sub2/sub3.cshtml?seq=372')
bridge=next(f for f in detail['roads'] if f['properties'].get('bridge:name')=='월영교'); bline=bridge['geometry']['coordinates']; west=min(bline,key=lambda c:c[0]);east=max(bline,key=lambda c:c[0])
place('bridge','월영교 서측 입구','sight',west,duration=10,price=0,priceText='산책',description='교량 위를 건너 낙동강과 정자를 둘러봅니다.')
place('bridge-east','월영교 동측 입구','sight',east,duration=5,price=0,priceText='산책')
place('popup','월영교 야간 팝업','popup',read('solution')['sites'][1]['coordinates'],proposed=True,duration=25,open=1110,close=1260,hours='18:30–21:00 (제안)',price=None,priceText='판매 가격 미확정',description='로컬 푸드·공예·체험·관광 안내. 부스·부지 사용 미확정.')
# Exact shop-name joins only; ambiguous and ungeocoded entries are not placed.
for r in rows('조사/12_원도심_식당영업시간_공식목록.csv'):
 hits=[s for s in shops if norm(s['상호명'])==norm(r['공식상호']) or norm(s['상호명']+s['지점명'])==norm(r['공식상호'])]
 hits=[s for s in hits if 128.716<float(s['경도'])<128.745 and 36.555<float(s['위도'])<36.578]
 if len(hits)!=1:continue
 s=hits[0];id='shop-'+s['상가업소번호']
 if any(p['id']==id for p in catalog):continue
 opts={}
 place(id,r['공식상호'],'restaurant',[float(s['경도']),float(s['위도'])],address=s['도로명주소'],hours='점포별 영업시간 확인 필요',areaHours=r['골목안내_영업시간'],description=s['상권업종소분류명'],duration=45,price=None,priceText='메뉴·가격 확인 필요',url=r['출처URL'],source='관광 공식목록·상권정보 좌표 2026.06.30',**opts)
for f in read('facilities')['features']:
 r=f['properties']
 if r['상태']=='폐업':continue
 hits=[s for s in shops if norm(s['상호명']+s['지점명'])==norm(r['상호명']) or norm(s['상호명'])==norm(r['상호명'])];s=min(hits,key=lambda s:distance([float(s['경도']),float(s['위도'])],f['geometry']['coordinates'])) if hits else {}
 times=r['영업종료'].split(':');close=int(times[0])*60+int(times[1]) if len(times)==2 else None
 place('local-'+str(len(catalog)),r['상호명'],'restaurant',f['geometry']['coordinates'],address=s.get('도로명주소','월영교 권역'),hours='종료 '+r['영업종료']+' · 개점·요일 미확인',close=close,duration=30,price=None,priceText='메뉴·가격 확인 필요',source='팀 취합 종료 시각·상권정보 좌표 2026.09')
benefits=json.loads((ROOT/'data/external/작업목록_2-3_수집_20260921/02_주민증/안동_가맹점목록.json').read_text());unmatched=[]
for b in benefits:
 name=b['mbrbNm'];hits=[p for p in catalog if norm(p['name'])==norm(name)]
 if not hits:
  matches=[s for s in shops if norm(s['상호명']+s['지점명'])==norm(name) or norm(s['상호명'])==norm(name)]
  if len(matches)==1:
   s=matches[0];hits=[place('benefit-'+b['mbrbExpsrId'],name,'restaurant',[float(s['경도']),float(s['위도'])],address=s['도로명주소'],hours='미확인',price=None,priceText='가격 확인 필요',duration=30)]
 if not hits:
  matches=[p for p in pois if norm(p['name'])==norm(name)]
  if matches:hits=[place('benefit-'+b['mbrbExpsrId'],name,{'STAYNG':'stay','VWNG':'attraction','EXPRN':'experience'}.get(b.get('mbrbBnefClCd'),'attraction'),matches[0]['coordinates'],hours='미확인',price=None,priceText='가격 확인 필요',duration=30)]
 if hits:
  hits[0]['benefit']=re.sub('<[^>]*>',' ',b['bnefCn']);hits[0]['benefitSource']='디지털 관광주민증 가맹 목록 · 2026.09.21 수집';hits[0]['description']=b.get('mbrbIntroWordsCn','')
 else:unmatched.append({'name':name,'benefit':re.sub('<[^>]*>',' ',b['bnefCn'])})
# Graph uses true shared coordinates; short boundary joins are explicitly tagged.
nodes=[];keys={};edges=[]; rawset=set();globalset=set()
def node(c,raw):
 k=(round(c[0],6),round(c[1],6))
 if k not in keys:keys[k]=len(nodes);nodes.append(list(k))
 i=keys[k];(rawset if raw else globalset).add(i);return i
bbox=detail['bbox']
regional_details=[read('regions/'+name) for name in ['station','hahoe'] if (OUT/('regions/'+name+'.json')).exists()]
detail_bounds=[bbox]+[r['bbox'] for r in regional_details]
def inside(c):return bbox[0]<c[0]<bbox[2] and bbox[1]<c[1]<bbox[3]
def boundary_distance(c):return min(min(abs(c[0]-b[0])*89300,abs(c[0]-b[2])*89300,abs(c[1]-b[1])*111320,abs(c[1]-b[3])*111320) for b in detail_bounds if b[0]-.001<c[0]<b[2]+.001 and b[1]-.001<c[1]<b[3]+.001) if any(b[0]-.001<c[0]<b[2]+.001 and b[1]-.001<c[1]<b[3]+.001 for b in detail_bounds) else float('inf')
def add(f,raw,walk_only=False):
 p=f['properties'];h=p.get('highway',p.get('subclass',p.get('class','')))
 if p.get('access') in ['private','no'] or h in ['rail','railway','aerialway','ferry','construction']:return
 walk=h not in ['motorway','motorway_link','trunk','trunk_link'] and p.get('foot')!='no';drive=not walk_only and h not in ['path','footway','pedestrian','cycleway','steps','bridleway','track'] and p.get('motor_vehicle')!='no'
 if not walk and not drive:return
 ls=[f['geometry']['coordinates']] if f['geometry']['type']=='LineString' else f['geometry']['coordinates']
 for line in ls:
  for a,b in zip(line,line[1:]):
   if not all(128.50<c[0]<128.785 and 36.525<c[1]<36.595 for c in [a,b]):continue
   if not raw and inside(a) and inside(b):continue
   u,v=node(a,raw),node(b,raw)
   if u==v:continue
   oneway=str(p.get('oneway','')).lower();forward=drive and oneway!='-1';back=drive and oneway not in ['1','yes','true']
   edges.append([u,v,round(distance(a,b),2),int(walk),int(forward),int(back),str(f['id']) if p.get('bridge') and p.get('bridge')!='no' else '',h])
for f in m['transportation']:add(f,False)
for f in detail['roads']:add(f,True)
for region in regional_details:
 for f in region['roads']:add(f,True,walk_only=True)
# Only join the two map sources at the detailed-area boundary, at most 35 m.
rawboundary=[i for i in rawset if boundary_distance(nodes[i])<100]
joincount=0
for u in globalset-rawset:
 if not rawboundary:break
 if boundary_distance(nodes[u])>50:continue
 v=min(rawboundary,key=lambda i:distance(nodes[u],nodes[i]));d=distance(nodes[u],nodes[v])
 if d<35:edges.append([u,v,round(d,2),1,1,1,'join']);joincount+=1
# Cached OSRM/OSM driving geometry bridges a disconnected regional tile graph.
regional=ROOT/'andong-atlas/.cache/hahoe-road-route.json'
if not regional.exists():
 import urllib.request
 url='https://router.project-osrm.org/route/v1/driving/128.520824,36.540239;128.728,36.5655?overview=full&geometries=geojson&steps=false'
 with urllib.request.urlopen(url,timeout=30) as response: response_data=json.load(response)
 if response_data.get('code')!='Ok':raise RuntimeError('Regional route unavailable; retain the existing generated journey.json')
 regional.parent.mkdir(parents=True,exist_ok=True)
 regional.write_text(json.dumps({'source':url,'data':response_data}))
if regional.exists():
 rd=json.loads(regional.read_text())['data']['routes'][0]['geometry']['coordinates']
 ids=[node(c,False) for c in rd]
 for u,v in zip(ids,ids[1:]):edges.append([u,v,round(distance(nodes[u],nodes[v]),2),0,1,0,''])
 end=ids[-1];v=min(rawset,key=lambda i:distance(nodes[end],nodes[i]))
 if distance(nodes[end],nodes[v])<35:edges.append([end,v,round(distance(nodes[end],nodes[v]),2),0,1,0,'join'])
bus=json.loads((ROOT/'data/external/작업목록_1-12_보강_20260922/01_시내버스/api_bus_stops.json').read_text());stops=[{'id':str(s['stopId']),'name':s['stopName'],'coordinates':[s['lng'],s['lat']]} for s in bus if 128.67<s['lng']<128.78 and 36.55<s['lat']<36.59]
result={'places':catalog,'unlocatedBenefits':unmatched,'stops':stops,'network':{'nodes':nodes,'edges':edges},'source':'OSM/OpenFreeMap 2026.09 · 안동 BIS 2026.09 수집 · 가맹 목록·체험 조사','regionalSource':'OSRM / OpenStreetMap 공개 도로 경로 · 2026.09.28 저장 · 하회마을→원도심', 'routeNote':'공개 도로망을 잇는 설명 경로. 실제 버스 운행 경로·교통 상황과 다를 수 있습니다. 지도 자료 경계 연결 '+str(joincount)+'개.'}
(OUT/'journey.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
print('places',len(catalog),'benefits',sum(bool(p.get('benefit')) for p in catalog),'unlocated',len(unmatched),'nodes',len(nodes),'edges',len(edges),'joins',joincount)
