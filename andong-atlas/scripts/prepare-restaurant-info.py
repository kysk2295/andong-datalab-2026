"""Reuse verified collected sources; missing practical information stays unknown."""
import csv
import json
import re
from pathlib import Path
from restaurant_identity import same_business, normalize, address

APP=Path(__file__).resolve().parents[1];ROOT=APP.parent
base=ROOT/'data/external/작업목록_1-12_보강_20260922/12_영업시간'
foods=json.loads((base/'tourapi_andong_food_list.json').read_text())
details=json.loads((base/'tourapi_andong_food_detailIntro.json').read_text())
guide=list(csv.DictReader((ROOT/'조사/12_원도심_식당영업시간_공식목록.csv').open(encoding='utf-8-sig')))
journey=json.loads((APP/'public/data/journey.json').read_text())
records={}
for p in journey['places']:
    if p['kind']!='restaurant':continue
    r={'id':p['id'],'name':p['name'],'address':p.get('address'), 'waiting':None,'price':None,'parking':None,'children':None}
    # All shop-* entries originated in the alley guide, including unresolved
    # phone/address joins. None may inherit the guide's hours as store hours.
    if p['id'].startswith('shop-'):
        area_hours=p.get('areaHours') or (p.get('hours') if re.fullmatch(r'\d{1,2}:\d{2}[~–-]\d{1,2}:\d{2}',p.get('hours','')) else None)
        if area_hours:r['areaHours']=area_hours;p['areaHours']=area_hours
        p['hours']='점포별 영업시간 확인 필요';p.pop('open',None);p.pop('close',None)
    guides=[g for g in guide if normalize(g['공식상호'])==normalize(p['name']) and address(g['상권_도로명주소'])==address(p.get('address'))]
    if len(guides)==1:
        g=guides[0]
        r.update(phone=g['공식연락처'],phoneSource=g['출처URL'],phoneCollectedAt='2026-09-22',areaHours=g['골목안내_영업시간'],area=g['구역'])
        # Remove old alley hours from the exported catalogue as well as the UI.
        p.update(hours='점포별 영업시간 확인 필요',areaHours=g['골목안내_영업시간'])
        p.pop('open',None);p.pop('close',None)
    matches=[f for f in foods if same_business(p,f)]
    if len(matches)==1:
        f=matches[0];d=next((v for v in details if v['contentid']==f['contentid']),{})
        plain=lambda s:re.sub('<[^>]*>',' ',s or '').strip()
        r.update(contentId=f['contentid'],hours=plain(d.get('opentimefood')),restDays=plain(d.get('restdatefood')),phone=plain(d.get('infocenterfood')) or r.get('phone'),provider='한국관광공사 TourAPI',source='https://api.visitkorea.or.kr/',collectedAt='2026-09-22',updatedAt=f['modifiedtime'][:8])
        if p['name']=='중앙찜닭':
            r.update(source='https://chinese.visitkorea.or.kr/svc/whereToGo/locIntrdn/rgnContentsView.do?vcontsId=215200',checkedAt='2026-09-29')
        p['hours']=r['hours']+' · 휴무: '+(r['restDays'] or '확인 필요')
        p.pop('open',None);p.pop('close',None)
        # Only a single unqualified daily time interval is safe to parse.
        m=re.fullmatch(r'(\d{1,2}):(\d{2})\s*[~–-]\s*(\d{1,2}):(\d{2})',r['hours'])
        if m and r['restDays'] in ['연중무휴','없음']:
            a,b,c,d=map(int,m.groups());r['open']=a*60+b;r['close']=c*60+d
            p.update(open=r['open'],close=r['close'])
    records[p['id']]=r
(APP/'public/data/restaurant-info.json').write_text(json.dumps({'version':1,'records':records},ensure_ascii=False,indent=2)+'\n')
(APP/'public/data/journey.json').write_text(json.dumps(journey,ensure_ascii=False,separators=(',',':'))+'\n')
print('Restaurants',len(records),'individual hours',sum(bool(r.get('hours')) for r in records.values()),'phones',sum(bool(r.get('phone')) for r in records.values()))
