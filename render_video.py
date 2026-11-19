import json
import math
import os
import subprocess
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

with open("timeline.json") as f:
    data = json.load(f)

total_dur = data["total_duration"]
scenes = data["scenes"]
DNA = data.get("edit_dna", {})

ACCENT = tuple(DNA.get("accent", [244, 63, 94]))
HIGHLIGHT = tuple(DNA.get("highlight", [250, 204, 21]))
LAYOUT = DNA.get("layout_mode", "center_cinema")
CAP_STYLE = DNA.get("caption_style", "neon_stroke")
TRANSITION = DNA.get("transition", "flash_cut")

W, H = 1080, 1920
FPS = 30

os.makedirs("fonts", exist_ok=True)
FONT_URLS = {
    "fonts/Poppins-ExtraBold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf",
    "fonts/Poppins-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
    "fonts/Playfair-BoldItalic.ttf": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-BoldItalic.ttf",
}
for dest, url in FONT_URLS.items():
    if not os.path.exists(dest):
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as e:
            print("Font fallback:", e)

def load_font(path, fallback, size):
    for p in [path, fallback, "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"]:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, int(size))
            except:
                pass
    return ImageFont.load_default()

f_xs = load_font("fonts/Poppins-SemiBold.ttf", "", 28)
f_kicker = load_font("fonts/Poppins-SemiBold.ttf", "", 30)
f_headline = load_font("fonts/Poppins-ExtraBold.ttf", "", 66)
f_serif = load_font("fonts/Playfair-BoldItalic.ttf", "fonts/Poppins-ExtraBold.ttf", 72)
f_caption = load_font("fonts/Poppins-ExtraBold.ttf", "", 54)
f_caption_big = load_font("fonts/Poppins-ExtraBold.ttf", "", 62)

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
vd = ImageDraw.Draw(vignette)
for y in range(0, 640):
    alpha = int(215 * (1.0 - y / 640.0))
    vd.line([(0, y), (W, y)], fill=(6, 8, 14, alpha))
for y in range(900, H):
    alpha = int(240 * ((y - 900) / float(H - 900)))
    vd.line([(0, y), (W, y)], fill=(6, 8, 14, alpha))

bg_images = []
for sc in scenes:
    im = Image.open(sc["bg_path"]).convert("RGB")
    im = im.resize((1260, 2240), Image.Resampling.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.16)
    im = ImageEnhance.Brightness(im).enhance(0.84)
    bg_images.append(im)

def get_animated_bg(sc_idx, lt, sc_dur):
    src = bg_images[sc_idx]
    prog = clamp(lt / max(0.1, sc_dur))
    mode = sc_idx % 4
    if mode == 0:
        scale = 1.0 + 0.12 * prog
        cw, ch = int(W / scale), int(H / scale)
        x1, y1 = (1260 - cw) // 2, (2240 - ch) // 2
    elif mode == 1:
        cw, ch = 1080, 1920
        x1, y1 = int(180 * prog), 160
    elif mode == 2:
        scale = 1.12 - 0.12 * prog
        cw, ch = int(W / scale), int(H / scale)
        x1, y1 = (1260 - cw) // 2, (2240 - ch) // 2
    else:
        cw, ch = 1080, 1920
        x1, y1 = int(180 * (1.0 - prog)), 160

    cropped = src.crop((x1, y1, x1 + cw, y1 + ch))
    if (cw, ch) != (W, H):
        cropped = cropped.resize((W, H), Image.Resampling.BILINEAR)
    frame = cropped.convert("RGBA")
    frame.alpha_composite(vignette)
    return frame

