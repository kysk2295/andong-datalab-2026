"""index.html 생성기. 컷·자막·효과음 시점은 tools/plan.py(→ timeline.json)가 정본이다."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAN = json.loads((ROOT / "tools" / "timeline.json").read_text(encoding="utf-8"))
SHOTS = PLAN["shots"]
BY = {s["id"]: s for s in SHOTS}
EV = PLAN["events"]
TOTAL = PLAN["total"]

MAP_CREDIT = "지도 © OpenStreetMap contributors / OpenFreeMap · 행정경계 통계청 SGIS"
SITE_URL = "andong-atlas-production.up.railway.app"
CTA_ORIGIN = "130px 618px"  # 사이트 화면에서 누른 「1인칭 릴레이 체험」 위치


def fmt(x):
    return f"{round(x, 3):g}"


def video_html():
    out = []
    for i, s in enumerate(SHOTS):
        out.append(
            f'      <!-- {s["memo"]} -->\n'
            f'      <div id="{s["id"]}-w" class="shot" style="z-index: {i + 1}">\n'
            f'        <video id="{s["id"]}" class="clip" src="assets/cut/{s["id"]}.mp4" data-start="{fmt(s["start"])}" '
            f'data-duration="{fmt(s["dur"])}" data-media-start="0" data-track-index="{i % 2}" muted playsinline></video>\n'
            f'      </div>'
        )
    return "\n".join(out)


def caption_html():
    out = []
    for c in PLAN["labels"]:
        out.append(
            f'      <div id="{c["id"]}" class="clip cap cap-{c["pos"]}" data-start="{fmt(c["start"])}" '
            f'data-duration="{fmt(c["dur"])}" data-track-index="3">\n'
            f'        <div class="scrim"></div>\n'
            f'        <div class="cap-body">\n'
            f'          <p class="tag">{c["tag"]}</p>\n'
            f'          <p class="line">{c["text"]}</p>\n'
            f'        </div>\n'
            f'      </div>'
        )
    return "\n".join(out)


def timeline_js():
    js = []
    r = BY["alley"]["start"]
    js.append('gsap.set("#cta-w", { transformOrigin: "' + CTA_ORIGIN + '", scale: 1, filter: "blur(0px)" });')
    js.append('gsap.set("#ending-w", { transformOrigin: "50% 60%" });')
    for s in SHOTS:
        if s["x"] > 0 and s["id"] != "alley":
            js.append(f'gsap.set("#{s["id"]}-w", {{ opacity: 0 }});')
            js.append(f'tl.fromTo("#{s["id"]}-w", {{ opacity: 0 }}, {{ opacity: 1, duration: {fmt(s["x"])}, '
                      f'ease: "sine.inOut", immediateRender: false }}, {fmt(s["start"])});')
    # 사이트 화면 → 1인칭: 누른 버튼 쪽으로 파고들며 흐려지고, 골목이 흐림에서 초점을 찾는다
    js.append('gsap.set("#alley-w", { opacity: 0 });')
    js.append(f'tl.fromTo("#cta-w", {{ scale: 1, filter: "blur(0px)" }}, {{ scale: 1.45, filter: "blur(12px)", '
              f'duration: 0.8, ease: "power2.in", immediateRender: false }}, {fmt(r - 0.4)});')
    js.append(f'tl.fromTo("#alley-w", {{ opacity: 0, scale: 1.12, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, '
              f'filter: "blur(0px)", duration: 0.8, ease: "power2.out", immediateRender: false }}, {fmt(r)});')
    # 엔딩 전경은 아주 천천히 다가간다
    e0 = BY["ending"]["start"]
    js.append(f'tl.fromTo("#ending-w", {{ scale: 1 }}, {{ scale: 1.045, duration: {fmt(TOTAL - e0)}, ease: "none", '
              f'immediateRender: false }}, {fmt(e0)});')
    # 자막: 들어올 때 0.6초, 나갈 때 0.45초
    for c in PLAN["labels"]:
        cid, t, d = c["id"], c["start"], c["dur"]
        js.append(f'tl.fromTo("#{cid} .scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "sine.out" }}, {fmt(t)});')
        js.append(f'tl.fromTo("#{cid} .tag", {{ opacity: 0, y: 8 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }}, {fmt(t + 0.05)});')
        js.append(f'tl.fromTo("#{cid} .line", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }}, {fmt(t + 0.2)});')
        js.append(f'tl.to("#{cid} .cap-body, #{cid} .scrim", {{ opacity: 0, duration: 0.45, ease: "sine.in" }}, {fmt(t + d - 0.45)});')
    # 여는 제목
    o = EV["open_title"]
    js.append(f'tl.fromTo("#open .scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 1.0, ease: "sine.out" }}, {fmt(o)});')
    js.append(f'tl.fromTo("#open .kicker", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }}, {fmt(o + 0.3)});')
    js.append(f'tl.fromTo("#open .headline", {{ opacity: 0, y: 22 }}, {{ opacity: 1, y: 0, duration: 1.1, ease: "power3.out" }}, {fmt(o + 0.6)});')
    js.append(f'tl.fromTo("#open .rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.8, ease: "power3.out" }}, {fmt(o + 1.2)});')
    js.append(f'tl.fromTo("#open .notes", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.7, ease: "sine.out" }}, {fmt(o + 1.4)});')
    js.append(f'tl.to("#open .copy, #open .notes, #open .scrim", {{ opacity: 0, duration: 0.6, ease: "sine.in" }}, {fmt(BY["hahoe"]["start"] - 0.4)});')
    # 엔딩
    e = EV["ending_title"]
    js.append(f'tl.fromTo("#ending .scrim", {{ opacity: 0 }}, {{ opacity: 1, duration: 1.0, ease: "sine.out" }}, {fmt(e)});')
    js.append(f'tl.fromTo("#ending .kicker", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }}, {fmt(e + 0.1)});')
    js.append(f'tl.fromTo("#ending .title", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 1.0, ease: "power2.out" }}, {fmt(e + 0.3)});')
    js.append(f'tl.fromTo("#ending .rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.7, ease: "power3.out" }}, {fmt(e + 0.8)});')
    js.append(f'tl.fromTo("#ending .subtitle", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }}, {fmt(e + 0.9)});')
    js.append(f'tl.fromTo("#ending .url", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }}, {fmt(e + 1.6)});')
    js.append(f'tl.fromTo("#ending .credits", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8, ease: "sine.out" }}, {fmt(e + 2.0)});')
    # 처음·끝 검은 화면
    js.append('tl.fromTo("#fade", { opacity: 1 }, { opacity: 0, duration: 1.2, ease: "sine.out" }, 0);')
    js.append(f'tl.to("#fade", {{ opacity: 1, duration: 1.2, ease: "sine.in" }}, {fmt(TOTAL - 1.2)});')
    return "\n      ".join(js)


def audio_html():
    rows = [
        ("bgm", "assets/audio/bgm.wav", 0, TOTAL, 10, 1),
        ("amb", "assets/audio/ambience.wav", 0, TOTAL, 11, 0.8),
        ("foley", "assets/audio/foley.wav", 0, TOTAL, 12, 0.85),
        ("sfx-sunset", "assets/audio/sfx/click-soft.mp3", EV["sunset_click"] - 0.03, 0.37, 13, 0.45),
        ("sfx-night", "assets/audio/sfx/click-soft.mp3", EV["night_click"] - 0.03, 0.37, 14, 0.45),
        ("sfx-cta", "assets/audio/sfx/click-soft.mp3", EV["cta_click"] - 0.03, 0.37, 15, 0.5),
        ("sfx-whoosh", "assets/audio/sfx/whoosh-short.mp3", EV["to_relay"] - 0.35, 0.57, 16, 0.3),
    ]
    return "\n".join(
        f'      <audio id="{i}" src="{src}" data-start="{fmt(t)}" data-duration="{fmt(d)}" '
        f'data-track-index="{k}" data-volume="{v}"></audio>'
        for i, src, t, d, k, v in rows)


HTML = """<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>안동 3D Atlas · 사이트 소개</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Light.otf") format("opentype"); font-weight: 300; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Regular.otf") format("opentype"); font-weight: 400; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Medium.otf") format("opentype"); font-weight: 500; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-SemiBold.otf") format("opentype"); font-weight: 600; }
      @font-face { font-family: "Pretendard"; src: url("assets/fonts/Pretendard-Bold.otf") format("opentype"); font-weight: 700; }
      :root {
        --ink: #f7f4ec;
        --ink-soft: #e8e4da;
        --lamp: #e8bf78;
        --shade: 8, 16, 14;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #070b0a; }
      #root {
        position: relative; width: 100%; height: 100%; overflow: hidden;
        font-family: "Pretendard", sans-serif; color: var(--ink); word-break: keep-all;
      }
      .shot { position: absolute; inset: 0; will-change: transform, opacity; }
      .shot video { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
      p { margin: 0; }
      .sh { text-shadow: 0 2px 16px rgba(0, 0, 0, 0.5), 0 1px 3px rgba(0, 0, 0, 0.45); }

      /* 장소 자막: 작은 장소 이름 + 한 줄. 흰 글자와 경계 없는 어둠 번짐만 */
      .cap { position: absolute; inset: 0; z-index: 100; pointer-events: none; }
      .cap .scrim { position: absolute; }
      .cap-bottom .scrim { left: 0; right: 0; bottom: 0; height: 360px; background: linear-gradient(to top, rgba(var(--shade), 0.74), rgba(var(--shade), 0.34) 55%, rgba(var(--shade), 0)); }
      .cap-ui .scrim { left: 330px; width: 1000px; bottom: 90px; height: 330px; background: radial-gradient(ellipse at 30% 70%, rgba(var(--shade), 0.72), rgba(var(--shade), 0) 68%); }
      .cap-body { position: absolute; display: flex; flex-direction: column; gap: 14px; }
      .cap-bottom .cap-body { left: 132px; bottom: 100px; }
      .cap-ui .cap-body { left: 420px; bottom: 170px; }
      .line { font-size: 54px; font-weight: 600; letter-spacing: -0.015em; line-height: 1.25; text-shadow: 0 2px 16px rgba(0, 0, 0, 0.55), 0 1px 3px rgba(0, 0, 0, 0.5); }
      .tag { display: flex; align-items: center; gap: 12px; font-size: 26px; font-weight: 500; color: var(--ink-soft); letter-spacing: 0.02em; text-shadow: 0 1px 8px rgba(0, 0, 0, 0.6); }
      .tag::before { content: ""; display: block; width: 9px; height: 9px; border-radius: 50%; background: var(--lamp); }

      /* 여는 제목 */
      #open { position: absolute; inset: 0; z-index: 110; pointer-events: none; }
      #open .scrim { position: absolute; inset: 0; background: radial-gradient(ellipse 1500px 760px at 0% 18%, rgba(var(--shade), 0.72), rgba(var(--shade), 0.35) 50%, rgba(var(--shade), 0) 80%), radial-gradient(ellipse 1100px 360px at 100% 100%, rgba(var(--shade), 0.85), rgba(var(--shade), 0) 75%); }
      #open .copy { position: absolute; left: 132px; top: 150px; display: flex; flex-direction: column; gap: 22px; }
      #open .kicker { font-size: 28px; font-weight: 500; letter-spacing: 0.08em; color: var(--ink-soft); }
      #open .headline { font-size: 96px; font-weight: 700; letter-spacing: -0.025em; line-height: 1.12; }
      #open .rule, #ending .rule { display: block; width: 84px; height: 3px; background: var(--lamp); transform-origin: left center; }
      #open .notes { position: absolute; right: 120px; bottom: 80px; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; text-align: right; }
      #open .notes .demo { font-size: 24px; font-weight: 600; }
      #open .notes .credit { font-size: 19px; font-weight: 400; color: var(--ink-soft); }

      /* 엔딩: 하늘 쪽 왼쪽 위. 월영정과 수면 반사를 가리지 않는다 */
      #ending { position: absolute; inset: 0; z-index: 120; pointer-events: none; }
      #ending .scrim { position: absolute; left: 0; top: 0; width: 1250px; height: 560px; background: radial-gradient(ellipse at 0% 0%, rgba(var(--shade), 0.6), rgba(var(--shade), 0) 70%); }
      #ending .title-block { position: absolute; left: 132px; top: 96px; display: flex; flex-direction: column; gap: 20px; }
      #ending .kicker { font-size: 28px; font-weight: 500; letter-spacing: 0.08em; color: var(--ink-soft); }
      #ending .title { font-size: 112px; font-weight: 700; letter-spacing: -0.025em; line-height: 1.05; }
      #ending .subtitle { font-size: 46px; font-weight: 300; letter-spacing: -0.005em; }
      #ending .url { margin-top: 10px; font-size: 30px; font-weight: 500; letter-spacing: 0.01em; color: var(--lamp); }
      #ending .credits { position: absolute; right: 96px; bottom: 60px; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; text-align: right; }
      #ending .credits p { font-size: 19px; font-weight: 400; color: var(--ink-soft); text-shadow: 0 1px 6px rgba(0, 0, 0, 0.75); }
      #ending .credits .demo { font-size: 22px; font-weight: 600; color: var(--ink); }

      #fade { position: absolute; inset: 0; z-index: 200; background: #000; pointer-events: none; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__TOTAL__" data-width="1920" data-height="1080">
__VIDEOS__

      <div id="open" class="clip" data-start="__OPEN_START__" data-duration="__OPEN_DUR__" data-track-index="4">
        <div class="scrim"></div>
        <div class="copy">
          <p class="kicker sh">안동 3D Atlas</p>
          <p class="headline sh">강이 돌아 흐르는 도시,<br />안동</p>
          <span class="rule"></span>
        </div>
        <div class="notes sh">
          <p class="demo">안동 이어드림 제안 · 3D 지도 시연</p>
          <p class="credit">__MAP_CREDIT__</p>
        </div>
      </div>

__CAPTIONS__

      <div id="ending" class="clip" data-start="__END_START__" data-duration="__END_DUR__" data-track-index="6">
        <div class="scrim"></div>
        <div class="title-block">
          <p class="kicker sh">안동 3D Atlas</p>
          <p class="title sh">안동 이어드림</p>
          <span class="rule"></span>
          <p class="subtitle sh">지도에서 시작해, 안동의 밤까지</p>
          <p class="url sh">__SITE_URL__</p>
        </div>
        <div class="credits">
          <p class="demo">3D 시연 화면 · 공방·팝업·혜택 일부는 제안</p>
          <p>__MAP_CREDIT__</p>
          <p>음악 자체 제작 · 효과음 Pixabay</p>
        </div>
      </div>

      <div id="fade" class="clip" data-start="0" data-duration="__TOTAL__" data-track-index="7"></div>

__AUDIO__
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      __TIMELINE__
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

o = EV["open_title"]
html = (HTML.replace("__VIDEOS__", video_html())
        .replace("__CAPTIONS__", caption_html())
        .replace("__TIMELINE__", timeline_js())
        .replace("__AUDIO__", audio_html())
        .replace("__TOTAL__", fmt(TOTAL))
        .replace("__OPEN_START__", fmt(o))
        .replace("__OPEN_DUR__", fmt(BY["hahoe"]["start"] + 0.3 - o))
        .replace("__END_START__", fmt(EV["ending_title"]))
        .replace("__END_DUR__", fmt(TOTAL - EV["ending_title"]))
        .replace("__MAP_CREDIT__", MAP_CREDIT)
        .replace("__SITE_URL__", SITE_URL))
(ROOT / "index.html").write_text(html, encoding="utf-8")
print("index.html written:", len(SHOTS), "shots,", len(PLAN["labels"]), "labels, total", TOTAL)
