"""클립별 흔들림 측정: 연속 프레임 사이 화면 이동량(위상 상관)에서 부드러운 카메라 이동을 뺀 떨림 성분."""
import subprocess, sys, numpy as np
W, H = 320, 180
def frames(f, ss, to):
    raw = subprocess.run(["ffmpeg","-v","error","-ss",str(ss),"-to",str(to),"-i",f"assets/clips/{f}.mp4",
        "-vf",f"scale={W}:{H},format=gray","-f","rawvideo","-"],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,H,W).astype(np.float32)
win = np.outer(np.hanning(H), np.hanning(W))
def shift(a, b):
    A = np.fft.fft2((a-a.mean())*win); B = np.fft.fft2((b-b.mean())*win)
    R = A*np.conj(B); R /= np.abs(R)+1e-9
    r = np.fft.ifft2(R).real; y, x = np.unravel_index(r.argmax(), r.shape)
    if y > H//2: y -= H
    if x > W//2: x -= W
    return x, y, r.max()
def smooth(v, k=9):
    return np.convolve(np.pad(v,(k//2,k//2),mode="edge"), np.ones(k)/k, mode="valid")
for f, a, b in [(s.split(",")[0], float(s.split(",")[1]), float(s.split(",")[2])) for s in sys.argv[1:]]:
    fr = frames(f, a, b)
    d = np.array([shift(fr[i+1], fr[i])[:2] for i in range(len(fr)-1)], float)
    dup = np.mean(np.abs(fr[1:]-fr[:-1]).mean(axis=(1,2)) < 0.3)
    jit = d - np.stack([smooth(d[:,0]), smooth(d[:,1])], 1)
    j = np.sqrt((jit**2).sum(1))
    print(f"{f} {a}-{b}: 떨림 평균 {j.mean():.2f}px 최대 {j.max():.1f}px (320폭 기준) · 정지/중복 프레임 {dup*100:.0f}% · 이동 평균 {np.abs(d).mean(0).round(2)}")
