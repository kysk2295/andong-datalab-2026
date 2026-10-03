from pathlib import Path
import subprocess,json,zipfile
r=Path('보고서/영상촬영_20260930');v=r/'안동이어드림_90초_촬영연결본.mp4';tmp=r/'production'/'final-exact.mp4'
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(v),'-vf','setpts=PTS-STARTPTS,fps=30:start_time=0,tpad=stop_mode=clone:stop_duration=1,setpts=N/(30*TB)','-frames:v','2700','-t','90','-r','30','-fps_mode','cfr','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-af','asetpts=PTS-STARTPTS,apad','-c:a','aac','-ar','48000','-movflags','+faststart',str(tmp)],check=True)
tmp.replace(v)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(v)]));(r/'production'/'final-probe.json').write_text(json.dumps(probe,indent=2))
s=next(s for s in probe['streams'] if s['codec_type']=='video');print({k:s.get(k) for k in ('nb_frames','duration','r_frame_rate')},flush=True)
assert s['nb_frames']=='2700' and s['width']==1920 and s['height']==1080
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(v),'-f','null','-'],check=True)
(r/'검수결과.md').write_text('''# 촬영본 검수\n\n- 영상: 1920×1080, 30fps, 2,700프레임, 90초. H.264 / AAC.\n- 전체 MP4 디코딩 오류 없음.\n- 18개 대표 시점에서 지도, 줌인, 식사, 영수증, QR, 할인권 발급·적용, 탈 완성, 이동, 월영교·밤마당, 엔딩 확인. `촬영연결본_장면확인.jpg` 참고.\n- QR 인증과 할인권·탈 체험을 실제 앱 흐름으로 수행. 할인 패널 2개는 동일 체험의 실제 캡처 정지 화면으로 보완.\n- 초기 촬영 중 페이지 갱신으로 촬영용 연결 객체가 해제되는 오류 1건이 있었고, 페이지 연결 복구 후 이어서 촬영. 최종 MP4에서는 해당 오류 화면이 보이지 않음.\n- 이 파일은 자막·음악·전환을 완성하기 전의 촬영 연결본. 현장 실사가 아닌 3D 웹 제안 시연.\n''')
z=r.parent/'안동이어드림_클로드전달_촬영패키지.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as f:
 for p in sorted(r.rglob('*')):
  if p.is_file() and not any(x in ('raw','production') for x in p.relative_to(r).parts):f.write(p,Path('안동이어드림_촬영패키지')/p.relative_to(r))
print(json.dumps({'video_mb':round(v.stat().st_size/1e6,1),'zip_mb':round(z.stat().st_size/1e6,1),'clips':len(list((r/'clips').glob('*.mp4')))},ensure_ascii=False))
