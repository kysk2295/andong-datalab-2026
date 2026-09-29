"""Link verified public photographs and factual source records; never invent reviews."""
import json,re,urllib.request,urllib.parse
from restaurant_identity import same_business
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'andong-atlas'
plain=lambda s:re.sub('<[^>]*>',' ',s or '').strip()
norm=lambda s:re.sub(r'\s|[()·-]','',s)
journey=json.loads((APP/'public/data/journey.json').read_text())
cache=APP/'.cache/place-media/commons.json'
if not cache.exists():
 titles=['File:Woryeong Bridge Andong.JPG','File:Hahoe 8784.jpg','File:20211114 안동역 승강장.jpg']
 url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|extmetadata','iiurlwidth':1280,'titles':'|'.join(titles)})
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AndongAtlas/1.4 (tourism research)'}),timeout=20) as r:data=json.load(r)
 cache.parent.mkdir(parents=True,exist_ok=True);cache.write_text(json.dumps(data,ensure_ascii=False))
commons=json.loads(cache.read_text()); photos={}; records={}
for page in commons['query']['pages'].values():
 title=page['title'];info=page['imageinfo'][0];meta=info['extmetadata'];photo_id={'File:Woryeong Bridge Andong.JPG':'moon','File:Hahoe 8784.jpg':'hahoe','File:20211114 안동역 승강장.jpg':'station'}[title]
 photos[photo_id]={'id':photo_id,'src':info['thumburl'].split('?')[0],'sourceUrl':info['descriptionurl'],'credit':'Idobi' if photo_id=='hahoe' else plain(meta['Artist']['value']),'license':meta['LicenseShortName']['value'],'licenseUrl':meta['LicenseUrl']['value'],'capturedAt':plain(meta['DateTimeOriginal']['value'])[:10],'caption':{'moon':'월영교 전경','hahoe':'하회마을 전경 · 출발 정류장 사진과는 다릅니다','station':'현재 위치로 이전한 안동역 승강장'}[photo_id],'provider':'Wikimedia Commons','view':'photo'}
for p in journey['places']:
 photo_id='moon' if p['id'] in ['bridge','bridge-east'] else p['id'] if p['id'] in ['station','hahoe'] else 'hahoe' if p['name']=='하회마을' else None
 if photo_id:records[p['id']]={'photos':[photo_id]}
base=ROOT/'data/external/작업목록_1-12_보강_20260922/12_영업시간'
foods=json.loads((base/'tourapi_andong_food_list.json').read_text()); details=json.loads((base/'tourapi_andong_food_detailIntro.json').read_text())
for p in journey['places']:
 matches=[r for r in foods if same_business(p,r)]
 if len(matches)!=1:continue
 r=matches[0];record=records.setdefault(p['id'],{'photos':[]});detail=next((d for d in details if d['contentid']==r['contentid']),{})
 record['official']={'provider':'한국관광공사 TourAPI','sourceUrl':'https://api.visitkorea.or.kr/','contentId':r['contentid'],'collectedAt':'2026-09-22','updatedAt':r['modifiedtime'][:4]+'-'+r['modifiedtime'][4:6]+'-'+r['modifiedtime'][6:8],'hours':plain(detail.get('opentimefood')),'restDays':plain(detail.get('restdatefood')),'phone':plain(detail.get('infocenterfood'))}
 if r['firstimage'] and r['cpyrhtDivCd'] in ['Type1','Type3']:
  photo_id='tour-'+r['contentid'];photos[photo_id]={'id':photo_id,'src':r['firstimage'].replace('http://','https://'),'sourceUrl':r['firstimage'].replace('http://','https://'),'provider':'한국관광공사 TourAPI','credit':'한국관광공사','contentId':r['contentid'],'license':'공공누리 제'+r['cpyrhtDivCd'][-1]+'유형','licenseUrl':'https://www.kogl.or.kr/info/licenseType'+r['cpyrhtDivCd'][-1]+'.do','capturedAt':None,'updatedAt':record['official']['updatedAt'],'caption':p['name']+' · 공식 관광정보 제공 사진','view':'photo'};record['photos'].append(photo_id)
output={'version':1,'checkedAt':'2026-09-29','photos':photos,'records':records,'reviews':[],'reviewStatus':'not_connected'}
(APP/'public/data/place-media.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print('public photographs',len(photos),'linked places',sum(bool(r['photos']) for r in records.values()),'reviews',0)
