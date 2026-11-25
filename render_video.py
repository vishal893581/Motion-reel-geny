import json
import math
import os
import random
import subprocess
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

with open("timeline.json") as f:
    data = json.load(f)

total_dur = data["total_duration"]
beats = data["beats"]
THUMB_HERO = data.get("thumb_hero", "SMART PLAN")
THUMB_SUB = data.get("thumb_sub", "3-Step Formula")
THUMB_BADGE = data.get("thumb_badge", "3 STEPS")

W, H = 1080, 1920
FPS = 30

os.makedirs("fonts", exist_ok=True)
FONT_URLS = {
    "fonts/Poppins-Black.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Black.ttf",
    "fonts/Poppins-ExtraBold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf",
    "fonts/Poppins-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
}
for dest, url in FONT_URLS.items():
    if not os.path.exists(dest):
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            print("Font fallback:", e)


def load_font(path, size):
    for p in [path, "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"]:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, int(size))
            except:
                pass
    return ImageFont.load_default()


f_xs = load_font("fonts/Poppins-Bold.ttf", 24)
f_sm = load_font("fonts/Poppins-Bold.ttf", 32)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", 44)
f_sub = load_font("fonts/Poppins-Bold.ttf", 46)
f_hero_lg = load_font("fonts/Poppins-Black.ttf", 148)
f_hero_md = load_font("fonts/Poppins-Black.ttf", 112)
f_hero_sm = load_font("fonts/Poppins-Black.ttf", 88)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158
    return 1 + (c1 + 1) * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - pow(1 - t, 3)


# Exact Palette from Uploaded Reference Videos (Warm Cream Paper + Deep Crimson Maroon + Burnt Orange)
C_CREAM = (239, 230, 213)
C_MAROON_BG = (92, 16, 16)
C_MAROON = (112, 20, 20)
C_MAROON_DARK = (54, 8, 8)
C_ORANGE = (218, 92, 38)
C_ORANGE_DARK = (118, 42, 12)
C_GOLD = (238, 178, 46)
C_WHITE = (252, 249, 242)
C_INK = (45, 22, 18)


def make_textured_bg(base_rgb):
    img = Image.new("RGBA", (W, H), base_rgb + (255,))
    dr = ImageDraw.Draw(img)
    rng = random.Random(42)
    for _ in range(18000):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        d = rng.randint(-9, 9)
        c = tuple(clamp(base_rgb[k] + d, 0, 255) for k in range(3)) + (255,)
        dr.point((x, y), fill=c)
    # Soft vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for step in range(36):
        inset = step * 10
        a = int(55 * pow(1.0 - step / 36.0, 2.0))
        if a > 0:
            vd.rectangle([inset, inset, W - inset, H - inset], outline=(25, 10, 8, a), width=11)
    img.alpha_composite(vig)
    return img


BG_CREAM = make_textured_bg(C_CREAM)
BG_MAROON = make_textured_bg(C_MAROON_BG)


def choose_hero_font(text):
    n = len(text)
    if n <= 6:
        return f_hero_lg
    elif n <= 10:
        return f_hero_md
    return f_hero_sm


