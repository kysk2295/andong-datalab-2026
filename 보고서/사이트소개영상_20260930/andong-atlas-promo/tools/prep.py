"""timeline.json의 컷을 원본에서 잘라 assets/cut/<id>.mp4로 만든다(1920×1080·30fps·소리 없음)."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "tools" / "timeline.json").read_text(encoding="utf-8"))
for s in PLAN["shots"]:
    src = (ROOT / s["src"]).resolve()
    out = ROOT / "assets" / "cut" / f"{s['id']}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(s["ss"]), "-i", str(src), "-t", str(s["dur"]),
                    "-vf", "scale=1920:1080:flags=lanczos,fps=30", "-an", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "16", "-pix_fmt", "yuv420p", "-g", "30", "-movflags", "+faststart", str(out)], check=True)
    print(s["id"], "←", src.name)
