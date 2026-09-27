import json, pathlib, math, heapq
root=pathlib.Path(__file__).resolve().parents[2]; out=root/'andong-atlas/public/data'
s=json.loads((root/'보고서/성과도출_20260922/시뮬레이션결과.json').read_text()); q=json.loads((root/'보고서/교수브리핑_20260922/수치.json').read_text()); m=json.loads((out/'district.json').read_text())
# Route follows the downloaded road network, not a claimed bus service itinerary.
g={}; coords={}
def key(c):return (round(c[0],7),round(c[1],7))
def dist(a,b):return math.hypot((a[0]-b[0])*.803,a[1]-b[1])
for f in m['roads']:
 if f['properties'].get('highway') in ['path','footway','pedestrian','cycleway','steps','bridleway'] or f['properties'].get('access')=='private' or f['properties'].get('motor_vehicle')=='no':continue
 ls=[f['geometry']['coordinates']] if f['geometry']['type']=='LineString' else f['geometry']['coordinates']
 for line in ls:
  for a,b in zip(line,line[1:]):
   if not (128.71<a[0]<128.78 and 36.55<a[1]<36.60):continue
   u,v=key(a),key(b);coords[u]=a;coords[v]=b;w=dist(a,b)
   g.setdefault(u,[]).append((v,w));g.setdefault(v,[]).append((u,w))
start=min(g,key=lambda c:dist(c,[128.728,36.5655]));end=min(g,key=lambda c:dist(c,[128.758095,36.5767]));heap=[(0,start)];cost={start:0};prev={}
while heap:
 d,u=heapq.heappop(heap)
 if u==end:break
 if d!=cost[u]:continue
 for v,w in g[u]:
  if d+w<cost.get(v,float('inf')):cost[v]=d+w;prev[v]=u;heapq.heappush(heap,(d+w,v))
if end not in cost:raise RuntimeError('Road network is disconnected: do not invent route')
route=[end]
while route[-1]!=start:route.append(prev[route[-1]])
route=[coords[k] for k in route[::-1]]
result={'plans':{k:s[k] for k in ['기본안','확대안']},'resident':{'currentMonthly':q['주민증']['월평균'][-1]['월평균'],'addedMonthlyExpanded':s['p근거']['하한_주민증GLM']*s['고정값']['중구동_월방문']},'route':route,'routeNote':'공개 도로망 연결 시각화 · 실제 112번 노선·확정 셔틀 경로 아님','sites':[{'id':'market','name':'원도심 인증·체험 거점','coordinates':[128.728,36.5655],'note':'팀 분석 기준점 · 참여 업소와 설치 지점 미확정'},{'id':'popup','name':'월영교 야간 팝업','coordinates':[128.758095,36.5767],'note':'월영교 서측 주차장 권역의 제안 모형 · OSM 76992439 기준 · 점유·부지 사용 확정 아님'}],'source':'시뮬레이션결과.json · 2026-09-27 갱신 · 연간 12개월'}
(out/'solution.json').write_text(json.dumps(result,ensure_ascii=False));print('Road vertices',len(route),'plans exported')
