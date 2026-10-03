from pathlib import Path
import subprocess,json,csv
root=Path(__file__).resolve().parents[1]; clips=root/'clips'; tmp=root/'production'/'assembly';tmp.mkdir(exist_ok=True)
def run(args):subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y']+args,check=True)
for name,src in [('S06b_할인권발급_실제화면홀드.mp4','S06-coupon.png'),('S07c_할인적용_실제화면홀드.mp4','S07a-discount.png')]:
 run(['-loop','1','-framerate','30','-i',str(root/'stills'/src),'-t','3','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(clips/name)])
# Relative source time and duration. All source holds are identified explicitly.
cut=[('S01','S01_안동_3D전경.mp4',1,5),('S02','S02_원도심으로_줌인.mp4',1,5),('S03','S03_골목에서_식당으로.mp4',10,5),('S04','S04_찜닭_직접식사.mp4',1.3,6),('S05','S05_결제와_영수증수령.mp4',.8,5),('S06','S06_QR인증과_할인권.mp4',.5,6.5),('S06b','S06b_할인권발급_실제화면홀드.mp4',0,2.5),('S07a','S07c_할인적용_실제화면홀드.mp4',0,2),('S07b','S07b_하회탈_붓질과완성.mp4',1,4),('S07c','S07b_하회탈_붓질과완성.mp4',24.5,2),('S08','S08_월영교로_이동.mp4',2,6),('S09','S09_월영교_첫전경.mp4',1,7),('S10','S10_월영교_산책.mp4',1,7),('S11a','S11a_월영밤마당_산책.mp4',2,3),('S11b','S11c_국화차_맛보기_30fps.mp4',.5,5),('S12','S12_수면반사에서_월영교로.mp4',1,8),('S13','S13_S14_월영교_엔딩전경.mp4',0,7),('S14','S13_S14_월영교_엔딩전경.mp4',7,4)]
rows=[];t=0
for n,(id,f,start,duration) in enumerate(cut):
 src=clips/f; dest=tmp/f'{n:02d}.mp4'
 probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-of','json',str(src)]))
 has_audio=any(s['codec_type']=='audio' for s in probe['streams'])
 args=['-ss',str(start),'-i',str(src)]
 if not has_audio:args+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
 args+=['-map','0:v:0','-map','0:a:0' if has_audio else '1:a:0','-t',str(duration),'-vf','fps=30,setsar=1','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2','-af','apad','-movflags','+faststart',str(dest)]
 run(args);rows.append({'cut':id,'timeline_start':t,'duration':duration,'file':'clips/'+f,'source_in':start,'source_out':start+duration,'note':'Actual captured still hold' if '홀드' in f else 'Actual app capture'});t+=duration
 print(id,flush=True)
assert t==90,t
(root/'cutlist.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
with (root/'cutlist.csv').open('w',encoding='utf-8-sig',newline='') as fp:
 w=csv.DictWriter(fp,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(tmp/'concat.txt').write_text(''.join("file '"+str(tmp/f'{n:02d}.mp4')+"'\n" for n in range(len(cut))))
run(['-f','concat','-safe','0','-i',str(tmp/'concat.txt'),'-t','90','-c:v','copy','-c:a','aac','-ar','48000','-movflags','+faststart',str(root/'안동이어드림_90초_촬영연결본.mp4')])
print('DONE 90s',flush=True)