def draw_3d_hero_text(draw, cx, cy, text, color_key="maroon", strike_prog=0.0):
    """Exact 3D extruded bold typography from reference video_2.mp4."""
    font = choose_hero_font(text)
    bb = draw.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = int(cx - tw // 2)
    y = int(cy - th // 2)

    if color_key == "orange":
        front, side = C_ORANGE, C_ORANGE_DARK
    elif color_key == "cream":
        front, side = C_CREAM, C_MAROON_DARK
    else:
        front, side = C_MAROON, C_MAROON_DARK

    # 3D Extrusion layers
    for depth in range(12, 0, -1):
        draw.text((x + depth, y + depth), text, font=font, fill=side + (255,))
    draw.text((x, y), text, font=font, fill=front + (255,))

    # Animated orange strikethrough bar (like "TENSION" in video_2.mp4)
    if strike_prog > 0.02:
        sx1 = x - 18
        sx2 = x - 18 + int((tw + 36) * clamp(strike_prog))
        sy = y + int(th * 0.56)
        draw.rounded_rectangle([sx1, sy - 9, sx2, sy + 9], radius=8, fill=C_ORANGE + (255,))
    return x, y, tw, th


def draw_pill_subtitle(draw, cx, cy, sub_text, pill_word, is_dark_bg=False):
    """Clean Hinglish subtitle with rounded Maroon Pill Badge around keyword (exact video_2 style)."""
    words = sub_text.split()
    if not words:
        return
    pill_clean = pill_word.strip().lower()

    # Split into max 2 lines
    lines = []
    cur = []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textbbox((0, 0), test, font=f_sub)[2] <= 760:
            cur.append(w)
        else:
            if cur:
                lines.append(cur)
            cur = [w]
    if cur:
        lines.append(cur)
    lines = lines[:2]

    txt_col = C_CREAM if is_dark_bg else C_MAROON
    pill_bg = C_ORANGE if is_dark_bg else C_MAROON
    pill_fg = C_WHITE

    for l_idx, l_words in enumerate(lines):
        items = []
        tot_w = 0
        for w in l_words:
            bb = draw.textbbox((0, 0), w, font=f_sub)
            ww = bb[2] - bb[0]
            is_p = bool(pill_clean) and (pill_clean in w.lower() or w.lower() in pill_clean)
            pad = 28 if is_p else 0
            items.append((w, ww, is_p, pad))
            tot_w += ww + pad + 16
        tot_w -= 16

        x = int(cx - tot_w // 2)
        y = int(cy + l_idx * 74)
        for w, ww, is_p, pad in items:
            if is_p:
                draw.rounded_rectangle([x, y - 6, x + ww + pad, y + 60], radius=28, fill=pill_bg + (255,))
                draw.text((x + pad // 2, y), w, font=f_sub, fill=pill_fg + (255,))
            else:
                draw.text((x, y), w, font=f_sub, fill=txt_col + (255,))
            x += ww + pad + 16


def draw_vector_card(canvas, cx, cy, b, pop_t):
    """100% locally rendered crisp vector cards & diagrams (zero external APIs, zero blank boxes)."""
    ctype = b.get("card", "none")
    if ctype == "none":
        return

    scale = 0.72 + 0.28 * ease_out_back(pop_t)
    cw, ch = int(390 * scale), int(460 * scale)
    card = Image.new("RGBA", (cw + 30, ch + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)

    # Soft drop shadow + crisp white/cream card body
    d.rounded_rectangle([18, 22, cw + 18, ch + 22], radius=28, fill=(35, 15, 10, 48))
    d.rounded_rectangle([10, 10, cw + 10, ch + 10], radius=28, fill=C_WHITE + (255,), outline=(218, 206, 188, 255), width=4)

    title = b.get("card_title", "STEP")
    val = b.get("card_val", "100%")
    sub = b.get("card_sub", "")

    # Header pill/banner
    hdr_col = C_GOLD if ctype in ("timer", "badge", "clock") else C_MAROON
    hdr_txt = C_INK if hdr_col == C_GOLD else C_WHITE
    d.rounded_rectangle([32, 28, cw - 12, 82], radius=16, fill=hdr_col + (255,))
    tbb = d.textbbox((0, 0), title, font=f_xs)
    d.text((10 + (cw - (tbb[2] - tbb[0])) // 2, 41), title, font=f_xs, fill=hdr_txt + (255,))

    if ctype == "checklist" or ctype == "sheet":
        rows = [r.strip() for r in val.split("|") if r.strip()][:3]
        for idx, r in enumerate(rows):
            ry = 115 + idx * 82
            d.rounded_rectangle([34, ry, 74, ry + 40], radius=10, outline=C_MAROON + (255,), width=4)
            if pop_t > 0.35 + idx * 0.15:
                d.line([(42, ry + 20), (52, ry + 31), (68, ry + 10)], fill=C_ORANGE + (255,), width=5)
            d.text((88, ry + 4), r[:16], font=f_sm, fill=C_INK + (255,))
        # Progress bar at bottom
        d.rounded_rectangle([34, ch - 78, cw - 14, ch - 56], radius=10, fill=(228, 220, 206, 255))
        pw = int((cw - 48) * clamp(pop_t))
        if pw > 12:
            d.rounded_rectangle([34, ch - 78, 34 + pw, ch - 56], radius=10, fill=C_GOLD + (255,))

    elif ctype == "compare":
        parts = val.split("vs") if "vs" in val else [val, "SMART"]
        p1, p2 = parts[0].strip()[:10], parts[1].strip()[:10]
        d.rounded_rectangle([32, 115, cw // 2 - 4, ch - 75], radius=18, fill=(244, 238, 228, 255), outline=(210, 198, 180, 255), width=3)
        d.rounded_rectangle([cw // 2 + 16, 115, cw - 12, ch - 75], radius=18, fill=(255, 246, 224, 255), outline=C_GOLD + (255,), width=4)
        d.text((46, 145), p1, font=f_xs, fill=C_INK + (255,))
        d.text((cw // 2 + 30, 145), p2, font=f_xs, fill=C_MAROON + (255,))
        d.rounded_rectangle([cw // 2 - 22, 220, cw // 2 + 42, 272], radius=24, fill=C_ORANGE + (255,))
        d.text((cw // 2 - 6, 231), "2x", font=f_xs, fill=C_WHITE + (255,))

    elif ctype == "clock":
        ocx, ocy, rad = 10 + cw // 2, 230, 105
        d.ellipse([ocx - rad, ocy - rad, ocx + rad, ocy + rad], fill=(252, 248, 240, 255), outline=C_ORANGE + (255,), width=12)
        ang = -math.pi / 3 + pop_t * 1.4
        d.line([(ocx, ocy), (ocx + int(72 * math.cos(ang)), ocy + int(72 * math.sin(ang)))], fill=C_MAROON + (255,), width=7)
        d.line([(ocx, ocy), (ocx, ocy - 55)], fill=C_INK + (255,), width=7)
        d.ellipse([ocx - 9, ocy - 9, ocx + 9, ocy + 9], fill=C_ORANGE + (255,))

    elif ctype == "cross":
        vbb = d.textbbox((0, 0), val[:14], font=f_md)
        d.text((10 + (cw - (vbb[2] - vbb[0])) // 2, 195), val[:14], font=f_md, fill=C_MAROON + (255,))
        if pop_t > 0.25:
            p = clamp((pop_t - 0.25) / 0.5)
            d.line([(45, 115), (45 + int((cw - 70) * p), 115 + int(230 * p))], fill=C_ORANGE + (255,), width=12)
            d.line([(cw - 25, 115), (cw - 25 - int((cw - 70) * p), 115 + int(230 * p))], fill=C_ORANGE + (255,), width=12)

    elif ctype == "save":
        d.rounded_rectangle([40, 108, cw - 20, 310], radius=20, fill=C_GOLD + (255,))
        vbb = d.textbbox((0, 0), title[:14], font=f_sm)
        d.text((10 + (cw - (vbb[2] - vbb[0])) // 2, 185), title[:14], font=f_sm, fill=C_INK + (255,))
        # Saved pill
        d.rounded_rectangle([95, 335, cw - 75, 388], radius=24, fill=C_MAROON + (255,))
        d.text((135, 347), "Saved ✓", font=f_xs, fill=C_WHITE + (255,))

    elif ctype == "share":
        # Two clean minimal avatars + dashed send arc
        for ax, ay in [(115, 275), (cw - 95, 175)]:
            d.ellipse([ax - 24, ay - 52, ax + 24, ay - 4], fill=C_ORANGE + (255,))
            d.pieslice([ax - 44, ay + 2, ax + 44, ay + 75], 180, 360, fill=C_MAROON + (255,))
        d.line([(165, 255), (cw - 145, 195)], fill=C_ORANGE + (255,), width=6)

    elif ctype == "comment":
        d.rounded_rectangle([32, 165, cw - 12, 245], radius=36, fill=(246, 240, 230, 255), outline=C_MAROON + (255,), width=4)
        d.text((54, 190), val[:18], font=f_xs, fill=C_INK + (255,))
        d.ellipse([cw - 76, 177, cw - 24, 231], fill=C_ORANGE + (255,))

    else:
        # Timer / Badge big crisp display
        vfont = f_md if len(val) <= 10 else f_sm
        vbb = d.textbbox((0, 0), val[:14], font=vfont)
        d.text((10 + (cw - (vbb[2] - vbb[0])) // 2, 195), val[:14], font=vfont, fill=C_INK + (255,))

    if sub:
        sbb = d.textbbox((0, 0), sub, font=f_xs)
        d.text((10 + (cw - (sbb[2] - sbb[0])) // 2, ch - 42), sub, font=f_xs, fill=C_ORANGE + (255,))

    canvas.alpha_composite(card, (int(cx - card.width // 2), int(cy - card.height // 2)))


def render_cover_frame():
    """Frame 0 Cover Thumbnail matching video_2.mp4 opening layout."""
    canvas = BG_CREAM.copy()
    d = ImageDraw.Draw(canvas)
    draw_3d_hero_text(d, W // 2, 680, THUMB_HERO, color_key="maroon")
    draw_pill_subtitle(d, W // 2, 860, THUMB_SUB, THUMB_SUB.split()[0], is_dark_bg=False)
    fake_b = {"card": "timer", "card_title": "MUST WATCH", "card_val": THUMB_BADGE, "card_sub": "@sochbadlo.hq"}
    draw_vector_card(canvas, W // 2, 1280, fake_b, 1.0)
    return canvas


def render_frame(b, lt, dur):
    is_maroon = (b.get("bg") == "maroon")
    canvas = (BG_MAROON if is_maroon else BG_CREAM).copy()
    d = ImageDraw.Draw(canvas)

    enter_t = ease_out_back(lt / 0.28)
    has_card = (b.get("card", "none") != "none")

    if has_card:
        # Side-by-side / Balanced upper-lower composition matching video_2.mp4
        hero_x = 340 if b["index"] % 2 == 0 else 740
        card_x = 795 if b["index"] % 2 == 0 else 285
        hero_y = 780 - int((1.0 - enter_t) * 50)
        draw_3d_hero_text(
            d, hero_x, hero_y, b["hero"],
            color_key=b.get("hero_color", "maroon"),
            strike_prog=(lt - 0.25) / 0.35 if b.get("strike") else 0.0
        )
        draw_pill_subtitle(d, hero_x, hero_y + 150, b["sub"], b["pill"], is_dark_bg=is_maroon)
        draw_vector_card(canvas, card_x, 860, b, clamp((lt - 0.12) / 0.35))
    else:
        # Center hero kinetic typography (like video_1.mp4 & video_2.mp4 punch beats)
        hero_y = 840 - int((1.0 - enter_t) * 55)
        draw_3d_hero_text(
            d, W // 2, hero_y, b["hero"],
            color_key=b.get("hero_color", "maroon"),
            strike_prog=(lt - 0.25) / 0.35 if b.get("strike") else 0.0
        )
        draw_pill_subtitle(d, W // 2, hero_y + 160, b["sub"], b["pill"], is_dark_bg=is_maroon)

    # Subtle watermark at bottom like @grower_talk in video_1
    wbb = d.textbbox((0, 0), "@sochbadlo.hq", font=f_xs)
    wcol = (220, 200, 190, 150) if is_maroon else (120, 95, 85, 150)
    d.text(((W - (wbb[2] - wbb[0])) // 2, H - 150), "@sochbadlo.hq", font=f_xs, fill=wcol)
    return canvas


total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) of V21 Kinetic Explainer Reel...")

ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(FPS),
    "-i", "-", "-i", "final_audio.m4a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "final_reel.mp4"
], stdin=subprocess.PIPE)

cover_0 = render_cover_frame()

for frame in range(total_frames):
    if frame == 0:
        ffmpeg.stdin.write(cover_0.tobytes())
        continue

    t = frame / FPS
    active_b = beats[-1]
    for b in beats:
        if b["start"] <= t < b["start"] + b["duration"]:
            active_b = b
            break

    lt = t - active_b["start"]
    img = render_frame(active_b, lt, active_b["duration"])
    ffmpeg.stdin.write(img.tobytes())

    if frame % 300 == 0:
        print(f"Rendered {frame}/{total_frames} frames...")

ffmpeg.stdin.close()
ffmpeg.wait()
print("100% DONE! V21 Kinetic Explainer Reel rendered successfully.")
