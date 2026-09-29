"""Cache CC0 surfaces/models with checksums; never substitutes an unrelated cultural prop."""
import json,subprocess,hashlib,pathlib,concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[1]
REF=ROOT/'artifacts/relay/v7/references';REF.mkdir(parents=True,exist_ok=True)
def get(url,path):
 path.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','-L','--retry','2','-sS','-A','AndongAtlas/1.0',url,'-o',str(path)],check=True)
 return path.read_bytes()
def api(asset):
 p=REF/(asset+'-files.json');get('https://api.polyhaven.com/files/'+asset,p);return json.loads(p.read_text())
manifest=json.loads((ROOT/'public/data/relay-materials.json').read_text())
jobs=[]
for asset in ['wood_table','brick_wall_001','fabric_pattern_05']:
 files=api(asset)
 for key,kind in [('Diffuse','diffuse'),('nor_gl','nor_gl'),('Rough','rough')]:
  aliases={'Diffuse':['Diffuse','diff','diffuse','col_01'],'Rough':['Rough','rough'],'nor_gl':['nor_gl']};actual=next(k for k in aliases[key] if k in files);item=files[actual]['1k']['jpg'];file='/assets/relay/materials/'+asset+'_'+kind+'.jpg';jobs.append((asset,kind,item,file))
def material(job):
 asset,kind,item,file=job;data=get(item['url'],ROOT/('public'+file));assert hashlib.md5(data).hexdigest()==item['md5']
 return dict(asset=asset,kind=kind,file=file,source='https://polyhaven.com/a/'+asset,download=item['url'],license='CC0-1.0',licenseUrl='https://polyhaven.com/license',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:added=list(pool.map(material,jobs))
keys={(a['asset'],a['kind']) for a in added};manifest=[a for a in manifest if (a['asset'],a['kind']) not in keys]+added
(ROOT/'public/data/relay-materials.json').write_text(json.dumps(manifest,indent=2)+'\n')
asset='wooden_bowl_01';item=api(asset)['gltf']['1k']['gltf'];base='/assets/relay/models/'+asset+'/'
items=[(asset+'.gltf',item)]+list(item['include'].items());model=[]
for name,entry in items:
 data=get(entry['url'],ROOT/('public'+base+name));assert hashlib.md5(data).hexdigest()==entry['md5'];model.append(dict(file=base+name,download=entry['url'],bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
(ROOT/'public/data/relay-model-assets.json').write_text(json.dumps([dict(id=asset,source='https://polyhaven.com/a/'+asset,license='CC0-1.0',licenseUrl='https://polyhaven.com/license',file=base+asset+'.gltf',files=model)],indent=2)+'\n')
print('Downloaded',len(added),'PBR maps and',len(model),'model files;',sum(a['bytes'] for a in added+model),'bytes')
