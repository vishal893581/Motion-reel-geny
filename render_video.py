import json
import math
import os
import subprocess
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

with open("timeline.json") as f:
    timeline = json.load(f)

with open("script_data.json") as f:
    S = json.load(f)

DNA = S.get("_visual_dna", {})
PAL = DNA.get("palette", {
    "name": "obsidian_crimson", "primary": [244, 63, 94], "secondary": [251, 191, 36],
    "dark": [248, 250, 252], "soft": [30, 27, 38], "tint": [24, 24, 34],
    "bg": [11, 11, 16], "grid": [32, 32, 46], "is_dark": True
})

T = {k: tuple(v) if isinstance(v, list) else v for k, v in PAL.items()}
IS_DARK = T.get("is_dark", True)
CARD_BG = (20, 22, 34) if IS_DARK else (255, 255, 255)
CARD_BORDER = (48, 54, 78) if IS_DARK else (226, 232, 240)
MUTED_TXT = (156, 163, 175) if IS_DARK else (100, 116, 139)

BG_PATTERN = DNA.get("bg_pattern", "grid")
TRANSITION = DNA.get("transition", "shutter_v")
WIDGETS = DNA.get("widgets", {})

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
f_sm = load_font("fonts/Poppins-SemiBold.ttf", "", 34)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", "", 44)
f_lg = load_font("fonts/Poppins-ExtraBold.ttf", "", 64)
f_serif = load_font("fonts/Playfair-BoldItalic.ttf", "fonts/Poppins-ExtraBold.ttf", 70)
f_xl = load_font("fonts/Poppins-ExtraBold.ttf", "", 104)
f_mega = load_font("fonts/Poppins-ExtraBold.ttf", "", 148)

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

base_bg = Image.new("RGBA", (W, H), T["bg"] + (255,))
bg_d = ImageDraw.Draw(base_bg)

if BG_PATTERN == "grid":
    for x in range(0, W, 64):
        bg_d.line([(x, 0), (x, H)], fill=T["grid"] + (160,), width=2)
    for y in range(0, H, 64):
        bg_d.line([(0, y), (W, y)], fill=T["grid"] + (160,), width=2)
elif BG_PATTERN == "dots":
    for x in range(32, W, 64):
        for y in range(32, H, 64):
            bg_d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=T["grid"] + (210,))
elif BG_PATTERN == "diagonal":
    for i in range(-H, W + H, 72):
        bg_d.line([(i, 0), (i + H, H)], fill=T["grid"] + (145,), width=2)
elif BG_PATTERN == "concentric":
    cx, cy = W // 2, H // 2
    for r in range(120, 1400, 110):
        bg_d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=T["grid"] + (150,), width=2)

glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([100, -180, 980, 640], fill=T["primary"] + (65 if IS_DARK else 35,))
gd.ellipse([200, 1350, 900, 2050], fill=T["secondary"] + (45 if IS_DARK else 25,))
glow = glow.filter(ImageFilter.GaussianBlur(110))
base_bg.alpha_composite(glow)

def draw_card(canvas, box, radius=40, fill=None, outline=None, width=0):
    if fill is None:
        fill = CARD_BG
    x1, y1, x2, y2 = [int(v) for v in box]
    if x2 <= x1 or y2 <= y1:
        return
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x1, y1 + 22, x2, y2 + 22], radius=radius, fill=(0, 0, 0, 110 if IS_DARK else 42))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    canvas.alpha_composite(shadow)

    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill + (255,), outline=outline, width=width)

def draw_txt(draw, pos, text, font, fill, alpha=255, shadow=True):
    x, y = int(pos[0]), int(pos[1])
    if shadow:
        draw.text((x, y + 5), text, font=font, fill=(0, 0, 0, int(alpha * (0.55 if IS_DARK else 0.16))))
    draw.text((x, y), text, font=font, fill=fill + (int(alpha),))

