"""Cache explicitly licensed photographic references; preserve originals and attribution."""
import json, hashlib, urllib.request, re
from pathlib import Path
import argparse, time
ROOT=Path(__file__).resolve().parents[1]
existing=json.loads((ROOT/'public/data/place-media.json').read_text())['photos']
photos=[dict(existing[k]) for k in ['tour-2866691','tour-2679452','tour-134770','moon','hahoe','station']]
next(p for p in photos if p['id']=='hahoe')['caption']='하회마을 한옥 경관 · 공간과 전통 건축 참고'
photos.append(dict(id='mask',src='https://upload.wikimedia.org/wikipedia/commons/5/5c/Korean_mask-Hahoe_mask-02.jpg',sourceUrl='https://commons.wikimedia.org/wiki/File:Korean_mask-Hahoe_mask-02.jpg',credit='Julie',license='CC BY-SA 2.0',licenseUrl='https://creativecommons.org/licenses/by-sa/2.0/',capturedAt='2008-05-25',caption='하회탈 · 실제 탈의 표정과 재료 참고',provider='Wikimedia Commons'))
photos.append(dict(id='maskdance',src='https://upload.wikimedia.org/wikipedia/commons/a/a2/Hahoe_8747.jpg',sourceUrl='https://commons.wikimedia.org/wiki/File:Hahoe_8747.jpg',credit='Idobi',license='CC BY-SA 3.0',licenseUrl='https://creativecommons.org/licenses/by-sa/3.0/',capturedAt='2012-09-28',caption='하회별신굿탈놀이 · 전통 공연 참고',provider='Wikimedia Commons'))
for entry in [
 ('jjimdak','5/57/Korean_cuisine-Andong_jjimdak-01.jpg','Korean_cuisine-Andong_jjimdak-01.jpg','shizu k (shezzz)','CC BY-SA 2.0','by-sa/2.0','2007-07-22','안동찜닭 · 음식 형태 참고, 시연 식당의 실제 메뉴 사진은 아님'),
 ('tea','b/b4/Gukwa-cha.jpg','Gukwa-cha.jpg','Jennifer Kang','CC BY 2.0','by/2.0','2013-11-19','국화차 · 꽃과 다기 참고, 안동 체험장 현장 사진은 아님'),
 ('soju','c/cc/Korean_distilled_liquor-Andong_soju-01.jpg','Korean_distilled_liquor-Andong_soju-01.jpg','Matt and Nayoung Wilson','CC BY 2.0','by/2.0','2007-10-10','민속주 안동소주 술병 · 체험 완성품과 표찰 참고')]:
 id,path,page,credit,license,slug,date,caption=entry
 photos.append(dict(id=id,src='https://upload.wikimedia.org/wikipedia/commons/'+path,sourceUrl='https://commons.wikimedia.org/wiki/File:'+page,credit=credit,license=license,licenseUrl='https://creativecommons.org/licenses/'+slug+'/',capturedAt=date,caption=caption,provider='Wikimedia Commons'))
def fetch(p):
 try:
  # Discover canonical original URL from the Commons file page rather than guessing a hash.
  if p['provider']=='Wikimedia Commons' and p['id'] not in {'jjimdak','tea','soju'}:
   page=urllib.request.urlopen(urllib.request.Request(p['sourceUrl'],headers={'User-Agent':'AndongEducationalPrototype/1.0'}),timeout=25).read().decode()
   (ROOT/'artifacts/relay/sources'/f"{p['id']}.html").write_text(page)
   match=re.search(r'class="fullImageLink"[^>]*>\s*<a href="([^"]+)"',page)
   if match:p['src']=match.group(1).replace('&amp;','&')
  raw=urllib.request.urlopen(urllib.request.Request(p['src'],headers={'User-Agent':'AndongEducationalPrototype/1.0'}),timeout=30).read()
  if raw[:2]!=b'\xff\xd8':raise ValueError('Not a JPEG')
  (ROOT/'public/media/relay'/f"{p['id']}.jpg").write_bytes(raw)
  p.update(local=f"/media/relay/{p['id']}.jpg",sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),collectedAt='2026-09-29',modifications='없음 · 원본 전체 표시')
  print(p['id'],len(raw),'OK')
 except Exception as e:
  p.update(local=None,downloadError=str(e)); print(p['id'],str(e))
 return p
parser=argparse.ArgumentParser()
parser.add_argument('--only',nargs='*')
args=parser.parse_args()
manifest=ROOT/'public/data/relay-media.json'
previous={p['id']:p for p in json.loads(manifest.read_text())} if manifest.exists() else {}
out=[]
for p in photos:
 old=previous.get(p['id'])
 if old and old.get('local') and (ROOT/'public'/old['local'].lstrip('/')).exists():
  out.append(old);continue
 if args.only and p['id'] not in args.only:
  out.append(old or dict(p,local=None));continue
 out.append(fetch(p))
 time.sleep(2)
(ROOT/'public/data/relay-media.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
