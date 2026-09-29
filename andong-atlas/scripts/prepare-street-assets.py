import json,pathlib,xml.etree.ElementTree as E
p=pathlib.Path(__file__).resolve().parents[1];r=E.parse(p/'.cache/detail/osm.xml').getroot();d=json.loads((p/'public/data/district.json').read_text());b=d['bbox'];items=[]
for n in r.findall('node'):
 t={v.get('k'):v.get('v') for v in n.findall('tag')};c=[float(n.get('lon')),float(n.get('lat'))]
 if t.get('highway') in ['crossing','bus_stop'] and b[0]<=c[0]<=b[2] and b[1]<=c[1]<=b[3]:items.append({'coordinates':c,'kind':t['highway'],'name':t.get('name',''),'source':'OpenStreetMap','id':n.get('id')})
d['streetAssets']=items;(p/'public/data/district.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')));print('mapped street assets',len(items))