def draw_center(draw, y, text, font, fill, alpha=255, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw_txt(draw, ((W - tw) // 2, y), text, font, fill, alpha=alpha, shadow=shadow)

def draw_heading(canvas, y_start, lines, local_t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    word_idx = 0
    for line_idx, segments in enumerate(lines):
        total_w = 0
        rendered = []
        for seg in segments:
            txt, col, fnt = seg[0], seg[1], seg[2]
            mode = seg[3] if len(seg) > 3 else "normal"
            bbox = d.textbbox((0, 0), txt, font=fnt)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pad_x = 26 if mode == "pill" else 0
            rendered.append((txt, col, fnt, mode, w, h, pad_x))
            total_w += w + pad_x * 2 + 18
        total_w -= 18
        cur_x = (W - total_w) // 2

        for txt, col, fnt, mode, w, h, pad_x in rendered:
            p = ease_out_back((local_t - word_idx * 0.08) / 0.35)
            dy = (1.0 - p) * 40
            alpha = int(clamp(p) * 255)
            bx, by = int(cur_x), int(y_start + line_idx * 94 + dy)

            if mode == "pill" and alpha > 20:
                d.rounded_rectangle([bx, by - 6, bx + w + pad_x * 2, by + h + 22], radius=24, fill=col + (alpha,))
                draw_txt(d, (bx + pad_x, by), txt, fnt, (255, 255, 255), alpha=alpha, shadow=False)
            else:
                draw_txt(d, (bx, by), txt, fnt, col, alpha=alpha, shadow=True)
                if mode == "underline" and p > 0.35:
                    up = clamp((p - 0.35) / 0.65)
                    uy = by + h + 16
                    d.rounded_rectangle([bx, uy, bx + int(w * up), uy + 10], radius=5, fill=col + (alpha,))

            cur_x += w + pad_x * 2 + 18
            word_idx += 1
    canvas.alpha_composite(layer)

def draw_live_captions(canvas, text, local_t, sc_dur):
    words = text.split()
    if not words:
        return
    chunk_size = 4
    total_chunks = math.ceil(len(words) / chunk_size)
    chunk_idx = min(total_chunks - 1, int((local_t / max(0.1, sc_dur)) * total_chunks))
    chunk = words[chunk_idx * chunk_size : (chunk_idx + 1) * chunk_size]

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    chunk_dur = sc_dur / max(1, total_chunks)
    chunk_local = local_t - chunk_idx * chunk_dur
    active_w_idx = min(len(chunk) - 1, int((chunk_local / max(0.05, chunk_dur)) * len(chunk)))

    word_boxes = []
    tot_w = 0
    for idx, w in enumerate(chunk):
        bbox = d.textbbox((0, 0), w, font=f_md)
        ww = bbox[2] - bbox[0]
        word_boxes.append((w, ww))
        tot_w += ww + 22
    tot_w -= 22

    pad_bx = 38
    bx1 = max(60, (W - tot_w) // 2 - pad_bx)
    bx2 = min(W - 60, (W + tot_w) // 2 + pad_bx)
    by1, by2 = 1465, 1555
    d.rounded_rectangle([bx1, by1, bx2, by2], radius=34, fill=(10, 12, 20, 215), outline=T["primary"] + (180,), width=3)

    cx = (W - tot_w) // 2
    for idx, (w, ww) in enumerate(word_boxes):
        is_active = (idx == active_w_idx)
        col = T["secondary"] if is_active else (255, 255, 255)
        y_off = -4 if is_active else 0
        d.text((int(cx), int(1485 + y_off)), w, font=f_md, fill=col + (255,))
        cx += ww + 22

    canvas.alpha_composite(layer)

def draw_audio_equalizer(canvas, t):
    d = ImageDraw.Draw(canvas)
    start_x = 890
    base_y = 85
    for i in range(7):
        h = int(14 + 26 * abs(math.sin(t * 11 + i * 1.1)))
        d.rounded_rectangle([start_x + i * 16, base_y - h // 2, start_x + i * 16 + 9, base_y + h // 2], radius=4, fill=T["primary"] + (230,))

total_dur = timeline["total_duration"]
scenes = timeline["scenes"]
total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s)...")

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
    frame_img = base_bg.copy()
    d = ImageDraw.Draw(frame_img)

    prog_w = int((t / total_dur) * W)
    d.rectangle([0, 0, W, 14], fill=CARD_BORDER + (200,))
    d.rectangle([0, 0, prog_w, 14], fill=T["primary"] + (255,))

    d.ellipse([65, 73, 85, 93], fill=T["primary"] + (255,))
    d.text((100, 67), "VIRAL INSIGHTS", font=f_xs, fill=MUTED_TXT + (220,))
    draw_audio_equalizer(frame_img, t)

    active_sc = scenes[-1]
    sc_idx = len(scenes) - 1
    for i, sc in enumerate(scenes):
        if sc["start"] <= t < sc["start"] + sc["duration"]:
            active_sc = sc
            sc_idx = i
            break

    lt = t - active_sc["start"]
    sid = active_sc["id"]
    w_type = WIDGETS.get(sid, "")

    if sid == "scene1":
        sc1 = S["scene1"]
        draw_heading(frame_img, 185, [
            [(sc1.get("h_top", "Secret"), T["dark"], f_lg, "normal"), (sc1.get("h_highlight", "Truth"), T["primary"], f_serif, "underline")],
            [(sc1.get("h_pill", "Must Watch"), T["primary"], f_md, "pill")]
        ], lt)

        if w_type == "big_stat_hook":
            p = ease_out_back(lt / 0.45)
            cy = int(510 + (1 - p) * 140)
            draw_card(frame_img, [150, cy, 930, cy + 680], radius=52, outline=T["primary"] + (255,), width=8)
            d = ImageDraw.Draw(frame_img)
            draw_center(d, cy + 55, sc1.get("card_title", "DID YOU KNOW?"), f_xs, MUTED_TXT, shadow=False)
            draw_center(d, cy + 135, sc1.get("big_number", "99%"), f_mega, T["primary"], shadow=True)
            d.rounded_rectangle([210, cy + 360, 870, cy + 465], radius=24, fill=T["tint"] + (255,))
            draw_center(d, cy + 392, sc1.get("point1", ""), f_sm, T["dark"], shadow=False)
            d.rounded_rectangle([210, cy + 500, 870, cy + 605], radius=24, fill=T["primary"] + (255,))
            draw_center(d, cy + 532, sc1.get("point2", ""), f_sm, (255, 255, 255), shadow=False)

        elif w_type == "split_question":
            p1 = ease_out_back((lt - 0.25) / 0.4)
            p2 = ease_out_back((lt - 0.8) / 0.4)
            draw_card(frame_img, [140, int(500 - (1 - p1) * 100), 940, int(800 - (1 - p1) * 100)], radius=40, outline=CARD_BORDER + (255,), width=4)
            d = ImageDraw.Draw(frame_img)
            d.text((200, 555), "01 • REALITY CHECK", font=f_xs, fill=T["primary"] + (255,))
            d.text((200, 625), sc1.get("point1", ""), font=f_md, fill=T["dark"] + (255,))

            if lt > 0.7:
                draw_card(frame_img, [140, int(860 + (1 - p2) * 120), 940, int(1190 + (1 - p2) * 120)], radius=40, fill=T["primary"], outline=T["primary"] + (255,), width=4)
                d = ImageDraw.Draw(frame_img)
                d.text((200, 920), "02 • GAME CHANGER", font=f_xs, fill=(255, 255, 255, 210))
                d.text((200, 990), sc1.get("point2", ""), font=f_md, fill=(255, 255, 255, 255))
        else:
            p = ease_out_back(lt / 0.45)
            cy = int(500 + (1 - p) * 150)
            draw_card(frame_img, [140, cy, 940, cy + 720], radius=52, outline=T["primary"] + (255,), width=8)
            d = ImageDraw.Draw(frame_img)
            d.rounded_rectangle([156, cy + 16, 924, cy + 130], radius=38, fill=T["tint"] + (255,))
            d.ellipse([195, cy + 40, 260, cy + 105], fill=T["primary"] + (255,))
            d.text((216, cy + 48), "!", font=f_sm, fill=(255, 255, 255, 255))
            d.text((285, cy + 52), sc1.get("card_title", "SECRET ALERT"), font=f_xs, fill=T["dark"] + (255,))
            if lt > 0.45:
                d.rounded_rectangle([200, cy + 195, 880, cy + 325], radius=26, fill=T["tint"] + (255,))
                d.text((240, cy + 238), sc1.get("point1", ""), font=f_sm, fill=T["dark"] + (255,))
            if lt > 1.0:
                d.rounded_rectangle([200, cy + 370, 880, cy + 520], radius=28, fill=T["primary"] + (255,))
                d.text((240, cy + 422), sc1.get("point2", ""), font=f_sm, fill=(255, 255, 255, 255))
            pulse = int(340 * (1.0 + 0.06 * math.sin(lt * 8)))
            d.rounded_rectangle([W // 2 - pulse // 2, cy + 585, W // 2 + pulse // 2, cy + 650], radius=32, fill=T["soft"] + (255,))
            draw_center(d, cy + 598, "WATCH TILL END", f_xs, T["primary"], shadow=False)

    elif sid == "scene2":
        sc2 = S["scene2"]
        draw_center(d, 380, sc2.get("sub", "99% log yeh galti karte hain..."), f_sm, MUTED_TXT, shadow=False)
        draw_center(d, 540, sc2.get("myth", "WRONG WAY?"), f_xl, T["dark"], shadow=True)

        if lt > 0.65:
            sp = ease_out_cubic((lt - 0.65) / 0.4)
            d.line([(180, 615), (180 + int(720 * sp), 615)], fill=T["secondary"] + (255,), width=18)

        if lt > 1.4:
            st = ease_out_back((lt - 1.4) / 0.25)
            sw, sh = int(720 * clamp(st)), int(310 * clamp(st))
            cx, cy = W // 2, 930
            draw_card(frame_img, [cx - sw // 2, cy - sh // 2, cx + sw // 2, cy + sh // 2], radius=40, outline=T["primary"] + (255,), width=10)
            d = ImageDraw.Draw(frame_img)
            if st > 0.7:
                draw_center(d, cy - 105, sc2.get("truth_big", "3 SECRETS"), f_xl, T["primary"], shadow=True)
                draw_center(d, cy + 42, sc2.get("truth_sub", "REAL TRUTH"), f_serif, T["dark"], shadow=False)

    elif sid == "scene3":
        sc3 = S["scene3"]
        draw_card(frame_img, [290, 175, 790, 250], radius=36, outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_center(d, 195, sc3.get("badge", "01 • 3 STEPS"), f_xs, T["primary"], shadow=False)

        draw_heading(frame_img, 300, [
            [(sc3.get("h_top", "Yeh"), T["dark"], f_lg, "normal"), (sc3.get("h_pill", "3 rules"), T["primary"], f_serif, "pill")],
            [(sc3.get("h_bottom", "follow karein"), T["dark"], f_lg, "normal")]
        ], lt)

        items = [
            (sc3.get("item1", ""), sc3.get("tag1", "#1"), CARD_BG, T["dark"], 0.25),
            (sc3.get("item2", ""), sc3.get("tag2", "#2"), T["tint"], T["dark"], 0.85),
            (sc3.get("item3", ""), sc3.get("tag3", "#3"), T["primary"], (255, 255, 255), 1.45)
        ]

        if w_type == "timeline_nodes":
            d.line([(230, 680), (230, 1180)], fill=T["primary"] + (255,), width=8)
            for idx, (label, tag, bg_c, fg_c, delay) in enumerate(items):
                if lt > delay:
                    lp = ease_out_back((lt - delay) / 0.38)
                    ly = int(620 + idx * 215)
                    d.ellipse([190, ly + 35, 270, ly + 115], fill=T["primary"] + (255,))
                    d.text((212, ly + 55), tag, font=f_xs, fill=(255, 255, 255, 255))
                    ox = int(310 + (1 - lp) * 120)
                    draw_card(frame_img, [ox, ly, ox + 630, ly + 150], radius=30, fill=bg_c, outline=T["primary"] + (255,), width=4)
                    d = ImageDraw.Draw(frame_img)
                    d.text((ox + 40, ly + 52), label, font=f_sm, fill=fg_c + (255,))
        else:
            for idx, (label, tag, bg_c, fg_c, delay) in enumerate(items):
                if lt > delay:
                    lp = ease_out_back((lt - delay) / 0.38)
                    ly = int(630 + idx * 205 - (1 - lp) * 85)
                    draw_card(frame_img, [140, ly, 940, ly + 155], radius=32, fill=bg_c, outline=T["primary"] + (255,), width=4)
                    d = ImageDraw.Draw(frame_img)
                    d.text((195, ly + 54), label, font=f_sm, fill=fg_c + (255,))
                    d.text((800, ly + 54), tag, font=f_sm, fill=fg_c + (255,))

    elif sid == "scene4":
        sc4 = S["scene4"]
        draw_card(frame_img, [290, 175, 790, 250], radius=36, outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_center(d, 195, sc4.get("badge", "02 • IMPACT"), f_xs, T["primary"], shadow=False)

        draw_heading(frame_img, 300, [
            [(sc4.get("h_top", "Purana nahi,"), T["dark"], f_lg, "normal")],
            [(sc4.get("h_pill", "Smart Trick"), T["primary"], f_serif, "pill"), (sc4.get("h_tail", "lagao"), T["dark"], f_lg, "normal")]
        ], lt)

        draw_card(frame_img, [120, 610, 960, 1260], radius=44, outline=CARD_BORDER + (255,), width=3)
        d = ImageDraw.Draw(frame_img)

        if w_type == "radial_gauge":
            pct = int(sc4.get("percent_val", 94))
            gp = ease_out_cubic((lt - 0.25) / 1.3)
            cur_pct = int(pct * gp)
            cx, cy, r = W // 2, 875, 170
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=CARD_BORDER + (255,), width=28)
            d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + int(360 * (cur_pct / 100.0)), fill=T["primary"] + (255,), width=28)
            draw_center(d, cy - 52, f"{cur_pct}%", f_xl, T["primary"], shadow=True)
            draw_center(d, cy + 55, "EFFICIENCY", f_xs, MUTED_TXT, shadow=False)
            d.rounded_rectangle([180, 1100, 900, 1195], radius=22, fill=T["tint"] + (255,))
            draw_center(d, 1128, sc4.get("footer", ""), f_xs, T["dark"], shadow=False)
        else:
            slow_p = ease_out_cubic((lt - 0.25) / 1.2)
            d.text((180, 685), sc4.get("before_label", ""), font=f_sm, fill=MUTED_TXT + (255,))
            d.rounded_rectangle([180, 750, 900, 788], radius=16, fill=CARD_BORDER + (255,))
            d.rounded_rectangle([180, 750, 180 + int(280 * slow_p), 788], radius=16, fill=MUTED_TXT + (255,))

            fast_p = ease_out_cubic((lt - 1.3) / 0.45)
            d.text((180, 875), sc4.get("after_label", ""), font=f_sm, fill=T["primary"] + (255,))
            d.rounded_rectangle([180, 940, 900, 978], radius=16, fill=CARD_BORDER + (255,))
            if fast_p > 0:
                d.rounded_rectangle([180, 940, 180 + int(720 * fast_p), 978], radius=16, fill=T["primary"] + (255,))

            d.rounded_rectangle([180, 1070, 900, 1170], radius=22, fill=T["tint"] + (255,))
            draw_center(d, 1102, sc4.get("footer", ""), f_xs, T["dark"], shadow=False)

    elif sid == "scene5":
        sc5 = S["scene5"]
        draw_card(frame_img, [290, 175, 790, 250], radius=36, outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_center(d, 195, sc5.get("badge", "03 • PROOF"), f_xs, T["primary"], shadow=False)

        draw_heading(frame_img, 300, [
            [(sc5.get("h_top", "Har jagah"), T["dark"], f_lg, "normal"), (sc5.get("h_highlight", "instant result"), T["primary"], f_serif, "underline")],
            [(sc5.get("h_bottom", "dikhna shuru"), T["dark"], f_lg, "normal")]
        ], lt)

        draw_card(frame_img, [120, 610, 960, 1290], radius=44, outline=CARD_BORDER + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        d.text((180, 665), sc5.get("metric_title", "SUCCESS"), font=f_xs, fill=MUTED_TXT + (255,))
        d.text((710, 660), sc5.get("metric_val", "98%"), font=f_sm, fill=(16, 185, 129, 255))

        rows = [
            (sc5.get("row1_left", ""), sc5.get("row1_right", "Done"), 0.3),
            (sc5.get("row2_left", ""), sc5.get("row2_right", "Done"), 0.85),
            (sc5.get("row3_left", ""), sc5.get("row3_right", "Done"), 1.4)
        ]
        for idx, (o_name, o_amt, delay) in enumerate(rows):
            if lt > delay:
                op = ease_out_back((lt - delay) / 0.35)
                oy = 760 + idx * 160
                ox = int(170 - (1 - op) * 80)
                d.rounded_rectangle([ox, oy, ox + 740, oy + 120], radius=24, fill=T["tint"] + (255,))
                d.text((ox + 35, oy + 42), o_name, font=f_xs, fill=T["dark"] + (255,))
                d.rounded_rectangle([ox + 490, oy + 30, ox + 710, oy + 90], radius=28, fill=(16, 185, 129, 255))
                d.text((ox + 530, oy + 44), o_amt, font=f_xs, fill=(255, 255, 255, 255))

    elif sid == "scene6":
        sc6 = S["scene6"]
        draw_heading(frame_img, 195, [
            [(sc6.get("h_top", "Aapko bhi chahiye"), T["dark"], f_lg, "normal")],
            [(sc6.get("h_pill", "Part 2"), T["primary"], f_serif, "pill"), (sc6.get("h_tail", "secrets?"), T["dark"], f_lg, "normal")]
        ], lt)

        draw_card(frame_img, [140, 510, 940, 960], radius=44, outline=CARD_BORDER + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_center(d, 565, sc6.get("stat_title", "RESULT"), f_xs, MUTED_TXT, shadow=False)
        draw_center(d, 645, sc6.get("stat_big", "10X FAST"), f_xl, T["primary"], shadow=True)
        d.rounded_rectangle([250, 820, 830, 890], radius=34, fill=T["tint"] + (255,))
        draw_center(d, 838, sc6.get("stat_pill", "Save & Share"), f_xs, T["primary"], shadow=False)

        draw_card(frame_img, [160, 1060, 920, 1185], radius=64, outline=T["primary"] + (255,), width=4)
        d = ImageDraw.Draw(frame_img)
        kw = sc6.get("keyword", "PART2")
        typed = ""
        if lt > 1.9:
            chars = int(clamp((lt - 1.9) / 0.5) * len(kw)) + 1
            typed = kw[:chars]
        d.text((230, 1095), typed, font=f_md, fill=T["dark"] + (255,))
        d.ellipse([810, 1082, 890, 1162], fill=T["primary"] + (255,))
        d.text((836, 1097), ">", font=f_sm, fill=(255, 255, 255, 255))

        draw_center(d, 1255, sc6.get("cta_text", f"Comment karo [ {kw} ]"), f_md, T["dark"], shadow=True)

    sc_voice = S.get(sid, {}).get("voice", "")
    draw_live_captions(frame_img, sc_voice, lt, active_sc["duration"])

    rem = (active_sc["start"] + active_sc["duration"]) - t
    if sc_idx < len(scenes) - 1 and rem < 0.30:
        wp = clamp((0.30 - rem) / 0.30)
        if TRANSITION == "curtain_h":
            bar_h = H // 6
            for b in range(6):
                bw = int(W * wp)
                if b % 2 == 0:
                    d.rectangle([0, b * bar_h, bw, (b + 1) * bar_h], fill=T["primary"] + (255,))
                else:
                    d.rectangle([W - bw, b * bar_h, W, (b + 1) * bar_h], fill=T["secondary"] + (255,))
        elif TRANSITION == "iris_zoom":
            rad = int(1250 * wp)
            d.ellipse([W // 2 - rad, H // 2 - rad, W // 2 + rad, H // 2 + rad], fill=T["primary"] + (255,))
        else:
            bar_w = W // 5
            for b in range(5):
                bh = int(H * wp)
                if b % 2 == 0:
                    d.rectangle([b * bar_w, 0, (b + 1) * bar_w, bh], fill=T["primary"] + (255,))
                else:
                    d.rectangle([b * bar_w, H - bh, (b + 1) * bar_w, H], fill=T["secondary"] + (255,))

    ffmpeg.stdin.write(frame_img.tobytes())
    if frame % 300 == 0:
        print(f"Rendered {frame}/{total_frames} frames...")

ffmpeg.stdin.close()
ffmpeg.wait()
print("100% DONE! Broadcast-Grade Viral Reel created successfully.")