def wrap_text(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

def draw_layout_header(canvas, sc, sc_idx, lt):
    d = ImageDraw.Draw(canvas)
    p = ease_out_back(lt / 0.35)
    dy = int((1.0 - p) * 35)
    alpha = int(clamp(p) * 255)
    kicker = sc["kicker"]
    headline = sc["headline"]
    badge = sc.get("stat_badge", "INSIGHT")

    if LAYOUT == "glass_editorial":
        card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([80, 150 + dy, W - 80, 465 + dy], radius=36, fill=(14, 18, 30, int(alpha * 0.82)), outline=ACCENT + (alpha,), width=3)
        canvas.alpha_composite(card)
        d = ImageDraw.Draw(canvas)

        d.rounded_rectangle([125, 185 + dy, 355, 235 + dy], radius=22, fill=ACCENT + (alpha,))
        d.text((150, 194 + dy), f"0{sc_idx+1} • {badge}", font=f_xs, fill=(255, 255, 255, alpha))

        lines = wrap_text(d, headline, f_headline, 820)[:2]
        for idx, line in enumerate(lines):
            d.text((125, 260 + idx * 84 + dy), line, font=f_headline, fill=(255, 255, 255, alpha))

    elif LAYOUT == "editorial_frame":
        d.rounded_rectangle([55, 135, W - 55, H - 135], radius=42, outline=ACCENT + (140,), width=3)
        kb = d.textbbox((0, 0), kicker, font=f_kicker)
        kw = kb[2] - kb[0]
        d.text(((W - kw) // 2, 185 + dy), f"— {kicker} —", font=f_kicker, fill=HIGHLIGHT + (alpha,))

        lines = wrap_text(d, headline, f_serif, 880)[:2]
        for idx, line in enumerate(lines):
            lb = d.textbbox((0, 0), line, font=f_serif)
            lw = lb[2] - lb[0]
            lx = (W - lw) // 2
            ly = 245 + idx * 88 + dy
            d.text((lx + 4, ly + 6), line, font=f_serif, fill=(0, 0, 0, int(alpha * 0.8)))
            d.text((lx, ly), line, font=f_serif, fill=(255, 255, 255, alpha))

    elif LAYOUT == "split_hud":
        d.rounded_rectangle([85, 175 + dy, 102, 430 + dy], radius=8, fill=ACCENT + (alpha,))
        d.text((130, 175 + dy), f"// {kicker}", font=f_kicker, fill=HIGHLIGHT + (alpha,))
        lines = wrap_text(d, headline, f_headline, 860)[:2]
        for idx, line in enumerate(lines):
            ly = 230 + idx * 84 + dy
            d.text((134, ly + 5), line, font=f_headline, fill=(0, 0, 0, int(alpha * 0.8)))
            d.text((130, ly), line, font=f_headline, fill=(255, 255, 255, alpha))

    else:
        kb = d.textbbox((0, 0), kicker, font=f_kicker)
        kw = kb[2] - kb[0]
        d.rounded_rectangle([(W - kw)//2 - 28, 165 + dy, (W + kw)//2 + 28, 222 + dy], radius=28, fill=ACCENT + (alpha,))
        d.text(((W - kw) // 2, 176 + dy), kicker, font=f_kicker, fill=(255, 255, 255, alpha))

        lines = wrap_text(d, headline, f_headline, 920)[:2]
        for idx, line in enumerate(lines):
            lb = d.textbbox((0, 0), line, font=f_headline)
            lw = lb[2] - lb[0]
            lx = (W - lw) // 2
            ly = 255 + idx * 86 + dy
            d.text((lx + 4, ly + 6), line, font=f_headline, fill=(0, 0, 0, int(alpha * 0.75)))
            d.text((lx, ly), line, font=f_headline, fill=(255, 255, 255, alpha))

def draw_viral_captions(canvas, text, lt, sc_dur):
    words = text.split()
    if not words:
        return
    chunk_size = 3
    total_chunks = math.ceil(len(words) / chunk_size)
    chunk_idx = min(total_chunks - 1, int((lt / max(0.1, sc_dur)) * total_chunks))
    chunk = words[chunk_idx * chunk_size : (chunk_idx + 1) * chunk_size]

    chunk_dur = sc_dur / max(1, total_chunks)
    chunk_local = lt - chunk_idx * chunk_dur
    active_idx = min(len(chunk) - 1, int((chunk_local / max(0.05, chunk_dur)) * len(chunk)))

    d = ImageDraw.Draw(canvas)
    boxes = []
    tot_w = 0
    for i, w in enumerate(chunk):
        fnt = f_caption_big if i == active_idx else f_caption
        bb = d.textbbox((0, 0), w, font=fnt)
        ww = bb[2] - bb[0]
        boxes.append((w, ww, fnt))
        tot_w += ww + 24
    tot_w -= 24

    cy = 1360
    if CAP_STYLE == "glass_pill":
        d.rounded_rectangle([max(50, (W - tot_w)//2 - 36), cy - 22, min(W - 50, (W + tot_w)//2 + 36), cy + 88], radius=32, fill=(10, 12, 20, 215), outline=ACCENT + (200,), width=3)

    cx = (W - tot_w) // 2
    for i, (w, ww, fnt) in enumerate(boxes):
        is_act = (i == active_idx)
        col = HIGHLIGHT if is_act else (255, 255, 255)
        y_shift = -8 if is_act else 0

        if is_act and CAP_STYLE == "bold_box":
            d.rounded_rectangle([int(cx - 14), int(cy + y_shift - 8), int(cx + ww + 14), int(cy + y_shift + 76)], radius=18, fill=ACCENT + (245,))
            col = (255, 255, 255)

        for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (4, 6)]:
            d.text((int(cx + ox), int(cy + y_shift + oy)), w, font=fnt, fill=(0, 0, 0, 235))
        d.text((int(cx), int(cy + y_shift)), w, font=fnt, fill=col + (255,))

        if is_act and CAP_STYLE == "underline_glow":
            d.rounded_rectangle([int(cx), int(cy + 74), int(cx + ww), int(cy + 84)], radius=5, fill=ACCENT + (255,))
        cx += ww + 24

total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) | Layout: {LAYOUT} | Captions: {CAP_STYLE}...")

ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(FPS),
    "-i", "-", "-i", "final_audio.m4a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "final_reel.mp4"
], stdin=subprocess.PIPE)

for frame in range(total_frames):
    t = frame / FPS
    active_sc = scenes[-1]
    sc_idx = len(scenes) - 1
    for i, sc in enumerate(scenes):
        if sc["start"] <= t < sc["start"] + sc["duration"]:
            active_sc = sc
            sc_idx = i
            break

    lt = t - active_sc["start"]
    frame_img = get_animated_bg(sc_idx, lt, active_sc["duration"])
    d = ImageDraw.Draw(frame_img)

    prog_w = int((t / total_dur) * W)
    d.rectangle([0, 0, W, 12], fill=(255, 255, 255, 60))
    d.rectangle([0, 0, prog_w, 12], fill=ACCENT + (255,))

    for i in range(6):
        eh = int(12 + 24 * abs(math.sin(t * 11 + i * 1.2)))
        d.rounded_rectangle([910 + i * 16, 75 - eh // 2, 910 + i * 16 + 9, 75 + eh // 2], radius=4, fill=ACCENT + (220,))

    draw_layout_header(frame_img, active_sc, sc_idx, lt)
    draw_viral_captions(frame_img, active_sc["voice"], lt, active_sc["duration"])

    rem = (active_sc["start"] + active_sc["duration"]) - t
    if sc_idx < len(scenes) - 1 and rem < 0.18:
        wp = clamp((0.18 - rem) / 0.18)
        if TRANSITION == "flash_cut":
            overlay = Image.new("RGBA", (W, H), (255, 255, 255, int(195 * wp)))
            frame_img.alpha_composite(overlay)
        elif TRANSITION == "iris_zoom":
            rad = int(1250 * wp)
            d.ellipse([W // 2 - rad, H // 2 - rad, W // 2 + rad, H // 2 + rad], fill=ACCENT + (255,))
        elif TRANSITION == "curtain_wipe":
            bw = int((W // 2) * wp)
            d.rectangle([0, 0, bw, H], fill=ACCENT + (255,))
            d.rectangle([W - bw, 0, W, H], fill=ACCENT + (255,))
        else:
            bh = int(H * wp)
            d.rectangle([0, H - bh, W, H], fill=ACCENT + (255,))

    ffmpeg.stdin.write(frame_img.tobytes())
    if frame % 300 == 0:
        print(f"Rendered {frame}/{total_frames} frames...")

ffmpeg.stdin.close()
ffmpeg.wait()
print("100% DONE! Multi-Format Viral Reel v9 rendered successfully.")
