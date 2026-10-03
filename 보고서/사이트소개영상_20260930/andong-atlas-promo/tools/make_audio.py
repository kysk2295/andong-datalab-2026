"""사이트 소개 영상의 음악·환경음·앱 효과음 스템(시점은 tools/timeline.json).

- bgm.wav      : 직접 합성한 원곡. D장조 5음계, 가야금 느낌의 뜯는 현(카플러스-스트롱 + 농현 떨림),
                 현악 패드, 피아노, 북 느낌의 낮은 타악. 외부 음원 없음.
                 밤 장면(events.night)이 18마디째 첫 박에 오도록 마디 길이를 맞춘다(약 82BPM).
  0~4마디    항공·하회: 패드와 뜯는 현만
  4~7        원도심: 피아노 화음이 들어옴
  7.6~13.8   사이트 화면·월영교: 낮은 북과 베이스로 걸음
  13.8~18    1인칭 체험: 선율이 커짐
  18~22      밤의 월영교·팝업: 가장 넓게(현악 위로)
  22~        엔딩: 마지막 화음과 여운
- ambience.wav : 합성 바람(도입), 물소리(월영교 장면)
- foley.wav    : 1인칭 촬영 클립의 앱 합성음(발소리·식기·밤마당)을 컷 시점에 맞춰 작게

실행(저장소 루트의 가상환경): ../../../.venv_pdf/bin/python tools/make_audio.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "tools" / "timeline.json").read_text(encoding="utf-8"))
EV = PLAN["events"]
SHOT = {s["id"]: s for s in PLAN["shots"]}
DUR = float(PLAN["total"])
N = int(SR * DUR)
OUT = ROOT / "assets" / "audio"
rng = np.random.default_rng(20260930)

BAR = EV["night"] / 18
BEAT = BAR / 4
B_PIANO, B_WALK, B_RELAY, B_NIGHT = 4, int(round(SHOT["ui"]["start"] / BAR)), int(round(EV["to_relay"] / BAR)), 18
B_FINAL = 22


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, hz, order=2):
    return sosfilt(butter(order, hz, "low", fs=SR, output="sos"), x)


def hp(x, hz, order=2):
    return sosfilt(butter(order, hz, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def place(buf, sig, start, pan=0.0):
    i = int(start * SR)
    if i >= buf.shape[1] or i + len(sig) <= 0:
        return
    sig = sig[: buf.shape[1] - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(sig)] += sig * l
    buf[1, i:i + len(sig)] += sig * r


def reverb(x, secs=3.4, mix=0.3):
    n = int(secs * SR)
    ir = rng.standard_normal((2, n)) * np.exp(-np.arange(n) / SR / (secs / 5.5))
    ir = np.stack([lp(ir[0], 6500), lp(ir[1], 6000)])
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
    wet = np.stack([fftconvolve(x[0], ir[0])[: x.shape[1]], fftconvolve(x[1], ir[1])[: x.shape[1]]])
    return x * (1 - mix) + wet * mix * 1.6


def pluck(m, vel=0.5, dur=2.6, bend=True):
    """가야금 느낌: 카플러스-스트롱 현 + 뜯은 뒤 살짝 눌러 올리는 떨림."""
    f = mtof(m)
    n = int(dur * SR)
    period = SR / f
    L = int(period)
    buf = rng.uniform(-1, 1, L) * vel
    buf = lp(np.concatenate([buf, buf]), 4500)[L:]
    out = np.zeros(n)
    idx = 0
    for k in range(n):
        out[k] = buf[idx]
        nxt = (idx + 1) % L
        buf[idx] = 0.996 * 0.5 * (buf[idx] + buf[nxt])
        idx = nxt
    if bend:  # 농현: 0.35초 뒤 느린 떨림을 위상 변조로 흉내
        t = np.arange(n) / SR
        depth = np.clip((t - 0.35) / 0.4, 0, 1) * 0.0022
        warp = np.cumsum(1 + depth * np.sin(2 * np.pi * 5.2 * t))
        out = np.interp(np.clip(warp, 0, n - 1), np.arange(n), out)
    out *= np.minimum(1, np.arange(n) / (0.002 * SR))
    return lp(out, 5200) * 0.9


def piano(m, dur, vel=0.4):
    n = int((dur + 1.8) * SR)
    t = np.arange(n) / SR
    f = mtof(m)
    x = sum(a * np.sin(2 * np.pi * f * h * t) * np.exp(-t * (0.9 + h * 0.8)) for h, a in [(1, 1), (2, 0.42), (3, 0.18), (4, 0.08)])
    x *= np.minimum(1, t / 0.004) * np.where(t < dur, 1, np.exp(-(t - dur) * 4))
    return x * vel * 0.3


def pad(ms, dur, level=0.1, bright=1800):
    n = int((dur + 2.5) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in ms:
        for det in (-0.07, 0.0, 0.08):
            f = mtof(m + det)
            x += 2 * ((t * f + rng.random()) % 1) - 1
    x = lp(x / (len(ms) * 3), bright, 2)
    att = np.minimum(1, t / 1.6)
    rel = np.where(t < dur, 1, np.exp(-(t - dur) * 1.4))
    return x * att * rel * level


def buk(vel=0.6):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 62 + 70 * np.exp(-t / 0.05)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    skin = lp(rng.standard_normal(n), 900) * np.exp(-t / 0.05) * 0.5
    return (x + skin) * vel


def tick(vel=0.12):
    n = int(0.08 * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 5000) * np.exp(-t / 0.018) * vel


def bass(m, dur, vel=0.35):
    n = int((dur + 0.4) * SR)
    t = np.arange(n) / SR
    f = mtof(m)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    x *= np.minimum(1, t / 0.01) * np.where(t < dur, np.exp(-t * 0.6), np.exp(-dur * 0.6) * np.exp(-(t - dur) * 12))
    return x * vel


CHORDS = {  # D · Bm · G · A(sus)
    "D": (38, [62, 66, 69, 74]),
    "Bm": (35, [59, 62, 66, 71]),
    "G": (43, [59, 62, 67, 71]),
    "A": (45, [61, 64, 69, 76]),
}
PROG = ["D", "Bm", "G", "A"]
PENTA = [62, 64, 66, 69, 71, 74, 76, 78, 81]  # D E F# A B (5음계)

# 뜯는 현 선율(마디 안 박 위치, 5음계 번호). 두 마디 한 묶음
MOTIF_A = [(0, 5), (1.5, 4), (2, 3), (3, 2), (4, 3), (5.5, 1), (6, 0)]
MOTIF_B = [(0, 3), (1, 4), (1.5, 5), (2, 6), (3.5, 5), (4, 4), (5, 3), (6.5, 2)]
MOTIF_HI = [(0, 7), (1, 6), (1.5, 5), (2, 6), (3, 8), (4, 7), (5, 5), (5.5, 6), (6, 4)]


def build_bgm():
    dry = np.zeros((2, N + SR * 4))
    # 패드: 처음부터 끝까지 화음을 받친다. 밤에는 한 옥타브 위 층을 더한다
    for b in range(0, B_FINAL):
        ch = CHORDS[PROG[b % 4]]
        lvl = 0.07 if b < B_WALK else 0.09 if b < B_NIGHT else 0.12
        place(dry, pad(ch[1], BAR, lvl, 1500 if b < B_NIGHT else 2600), b * BAR, 0)
        if b >= B_NIGHT:
            place(dry, pad([m + 12 for m in ch[1][1:]], BAR, 0.045, 3200), b * BAR, 0)
    # 뜯는 현 선율
    for b in range(0, B_FINAL, 2):
        motif = MOTIF_HI if b >= B_NIGHT else MOTIF_B if b >= B_RELAY else MOTIF_A
        vel = 0.34 if b < B_PIANO else 0.4 if b < B_NIGHT else 0.46
        for beat, deg in motif:
            if b < 2 and beat > 5:
                continue
            place(dry, pluck(PENTA[deg], vel), b * BAR + beat * BEAT, -0.25 + 0.1 * (deg % 3))
    # 피아노: 4마디부터 화음을 반박자 어긋나게
    for b in range(B_PIANO, B_FINAL):
        root, ch = CHORDS[PROG[b % 4]]
        for k, m in enumerate(ch[:3]):
            place(dry, piano(m - 12, BEAT * 3, 0.32), b * BAR + k * 0.04, 0.25)
        if b >= B_RELAY:
            place(dry, piano(ch[3], BEAT, 0.22), b * BAR + BEAT * 2.5, 0.3)
    # 걸음: 북·베이스·가벼운 틱
    for b in range(B_WALK, B_FINAL):
        root, _ = CHORDS[PROG[b % 4]]
        place(dry, bass(root, BEAT * 3.5, 0.3 if b < B_NIGHT else 0.36), b * BAR, 0)
        place(dry, buk(0.5 if b < B_RELAY else 0.62), b * BAR, 0)
        place(dry, buk(0.28), b * BAR + BEAT * 2.5, 0)
        if b >= B_RELAY:
            place(dry, buk(0.34), b * BAR + BEAT * 3, 0)
        for k in range(8):
            if b >= B_RELAY or k % 2 == 1:
                place(dry, tick(0.09 if k % 2 else 0.05), b * BAR + k * BEAT / 2, 0.4 if k % 2 else -0.4)
    # 밤 첫 박: 큰 북과 낮은 울림
    place(dry, buk(1.0), B_NIGHT * BAR, 0)
    place(dry, pad([38, 50, 57], BAR * 2, 0.12, 900), B_NIGHT * BAR, 0)
    # 마지막 화음: 피아노·현·패드가 함께 울리고 여운
    t = B_FINAL * BAR
    place(dry, buk(0.8), t, 0)
    place(dry, bass(38, 6, 0.4), t, 0)
    for m in [50, 57, 62, 66, 69, 74]:
        place(dry, piano(m, 6, 0.3), t, 0.1)
    place(dry, pad([62, 66, 69, 74, 78], DUR - t - 2, 0.11, 2200), t, 0)
    for k, deg in enumerate([5, 4, 3, 5, 7]):
        place(dry, pluck(PENTA[deg], 0.3), t + 2.2 + k * BEAT * 1.5, 0.2)
    x = reverb(dry[:, :N], 3.6, 0.34)
    x = level(x)
    fade = np.ones(N)
    fade[: int(1.2 * SR)] = np.linspace(0, 1, int(1.2 * SR))
    fade[-int(2.4 * SR):] = np.linspace(1, 0, int(2.4 * SR)) ** 1.5
    return x * fade


def level(x, win=2.0, strength=0.65):
    """구간 음량 고르기: 1~2초 창의 RMS를 전체 중앙값 쪽으로 당긴다(조용한 도입·엔딩이 묻히지 않게)."""
    mono = (x[0] ** 2 + x[1] ** 2) / 2
    k = int(win * SR)

    def smooth(v):
        c = np.concatenate([[0], np.cumsum(v)])
        i = np.arange(len(v))
        lo, hi = np.clip(i - k // 2, 0, len(v)), np.clip(i + k // 2, 0, len(v))
        return (c[hi] - c[lo]) / np.maximum(hi - lo, 1)

    env = np.sqrt(smooth(mono) + 1e-10)
    ref = np.median(env[env > 1e-4])
    gain = np.clip((ref / env) ** strength, 0.6, 4.0)
    gain = smooth(gain)
    return x * gain


def noise_bed(lo, hi, level, start, end, fin=2.0, fout=2.0):
    n = int((end - start) * SR)
    x = np.stack([bp(rng.standard_normal(n), lo, hi), bp(rng.standard_normal(n), lo, hi)])
    t = np.arange(n) / SR
    slow = 0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t + 1.2)
    env = np.minimum(1, t / fin) * np.minimum(1, (t[-1] - t) / fout) * slow
    out = np.zeros((2, N))
    i = int(start * SR)
    out[:, i:i + n] = x[:, : N - i] * env[: N - i] * level
    return out


def build_ambience():
    x = noise_bed(180, 1400, 0.05, 0, SHOT["city"]["end"], 2.5, 3)  # 바람
    x += noise_bed(500, 3800, 0.03, SHOT["bridge"]["start"], SHOT["bridge"]["end"], 1.2, 1.2)  # 물
    x += noise_bed(500, 3800, 0.035, SHOT["walk"]["start"], DUR, 1.5, 3)
    return x


def load_clip(path, ss, dur):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(ss), "-t", str(dur), "-i", str(path),
                          "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).T.copy()


def build_foley():
    out = np.zeros((2, N))
    for sid, gain in [("alley", 0.9), ("meal", 0.7), ("mask", 0.4), ("walk", 0.7), ("popup", 0.8)]:
        s = SHOT[sid]
        try:  # 소리 없는 클립(프레임별 기록본)은 건너뛴다
            x = load_clip((ROOT / s["src"]).resolve(), s["ss"], s["dur"])
        except subprocess.CalledProcessError:
            print("  소리 없음:", sid)
            continue
        n = x.shape[1]
        env = np.minimum(1, np.arange(n) / (0.25 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.3 * SR))
        i = int(s["start"] * SR)
        out[:, i:i + n] += (x * env * gain)[:, : N - i]
    return out


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def write(name, x, target_db):
    x = x * 10 ** ((target_db - rms_db(x[:, np.abs(x).max(axis=0) > 1e-4])) / 20)
    peak = np.abs(x).max()
    if peak > 0.89:
        x *= 0.89 / peak
    pcm = (x.T * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    str(OUT / name)], input=pcm, check=True)
    print(name, f"{x.shape[1] / SR:.2f}s", f"peak {20 * np.log10(np.abs(x).max()):.1f}dBFS")


if __name__ == "__main__":
    print(f"BAR {BAR:.3f}s ({240 / BAR:.1f}BPM) walk={B_WALK} relay={B_RELAY} night={B_NIGHT} final={B_FINAL * BAR:.2f}s")
    write("bgm.wav", build_bgm(), -19)
    write("ambience.wav", build_ambience(), -36)
    write("foley.wav", build_foley(), -30)
