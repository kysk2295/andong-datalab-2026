"""안동 이어드림 영상용 음악·환경음·앱 효과음 스템 생성(길이·장면 시점은 tools/timeline.json).

- bgm.wav      : 이 스크립트가 직접 합성한 원곡(피아노·현악 패드, D장조 5음계). 외부 음원 없음.
- ambience.wav : 합성 환경음(도입 바람, 월영교부터 물소리).
- foley.wav    : 촬영 클립의 앱 합성 효과음(S03 골목 발소리, S11a 밤마당)을 편집 속도·시점에 맞춰 키운 것.

실행: .venv_pdf/bin/python tools/make_audio.py  (프로젝트 폴더에서, ffmpeg 필요)
같은 입력이면 같은 파일이 나온다(난수 시드 고정).
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
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20260930)

B_NIGHT = 12
BAR = EV["night"] / B_NIGHT  # 12마디째가 월영교 첫 전경에 오도록 맞춘 마디 길이(약 75~80BPM)
BEAT = BAR / 4
B_MEAL = round(EV["meal"] / BAR)      # 아르페지오 시작(식사)
B_RIDE = round(EV["ride"] / BAR)      # 이동: 한 박자씩으로 줄이며 준비
B_RIVER = round(EV["river"] / BAR)    # 수면 반사부터 박 없이 여운
B_FINAL = int((DUR - 3.2) // BAR)     # 마지막 D 화음


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, hz, order=2):
    return sosfilt(butter(order, hz, "low", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- 악기
def piano(m, dur, vel=0.5):
    f = mtof(m)
    L = dur + 2.5
    t = np.arange(int(L * SR)) / SR
    out = np.zeros_like(t)
    npart = 9 if vel > 0.45 else 6
    for n in range(1, npart + 1):
        fn = n * f * np.sqrt(1 + 0.00035 * n * n)
        if fn > 12000:
            break
        amp = (1 / n ** 1.35) * (vel ** (0.4 * n))
        dec = np.exp(-t * (0.9 + 0.55 * n) * (220 / max(f, 110)) ** 0.25)
        out += amp * dec * np.sin(2 * np.pi * fn * t + n)
    att = np.clip(t / 0.004, 0, 1)
    rel = np.clip(1 - (t - dur) / 0.9, 0, 1)
    return out * att * rel * vel


def pad(ms, dur, level=0.12, bright=5):
    L = dur + 2.0
    t = np.arange(int(L * SR)) / SR
    out = np.zeros_like(t)
    for m in ms:
        f = mtof(m)
        for det in (-0.07, 0.0, 0.07):  # 약 ±7센트
            fd = f * 2 ** (det / 12)
            ph = rng.uniform(0, 2 * np.pi)
            for n in range(1, bright + 1):
                if n * fd > 6000:
                    break
                out += (1 / n ** 1.6) * np.sin(2 * np.pi * n * fd * t + ph * n)
    env = np.clip(t / 1.4, 0, 1) * np.clip(1 - (t - dur) / 1.6, 0, 1)
    lfo = 1 + 0.08 * np.sin(2 * np.pi * 0.21 * t)
    return out * env * lfo * level / (len(ms) * 3)


def place(buf, sig, start, pan=0.0):
    i = int(start * SR)
    if i >= buf.shape[1]:
        return
    j = min(buf.shape[1], i + len(sig))
    s = sig[: j - i]
    buf[0, i:j] += s * np.sqrt(0.5 * (1 - pan))
    buf[1, i:j] += s * np.sqrt(0.5 * (1 + pan))


def reverb(x, secs=3.2, mix=0.32):
    L = int(secs * SR)
    t = np.arange(L) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(L) * np.exp(-t / 0.75)
        ir = lp(ir, 5200)
        ir[: int(0.012 * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = fftconvolve(x[ch], ir)[: x.shape[1]]
    return x * (1 - mix) + out * mix * 1.6


# ---------------------------------------------------------------- 곡
CHORDS = {  # D · Bm · G · A (5음계 색을 살린 보이싱)
    "D": [50, 57, 62, 64, 66],
    "Bm": [47, 54, 59, 62, 66],
    "G": [43, 50, 55, 59, 62, 66],
    "Asus": [45, 52, 57, 62, 64],
    "A": [45, 52, 57, 61, 64],
}
PROG = ["D", "Bm", "G", "Asus"]


def chord_at(bar):
    if bar >= B_FINAL:
        return "D"
    if bar in (B_NIGHT - 1, B_FINAL - 1):  # 월영교 직전·마지막 전 마디는 A로 해결감
        return "A"
    return PROG[bar % 4]


# 넓어지는 선율(월영교부터, 마디 오프셋, 박, 음, 길이)
WIDE = [
    (0, 0, 69, 2), (0, 2, 66, 1), (0, 3, 64, 1),
    (1, 0, 71, 3), (1, 3, 69, 1),
    (2, 0, 74, 2), (2, 2, 71, 1), (2, 3, 69, 1),
    (3, 0, 69, 2), (3, 2, 64, 2),
    (4, 0, 66, 1), (4, 1, 69, 1), (4, 2, 74, 2),
    (5, 0, 76, 2), (5, 2, 74, 1), (5, 3, 71, 1),
    (6, 0, 69, 3), (6, 3, 71, 1),
]
# 여운 선율(마지막 화음 기준 마디 오프셋)
CALM = [
    (-4, 0, 74, 4),
    (-3, 0, 71, 2), (-3, 2, 69, 2),
    (-2, 0, 71, 4),
    (-1, 0, 69, 2), (-1, 2, 73, 2),
    (0, 0, 74, 8),
]


def build_bgm():
    mus = np.zeros((2, N + SR * 6))
    nbars = B_FINAL + 1

    for b in range(nbars):
        st = b * BAR
        ms = CHORDS[chord_at(b)]
        # 패드: 도입은 옅게, 월영교부터 넓게(한 옥타브 위 층 추가)
        if b < B_MEAL:
            lvl = 0.05 + 0.03 * b / max(B_MEAL, 1)
        elif b < B_RIDE:
            lvl = 0.085
        elif b < B_NIGHT:
            lvl = 0.085 + 0.065 * (b - B_RIDE + 1) / max(B_NIGHT - B_RIDE, 1)
        elif b < B_RIVER:
            lvl = 0.15
        else:
            lvl = 0.13
        dur = BAR if b < B_FINAL else DUR - st + 1.5
        place(mus, pad(ms, dur, lvl, bright=4 if b < B_NIGHT else 6), st, pan=-0.15)
        if b >= B_NIGHT:
            place(mus, pad([m + 12 for m in ms[2:]], dur, lvl * 0.55, bright=3), st, pan=0.35)

        # 피아노 저음: 식사부터 첫 박
        low = ms[0] - 12 if ms[0] > 45 else ms[0]
        if B_MEAL <= b < B_RIVER:
            place(mus, piano(low, BAR * 0.9, 0.34), st, pan=-0.2)
        elif b >= B_RIVER:
            place(mus, piano(low, BAR * 1.8, 0.26), st, pan=-0.2)

        # 아르페지오: 식사~이동 전 8분음, 이동~수면 반사 전 4분음, 이후 없음
        arp = [ms[0] + 12, ms[1] + 12, ms[2] + 12, ms[3] + 12, ms[4] + 12, ms[3] + 12, ms[2] + 12, ms[1] + 12]
        if B_MEAL <= b < B_RIDE:
            for k in range(8):
                v = 0.24 + (0.05 if k % 4 == 0 else 0) + rng.uniform(-0.02, 0.02)
                place(mus, piano(arp[k], BEAT * 0.9, v), st + k * BEAT / 2, pan=0.25)
        elif B_RIDE <= b < B_RIVER:
            for k in range(4):
                v = 0.2 + rng.uniform(-0.02, 0.02)
                place(mus, piano(arp[k * 2], BEAT * 1.4, v), st + k * BEAT, pan=0.25)

    # 도입의 높은 음(한 마디 한 음)
    for b, m in zip(range(1, B_MEAL), [78, 76, 74, 69]):
        place(mus, piano(m, BAR * 0.8, 0.22), b * BAR + 0.1, pan=0.4)

    mel = [(B_NIGHT + r, bt, m, d, True) for r, bt, m, d in WIDE if B_NIGHT + r < B_FINAL - 4]
    mel += [(B_FINAL + r, bt, m, d, False) for r, bt, m, d in CALM]
    for b, beat, m, d, wide in mel:
        st = b * BAR + beat * BEAT
        d_sec = min(d * BEAT, DUR - st + 1.0)
        place(mus, piano(m, d_sec * 0.95, 0.42 if wide else 0.34), st, pan=0.1)
        if not wide:  # 여운은 현 한 겹을 얹어 길게
            place(mus, pad([m], d_sec, 0.07, bright=4), st, pan=0.1)

    mus = mus[:, :N]
    mus = reverb(mus)
    # 전체 윤곽: 앞 2초 페이드인, 끝 2초 페이드아웃
    t = np.arange(N) / SR
    env = np.clip(t / 2.0, 0, 1) * np.clip((DUR - t) / 2.0, 0, 1)
    mus *= env
    return mus


def build_ambience():
    t = np.arange(N) / SR
    amb = np.zeros((2, N))
    for ch in range(2):
        w = lp(rng.standard_normal(N), 500)
        a0 = EV["map_to_alley"]
        wind_env = np.clip(t / 1.5, 0, 1) * np.clip((a0 + 1.5 - t) / 2.5, 0, 1)
        wind_env *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * t + ch)
        amb[ch] += w * wind_env * 0.9

        water = bp(rng.standard_normal(N), 350, 2600, order=2)
        mod = 0.6 + 0.25 * np.sin(2 * np.pi * 0.31 * t + ch * 1.7) + 0.15 * np.sin(2 * np.pi * 1.37 * t + ch)
        lap = lp(np.abs(bp(rng.standard_normal(N), 2, 9)), 12) * 6  # 느린 물결 찰랑임
        n0, m0, r0 = EV["night"], EV["market"], EV["river"]
        water_env = np.clip((t - (n0 - 1.5)) / 3.0, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1)
        water_env *= np.where((t > m0) & (t < r0), 0.55, 1.0)  # 밤마당에서는 잠시 뒤로
        water_env *= np.where(t >= r0, 1.25, 1.0)  # 수면 반사 구간에서 조금 앞으로
        amb[ch] += water * (mod + np.clip(lap, 0, 1)) * water_env * 0.55
    return amb


def load_clip(path, ss, to, speed=1.0):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(ss), "-to", str(to), "-i", str(path), "-vn",
         "-af", f"atempo={speed}", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)


def build_foley():
    fol = np.zeros((2, N))
    clips = ROOT / "assets" / "clips"
    sp = PLAN["speed"]
    # (컷, 증폭 dB): 편집 컷과 같은 원본 구간·속도·시점
    for sid, gain in [("alley", 18), ("market", 16)]:
        s = SHOT[sid]
        f, a, b = s["parts"][0]
        x = load_clip(clips / f"{f}.mp4", a, b, sp) * 10 ** (gain / 20)
        start = s["start"]
        x = x[:, : max(0, min(x.shape[1], N - int(start * SR)))]
        L = x.shape[1]
        ramp = np.ones(L)
        k = int(0.25 * SR)
        ramp[:k] = np.linspace(0, 1, k)
        ramp[-k:] = np.linspace(1, 0, k)
        i = int(start * SR)
        fol[:, i:i + L] += x * ramp
    return fol


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def write(name, x, target_db):
    active = x[:, np.abs(x).max(axis=0) > 1e-4]
    g = 10 ** ((target_db - rms_db(active)) / 20)
    y = x * g
    peak = np.abs(y).max()
    if peak > 0.89:
        y *= 0.89 / peak
    pcm = (np.clip(y, -1, 1).T * 32767).astype("<i2")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
         str(OUT / name)], input=pcm.tobytes(), check=True)
    print(f"{name}: rms {rms_db(y):.1f} dBFS, peak {20*np.log10(np.abs(y).max()):.1f} dBFS")


if __name__ == "__main__":
    write("bgm.wav", build_bgm(), -21)
    write("ambience.wav", build_ambience(), -30)
    write("foley.wav", build_foley(), -30)
