import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
source=root/'raw/relay_full.webm'
events={row['name']:row['time'] for row in json.loads((root/'production/capture-events.json').read_text())}
duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(source)]))
offset=events['session_end']-duration
names={'S03':'골목에서_식당으로','S04':'찜닭_직접식사','S05':'결제와_영수증수령','S06':'QR인증과_할인권','S07a':'체험할인권_사용','S07b':'하회탈_붓질과완성','S08':'월영교로_이동','S11a':'월영밤마당_산책','S11b':'국화차_구매와맛보기'}
manifest=[]
for key,name in names.items():
    start=events[key+'_start']-offset
    length=events[key+'_end']-events[key+'_start']
    dest=root/'clips'/f'{key}_{name}.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(source),'-i',str(root/'raw'/f'{key}_audio.webm'),'-t',str(length),'-map','0:v:0','-map','1:a:0','-vf','crop=1916:1076:2:2,scale=1920:1080:flags=lanczos,fps=30','-af','aresample=48000,apad','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(dest)],check=True)
    manifest.append({'id':key,'file':dest.name,'duration':length,'sourceStart':start,'source':'raw/relay_full.webm','sourceFPS':25,'outputFPS':30,'audio':'native synthesized app sounds','syncOffset':offset})
    print(key,round(length,2),flush=True)
(root/'production/recorded-clips.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
