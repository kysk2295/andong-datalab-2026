"""Build source-attributed regional photos from previously fetched Commons metadata."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
plain=lambda s:re.sub(r'\s+',' ',re.sub('<[^>]*>',' ',s or '')).strip()
base=json.loads((ROOT/'public/data/place-media.json').read_text())
photos={};records={}
choices=[('dosan','Dosan-Seowon','File:Korea-Andong-Dosan Seowon-01.jpg','도산서원 경내 · 권역 참고 사진','2008-05-25'),('byeongsan','Byeongsan-Seowon','File:병산서원-1.jpg','병산서원 전경 · 권역 참고 사진','2016-09-15'),('bongjeong','Bongjeongsa-Geungnakjeon','File:Korea-Andong-Bongjeongsa 3040-06 Geungnakjeon.JPG','봉정사 극락전','2006-05-11')]
for region,cache,title,caption,date in choices:
 pages=json.loads((ROOT/'.cache/place-media'/f'{cache}.json').read_text())['query']['pages'].values()
 page=next(p for p in pages if p['title']==title);info=page['imageinfo'][0];meta=info['extmetadata'];key='heritage-'+region
 photos[key]={'id':key,'src':info['thumburl'].split('?')[0],'sourceUrl':info['descriptionurl'],'credit':plain(meta['Artist']['value']),'license':meta['LicenseShortName']['value'],'licenseUrl':meta['LicenseUrl']['value'],'capturedAt':date,'caption':caption,'provider':'Wikimedia Commons','view':'photo'}
for region in ['hahoe','dosan','byeongsan','bongjeong']:
 data=json.loads((ROOT/f'public/data/regions/{region}.json').read_text())
 key='hahoe' if region=='hahoe' else 'heritage-'+region
 for p in data['heritageDetail']['sites']:
  records[region+':'+p['id']]={'photos':[key],'photoScope':'place' if region=='bongjeong' and p['name']=='극락전' else 'region'}
 records[region]={'photos':[key],'photoScope':'region'}
(ROOT/'public/data/heritage-media.json').write_text(json.dumps({'checkedAt':'2026-09-29','photos':photos,'records':records},ensure_ascii=False,indent=2)+'\n')
print('Added licensed photographs:',len(photos),'linked heritage records:',len(records))
