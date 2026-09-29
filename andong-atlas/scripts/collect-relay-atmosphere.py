"""Source-verified CC0 canopy, ground and lighting maps for the playable scene."""
import pathlib,json,subprocess,hashlib,concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[1]
REF=ROOT/'artifacts/relay/v9/references';REF.mkdir(parents=True,exist_ok=True)
def fetch(url,p):
 p.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','-L','-sS','--max-time','60','-A','AndongAtlas/1.0',url,'-o',str(p)],check=True)
 return p.read_bytes()
def api(name):
 p=REF/(name+'.json');fetch('https://api.polyhaven.com/files/'+name,p);return json.loads(p.read_text())
jobs=[]
pine=api('pine_tree_01')
for prefix,name in [('twig','pine_needles'),('bark','pine_bark')]:
 for suffix,kind in [('diff','diffuse'),('nor_gl','nor_gl'),('rough','rough')]+([('alpha','alpha')] if prefix=='twig' else []):
  item=pine[prefix+'_'+suffix]['2k' if suffix in ('diff','alpha') else '1k']['jpg'];jobs.append((name,kind,'pine_tree_01',item,'.jpg'))
forest=api('forest_ground_04')
for key,kind in [('diff','diffuse'),('nor_gl','nor_gl'),('rough','rough')]:
 actual=next(k for k in forest if k.lower() in [key,{'diff':'diffuse'}.get(key,key)]);jobs.append(('forest_ground_04',kind,'forest_ground_04',forest[actual]['1k']['jpg'],'.jpg'))
for sky,res in [('qwantani_night_puresky','2k'),('studio_small_09','1k')]:
 j=api(sky);jobs.append((sky,'hdri',sky,j['hdri'][res]['hdr'],'.hdr'))
def download(j):
 name,kind,source,item,ext=j;file='/assets/relay/materials/'+name+'_'+kind+ext;p=ROOT/('public'+file);data=fetch(item['url'],p)
 assert hashlib.md5(data).hexdigest()==item['md5']
 return dict(asset=name,kind=kind,file=file,source='https://polyhaven.com/a/'+source,download=item['url'],license='CC0-1.0',licenseUrl='https://polyhaven.com/license',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: added=list(pool.map(download,jobs))
p=ROOT/'public/data/relay-materials.json';existing=json.loads(p.read_text());keys={(a['asset'],a['kind']) for a in added};p.write_text(json.dumps([a for a in existing if (a['asset'],a['kind']) not in keys]+added,indent=2)+'\n')
print('Verified',len(added),'CC0 files,',round(sum(a['bytes'] for a in added)/1e6,2),'MB')
