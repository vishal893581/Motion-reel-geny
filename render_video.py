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
PAL = DNA.get("palette", {
    "is_light": False,
    "bg": [11, 15, 28],
    "card": [20, 27, 48],
    "card_border": [46, 58, 92],
    "text_main": [248, 250, 252],
    "text_muted": [148, 163, 184],
    "accent": [56, 189, 248],
    "secondary": [251, 191, 36],
    "positive": [52, 211, 153],
    "negative": [251, 113, 133]
})

IS_LIGHT = PAL.get("is_light", False)
BG_COL = tuple(PAL.get("bg", [11, 15, 28]))
CARD_BG = tuple(PAL.get("card", [20, 27, 48]))
CARD_BORDER = tuple(PAL.get("card_border", [46, 58, 92]))
TXT_MAIN = tuple(PAL.get("text_main", [248, 250, 252]))
TXT_MUTED = tuple(PAL.get("text_muted", [148, 163, 184]))
ACCENT = tuple(PAL.get("accent", [56, 189, 248]))
SECONDARY = tuple(PAL.get("secondary", [251, 191, 36]))
POSITIVE = tuple(PAL.get("positive", [52, 211, 153]))
NEGATIVE = tuple(PAL.get("negative", [251, 113, 133]))
TRANSITION = DNA.get("transition", "smooth_curtain")

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

f_xs = load_font("fonts/Poppins-SemiBold.ttf", "", 26)
f_sm = load_font("fonts/Poppins-SemiBold.ttf", "", 34)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", "", 44)
f_headline = load_font("fonts/Poppins-ExtraBold.ttf", "", 62)
f_serif = load_font("fonts/Playfair-BoldItalic.ttf", "fonts/Poppins-ExtraBold.ttf", 68)
f_big = load_font("fonts/Poppins-ExtraBold.ttf", "", 116)
f_caption = load_font("fonts/Poppins-ExtraBold.ttf", "", 50)
f_caption_big = load_font("fonts/Poppins-ExtraBold.ttf", "", 58)

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_out_cubic(t):
    t = clamp(t)
    return 1 - pow(1 - t, 3)

vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
if not IS_LIGHT:
    vd = ImageDraw.Draw(vignette)
    for y in range(0, 480):
        alpha = int(175 * (1.0 - y / 480.0))
        vd.line([(0, y), (W, y)], fill=(BG_COL[0], BG_COL[1], BG_COL[2], alpha))
    for y in range(1250, H):
        alpha = int(200 * ((y - 1250) / float(H - 1250)))
        vd.line([(0, y), (W, y)], fill=(BG_COL[0], BG_COL[1], BG_COL[2], alpha))

bg_images = []
for sc in scenes:
    im = Image.open(sc["bg_path"]).convert("RGB")
    im = im.resize((1260, 2240), Image.Resampling.LANCZOS)
    if not IS_LIGHT:
        im = ImageEnhance.Contrast(im).enhance(1.12)
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
    if not IS_LIGHT:
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

def draw_text_clean(draw, pos, text, font, fill, alpha=255):
    x, y = int(pos[0]), int(pos[1])
    if not IS_LIGHT:
        draw.text((x + 2, y + 4), text, font=font, fill=(0, 0, 0, int(alpha * 0.55)))
    draw.text((x, y), text, font=font, fill=fill + (alpha,))

def draw_center_text(draw, y, text, font, fill, alpha=255):
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    x = (W - tw) // 2
    draw_text_clean(draw, (x, y), text, font, fill, alpha=alpha)

