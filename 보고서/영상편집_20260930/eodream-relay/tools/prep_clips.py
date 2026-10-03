"""timeline.json의 컷마다 1.3배속·흔들림 보정을 적용한 편집용 클립을 assets/cut/<id>.mp4로 만든다.

실행: python3 tools/edit_plan.py && python3 tools/prep_clips.py [컷id ...]
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
plan = json.loads((ROOT / "tools" / "timeline.json").read_text(encoding="utf-8"))
SPEED = plan["speed"]
OUT = ROOT / "assets" / "cut"
OUT.mkdir(parents=True, exist_ok=True)

MODE_VF = {
    # 실제 렌더 프레임: 속도만 올리고 30fps로 솎음
    "frame": f"setpts=(PTS-STARTPTS)/{SPEED},fps=30",
    "static": f"setpts=(PTS-STARTPTS)/{SPEED},fps=30",
    # 25fps 녹화(6장마다 1장 중복)·고유 프레임이 드문 녹화: 중복 프레임을 버리고(원래 시각 유지)
    # 움직임 보간으로 사이를 채운다. 큰 움직임에서 보간을 건너뛰지 않게 장면 전환 감지(scd)는 끈다.
    "rt25": (f"mpdecimate=hi=64*4:lo=64*1:frac=0.15,setpts=(PTS-STARTPTS)/{SPEED},"
             "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=none"),
    # 손 동작(식사·결제·QR·국화차): 멈춘 프레임을 최대 4장까지만 버리고 움직임 보간.
    # 상한을 둬서 오래 멈춘 구간에서 손이 천천히 미끄러지는 가짜 움직임이 생기지 않게 한다.
    "hand": (f"mpdecimate=max=4,setpts=(PTS-STARTPTS)/{SPEED},"
             "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=none"),
    # 하회탈 색칠: 칠이 가끔 한 번씩 생겨 뚝뚝 끊김 → 멈춘 프레임을 버리고 사이를 섞어 서서히 칠해지게
    "paint": f"mpdecimate=hi=64*2:lo=64*0.5:frac=0.02:max=40,setpts=(PTS-STARTPTS)/{SPEED},minterpolate=fps=30:mi_mode=blend",
    "lowfps": (f"mpdecimate=hi=64*6:lo=64*2:frac=0.2,setpts=(PTS-STARTPTS)/{SPEED},"
               "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=none"),
}


def build(shot):
    nframes = round(shot["dur"] * 30)
    out = OUT / f'{shot["id"]}.mp4'
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if shot["mode"] == "hold":
        f, a, b = shot["parts"][0]
        cmd += ["-ss", str(a), "-i", str(ROOT / "assets" / "clips" / f"{f}.mp4"),
                "-vf", "fps=30,tpad=stop_mode=clone:stop_duration=5"]
    else:
        filt, labels = [], []
        for i, (f, a, b) in enumerate(shot["parts"]):
            cmd += ["-i", str(ROOT / "assets" / "clips" / f"{f}.mp4")]
            filt.append(f"[{i}:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[p{i}]")
            labels.append(f"[p{i}]")
        chain = "".join(labels) + (f"concat=n={len(labels)}:v=1:a=0" if len(labels) > 1 else "null")
        filt.append(f"{chain},{MODE_VF[shot['mode']]},tpad=stop_mode=clone:stop_duration=1[v]")
        cmd += ["-filter_complex", ";".join(filt), "-map", "[v]"]
    cmd += ["-an", "-frames:v", str(nframes), "-r", "30", "-c:v", "libx264", "-preset", "medium",
            "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    print(f'{shot["id"]}: {nframes} frames ({shot["mode"]})')


if __name__ == "__main__":
    want = set(sys.argv[1:])
    for s in plan["shots"]:
        if not want or s["id"] in want:
            build(s)
