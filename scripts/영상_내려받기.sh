#!/usr/bin/env bash
# 5MB 넘는 영상·zip을 GitHub Releases(media-20261003)에서 받아 원래 경로에 놓는다.
# 목록과 SHA-256은 보고서/대용량_영상_목록.csv. 이미 같은 파일이 있으면 건너뛴다.
# 사용: bash scripts/영상_내려받기.sh            (전부)
#       bash scripts/영상_내려받기.sh renders    (경로에 'renders'가 들어간 것만, 예: 완성본만)
set -euo pipefail
cd "$(dirname "$0")/.."
FILTER="${1:-}"
python3 - "$FILTER" <<'EOF'
import csv, hashlib, os, subprocess, sys
flt = sys.argv[1]
rows = list(csv.DictReader(open("보고서/대용량_영상_목록.csv", encoding="utf-8")))
for r in rows:
    p = r["path"]
    if flt and flt not in p:
        continue
    if os.path.exists(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == r["sha256"]:
        print("있음  ", p)
        continue
    os.makedirs(os.path.dirname(p), exist_ok=True)
    print("받는 중", p, f'({int(r["bytes"]) / 2**20:.0f}MB)')
    subprocess.run(["curl", "-fL", "--retry", "3", "-o", p, r["url"]], check=True)
    if hashlib.sha256(open(p, "rb").read()).hexdigest() != r["sha256"]:
        sys.exit(f"SHA-256 불일치: {p}")
print("완료")
EOF