def draw_elevated_card(canvas, box, radius=38, border_col=CARD_BORDER, border_w=3, alpha=245):
    x1, y1, x2, y2 = [int(v) for v in box]
    if x2 <= x1 or y2 <= y1:
        return
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sh_alpha = 36 if IS_LIGHT else 120
    sd.rounded_rectangle([x1, y1 + 18, x2, y2 + 18], radius=radius, fill=(15, 23, 42, sh_alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.alpha_composite(shadow)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=CARD_BG + (alpha,), outline=border_col + (255,), width=border_w)
    ld.rounded_rectangle([x1 + 36, y1 + 2, x2 - 36, y1 + 7], radius=3, fill=ACCENT + (210,))
    canvas.alpha_composite(layer)

def draw_center_motion_graphic(canvas, sc, lt, sc_dur):
    w_type = sc.get("widget", "radar_scanner")
    p_in = ease_out_back(lt / 0.42)
    alpha = int(clamp(p_in) * 255)
    cy_mid = 885

    if w_type == "radar_scanner":
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cx, cy = W // 2, cy_mid
        for r_idx, base_r in enumerate([165, 245, 325]):
            pulse = int(base_r + 12 * math.sin(lt * 5 - r_idx))
            ring_a = (130 - r_idx * 30) if not IS_LIGHT else (170 - r_idx * 35)
            ld.ellipse([cx - pulse, cy - pulse, cx + pulse, cy + pulse], outline=ACCENT + (ring_a,), width=4)
        ang = int((lt * 210) % 360)
        ld.pieslice([cx - 315, cy - 315, cx + 315, cy + 315], start=ang, end=ang + 50, fill=ACCENT + (32 if IS_LIGHT else 50,))
        for k in range(3):
            oa = lt * 2.2 + k * 2.09
            ox = int(cx + 245 * math.cos(oa))
            oy = int(cy + 245 * math.sin(oa))
            ld.ellipse([ox - 13, oy - 13, ox + 13, oy + 13], fill=SECONDARY + (255,))
        canvas.alpha_composite(layer)

        draw_elevated_card(canvas, [215, cy - 140, 865, cy + 140], radius=42, border_col=ACCENT, border_w=4, alpha=248)
        d = ImageDraw.Draw(canvas)
        draw_center_text(d, cy - 95, sc["metric_big"], f_big, ACCENT, alpha=alpha)
        draw_center_text(d, cy + 48, sc["metric_label"], f_xs, TXT_MUTED, alpha=alpha)

    elif w_type == "vs_clash_cards":
        p1 = ease_out_back(lt / 0.38)
        p2 = ease_out_back((lt - 0.45) / 0.38)
        off1 = int((1.0 - p1) * -450)
        off2 = int((1.0 - p2) * 450)

        draw_elevated_card(canvas, [95 + off1, 610, 505 + off1, 1085], radius=36, border_col=CARD_BORDER, border_w=3, alpha=245)
        d = ImageDraw.Draw(canvas)
        d.text((140 + off1, 658), "✕  AVOID THIS", font=f_xs, fill=NEGATIVE + (255,))
        for idx, ln in enumerate(wrap_text(d, sc["left_label"], f_md, 340)[:2]):
            draw_text_clean(d, (140 + off1, 740 + idx * 58), ln, f_md, TXT_MAIN)
        track_c = (226, 232, 240) if IS_LIGHT else (45, 55, 80)
        d.rounded_rectangle([140 + off1, 955, 460 + off1, 988], radius=14, fill=track_c + (255,))
        d.rounded_rectangle([140 + off1, 955, 140 + off1 + int(115 * clamp(p1)), 988], radius=14, fill=NEGATIVE + (255,))

        if lt > 0.35:
            draw_elevated_card(canvas, [575 + off2, 610, 985 + off2, 1085], radius=36, border_col=ACCENT, border_w=4, alpha=250)
            d = ImageDraw.Draw(canvas)
            d.text((620 + off2, 658), "✓  SMART MOVE", font=f_xs, fill=POSITIVE + (255,))
            for idx, ln in enumerate(wrap_text(d, sc["right_label"], f_md, 340)[:2]):
                draw_text_clean(d, (620 + off2, 740 + idx * 58), ln, f_md, TXT_MAIN)
            d.rounded_rectangle([620 + off2, 955, 940 + off2, 988], radius=14, fill=track_c + (255,))
            d.rounded_rectangle([620 + off2, 955, 620 + off2 + int(320 * clamp(p2)), 988], radius=14, fill=POSITIVE + (255,))

        if lt > 0.6:
            vp = ease_out_back((lt - 0.6) / 0.25)
            vr = int(48 * clamp(vp))
            d.ellipse([W // 2 - vr, 848 - vr, W // 2 + vr, 848 + vr], fill=ACCENT + (255,))
            if vp > 0.7:
                bb = d.textbbox((0, 0), "VS", font=f_sm)
                d.text(((W - (bb[2] - bb[0])) // 2, 828), "VS", font=f_sm, fill=(255, 255, 255, 255))

    elif w_type == "animated_bar_chart":
        draw_elevated_card(canvas, [105, 580, 975, 1135], radius=40, border_col=CARD_BORDER, border_w=3, alpha=248)
        d = ImageDraw.Draw(canvas)
        d.text((160, 628), f"GROWTH CURVE • {sc['metric_label']}", font=f_xs, fill=TXT_MUTED + (255,))
        d.text((735, 618), sc["metric_big"], font=f_md, fill=ACCENT + (255,))

        heights = [0.30, 0.46, 0.64, 0.82, 1.0]
        base_y = 1050
        muted_bar = (203, 213, 225) if IS_LIGHT else (60, 74, 102)
        for i, h_mul in enumerate(heights):
            bp = ease_out_cubic((lt - i * 0.14) / 0.55)
            bh = int(315 * h_mul * bp)
            bx = 180 + i * 152
            col = ACCENT if i == 4 else (SECONDARY if i == 3 else muted_bar)
            d.rounded_rectangle([bx, base_y - bh, bx + 96, base_y], radius=20, fill=col + (255,))

    elif w_type == "circular_gauge":
        pct = sc.get("pct", 94)
        gp = ease_out_cubic(lt / 1.15)
        cur_val = int(pct * gp)
        draw_elevated_card(canvas, [165, 565, 915, 1150], radius=44, border_col=CARD_BORDER, border_w=3, alpha=248)
        d = ImageDraw.Draw(canvas)
        cx, cy, r = W // 2, 838, 185
        track_c = (226, 232, 240) if IS_LIGHT else (48, 60, 88)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=track_c + (255,), width=28)
        d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + int(360 * (cur_val / 100.0)), fill=ACCENT + (255,), width=28)
        draw_center_text(d, cy - 65, f"{cur_val}%", f_big, TXT_MAIN)
        draw_center_text(d, cy + 68, sc["metric_label"], f_xs, ACCENT)

    elif w_type == "floating_checklist":
        rows = [
            ("01", sc["left_label"], TXT_MUTED, 0.15),
            ("02", sc["right_label"], ACCENT, 0.65),
            ("03", sc["metric_label"], POSITIVE, 1.15)
        ]
        for idx, (num, label, badge_c, delay) in enumerate(rows):
            if lt > delay:
                rp = ease_out_back((lt - delay) / 0.35)
                ry = int(585 + idx * 185 + (1.0 - rp) * 55)
                draw_elevated_card(canvas, [115, ry, 965, ry + 148], radius=32, border_col=badge_c if idx > 0 else CARD_BORDER, border_w=3, alpha=248)
                d = ImageDraw.Draw(canvas)
                d.rounded_rectangle([155, ry + 34, 235, ry + 114], radius=22, fill=badge_c + (255,))
                d.text((174, ry + 52), num, font=f_sm, fill=(255, 255, 255, 255))
                draw_text_clean(d, (270, ry + 50), label, f_md, TXT_MAIN)

    else:
        draw_elevated_card(canvas, [125, 595, 955, 1115], radius=42, border_col=CARD_BORDER, border_w=3, alpha=248)
        d = ImageDraw.Draw(canvas)
        draw_center_text(d, 648, sc["metric_big"], f_big, ACCENT)
        draw_center_text(d, 795, sc["metric_label"], f_sm, TXT_MUTED)
        for b in range(18):
            bh = int(18 + 75 * abs(math.sin(lt * 10 + b * 0.65)))
            bx = 192 + b * 39
            bar_c = ACCENT if b % 3 != 0 else SECONDARY
            d.rounded_rectangle([bx, 1035 - bh, bx + 22, 1035], radius=9, fill=bar_c + (240,))

def draw_top_header(canvas, sc, lt):
    d = ImageDraw.Draw(canvas)
    p = ease_out_back(lt / 0.32)
    dy = int((1.0 - p) * 28)
    alpha = int(clamp(p) * 255)

    kb = d.textbbox((0, 0), sc["kicker"], font=f_xs)
    kw = kb[2] - kb[0]
    pill_bg = ACCENT if not IS_LIGHT else tuple(int(BG_COL[i] * 0.85 + ACCENT[i] * 0.15) for i in range(3))
    pill_fg = (255, 255, 255) if not IS_LIGHT else ACCENT
    d.rounded_rectangle([(W - kw)//2 - 30, 128 + dy, (W + kw)//2 + 30, 184 + dy], radius=28, fill=pill_bg + (alpha,), outline=ACCENT + (alpha,), width=2)
    d.text(((W - kw) // 2, 140 + dy), sc["kicker"], font=f_xs, fill=pill_fg + (alpha,))

    lines = wrap_text(d, sc["headline"], f_headline, 920)[:2]
    for idx, line in enumerate(lines):
        lb = d.textbbox((0, 0), line, font=f_headline)
        lw = lb[2] - lb[0]
        lx = (W - lw) // 2
        ly = 214 + idx * 80 + dy
        draw_text_clean(d, (lx, ly), line, f_headline, TXT_MAIN, alpha=alpha)

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
        tot_w += ww + 22
    tot_w -= 22

    cy = 1370
    cap_bg = (15, 23, 42, 235)
    d.rounded_rectangle([max(45, (W - tot_w)//2 - 36), cy - 20, min(W - 45, (W + tot_w)//2 + 36), cy + 86], radius=32, fill=cap_bg, outline=ACCENT + (200,), width=3)

    cx = (W - tot_w) // 2
    for i, (w, ww, fnt) in enumerate(boxes):
        is_act = (i == active_idx)
        col = SECONDARY if is_act else (255, 255, 255)
        y_shift = -5 if is_act else 0
        d.text((int(cx), int(cy + y_shift)), w, font=fnt, fill=col + (255,))
        cx += ww + 22

total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) of Luxury Agency-Grade Motion Graphics...")

ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(FPS),
    "-i", "-", "-i", "final_audio.m4a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
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
    track_top = (216, 224, 238, 220) if IS_LIGHT else (255, 255, 255, 50)
    d.rectangle([0, 0, W, 12], fill=track_top)
    d.rectangle([0, 0, prog_w, 12], fill=ACCENT + (255,))
    for i in range(6):
        eh = int(12 + 22 * abs(math.sin(t * 11 + i * 1.2)))
        d.rounded_rectangle([910 + i * 16, 68 - eh // 2, 910 + i * 16 + 9, 68 + eh // 2], radius=4, fill=ACCENT + (230,))

    draw_top_header(frame_img, active_sc, lt)
    draw_center_motion_graphic(frame_img, active_sc, lt, active_sc["duration"])
    draw_viral_captions(frame_img, active_sc["voice"], lt, active_sc["duration"])

    rem = (active_sc["start"] + active_sc["duration"]) - t
    if sc_idx < len(scenes) - 1 and rem < 0.22:
        wp = clamp((0.22 - rem) / 0.22)
        if TRANSITION == "iris_reveal":
            rad = int(1250 * wp)
            d.ellipse([W // 2 - rad, H // 2 - rad, W // 2 + rad, H // 2 + rad], fill=ACCENT + (255,))
        elif TRANSITION == "prism_wipe":
            bw = int((W // 2) * wp)
            d.rectangle([0, 0, bw, H], fill=ACCENT + (255,))
            d.rectangle([W - bw, 0, W, H], fill=SECONDARY + (255,))
        else:
            bh = int(H * wp)
            d.rectangle([0, H - bh, W, H], fill=ACCENT + (255,))

    ffmpeg.stdin.write(frame_img.tobytes())
    if frame % 300 == 0:
        print(f"Rendered {frame}/{total_frames} frames...")

ffmpeg.stdin.close()
ffmpeg.wait()
print("100% DONE! Luxury Pro Studio Reel v11 rendered successfully.")
