import json
import math
import os
import subprocess
import sys
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

theme_name = sys.argv[1] if len(sys.argv) > 1 else "royal_indigo"

THEMES = {
    "royal_indigo": {
        "primary": (37, 99, 235),
        "dark": (15, 23, 42),
        "soft": (219, 234, 254),
        "tint": (239, 246, 255),
        "accent": (239, 68, 68),
        "bg": (248, 250, 252),
        "grid": (222, 230, 240)
    },
    "emerald_tech": {
        "primary": (5, 150, 105),
        "dark": (6, 78, 59),
        "soft": (209, 250, 229),
        "tint": (236, 253, 245),
        "accent": (225, 29, 72),
        "bg": (248, 250, 252),
        "grid": (205, 238, 222)
    },
    "midnight_gold": {
        "primary": (79, 70, 229),
        "dark": (30, 27, 75),
        "soft": (224, 231, 255),
        "tint": (238, 242, 255),
        "accent": (234, 88, 12),
        "bg": (250, 250, 252),
        "grid": (220, 225, 245)
    }
}

T = THEMES.get(theme_name, THEMES["royal_indigo"])
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
            print("Font download fallback:", e)

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
f_lg = load_font("fonts/Poppins-ExtraBold.ttf", "", 66)
f_serif = load_font("fonts/Playfair-BoldItalic.ttf", "fonts/Poppins-ExtraBold.ttf", 72)
f_xl = load_font("fonts/Poppins-ExtraBold.ttf", "", 104)

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
bg_draw = ImageDraw.Draw(base_bg)
for x in range(0, W, 64):
    bg_draw.line([(x, 0), (x, H)], fill=T["grid"] + (165,), width=2)
for y in range(0, H, 64):
    bg_draw.line([(0, y), (W, y)], fill=T["grid"] + (165,), width=2)

glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([140, -180, 940, 620], fill=T["soft"] + (140,))
glow = glow.filter(ImageFilter.GaussianBlur(95))
base_bg.alpha_composite(glow)

def draw_shadow_card(canvas, box, radius=40, fill=(255, 255, 255), outline=None, width=0):
    x1, y1, x2, y2 = [int(v) for v in box]
    if x2 <= x1 or y2 <= y1:
        return
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x1, y1 + 20, x2, y2 + 20], radius=radius, fill=(15, 23, 42, 42))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.alpha_composite(shadow)

    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill + (255,), outline=outline, width=width)

def draw_styled_text(draw, pos, text, font, fill, alpha=255, shadow=True):
    x, y = int(pos[0]), int(pos[1])
    if shadow:
        draw.text((x, y + 5), text, font=font, fill=(15, 23, 42, int(alpha * 0.16)))
    draw.text((x, y), text, font=font, fill=fill + (int(alpha),))

def draw_centered_text(draw, y, text, font, fill, alpha=255, shadow=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw_styled_text(draw, (x, y), text, font, fill, alpha=alpha, shadow=shadow)

def draw_kinetic_heading(canvas, y_start, lines, local_t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    word_idx = 0
    for line_idx, segments in enumerate(lines):
        total_w = 0
        rendered_segs = []
        for seg in segments:
            txt, col, fnt = seg[0], seg[1], seg[2]
            mode = seg[3] if len(seg) > 3 else "normal"
            bbox = d.textbbox((0, 0), txt, font=fnt)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            pad_x = 26 if mode == "pill" else 0
            rendered_segs.append((txt, col, fnt, mode, w, h, pad_x))
            total_w += w + pad_x * 2 + 18
        total_w -= 18
        cur_x = (W - total_w) // 2

        for txt, col, fnt, mode, w, h, pad_x in rendered_segs:
            p = ease_out_back((local_t - word_idx * 0.08) / 0.36)
            dy = (1.0 - p) * 40
            alpha = int(clamp(p) * 255)
            bx = int(cur_x)
            by = int(y_start + line_idx * 96 + dy)

            if mode == "pill" and alpha > 20:
                d.rounded_rectangle([bx, by - 6, bx + w + pad_x * 2, by + h + 22], radius=24, fill=col + (alpha,))
                draw_styled_text(d, (bx + pad_x, by), txt, fnt, (255, 255, 255), alpha=alpha, shadow=False)
            else:
                draw_styled_text(d, (bx, by), txt, fnt, col, alpha=alpha, shadow=True)
                if mode == "underline" and p > 0.35:
                    up = clamp((p - 0.35) / 0.65)
                    uy = by + h + 16
                    d.rounded_rectangle([bx, uy, bx + int(w * up), uy + 10], radius=5, fill=col + (alpha,))

            cur_x += w + pad_x * 2 + 18
            word_idx += 1
    canvas.alpha_composite(layer)

with open("timeline.json") as f:
    timeline = json.load(f)

with open("script_data.json") as f:
    S = json.load(f)

total_dur = timeline["total_duration"]
scenes = timeline["scenes"]
total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s)...")

ffmpeg = subprocess.Popen([
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{W}x{H}",
    "-pix_fmt", "rgba",
    "-r", str(FPS),
    "-i", "-",
    "-i", "final_audio.m4a",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "19",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    "final_reel.mp4"
], stdin=subprocess.PIPE)

for frame in range(total_frames):
    t = frame / FPS
    frame_img = base_bg.copy()
    d = ImageDraw.Draw(frame_img)

    prog_w = int((t / total_dur) * W)
    d.rectangle([0, 0, W, 14], fill=(226, 232, 240, 200))
    d.rectangle([0, 0, prog_w, 14], fill=T["primary"] + (255,))

    active_sc = scenes[-1]
    sc_idx = len(scenes) - 1
    for i, sc in enumerate(scenes):
        if sc["start"] <= t < sc["start"] + sc["duration"]:
            active_sc = sc
            sc_idx = i
            break

    lt = t - active_sc["start"]
    sid = active_sc["id"]

    if sid == "scene1":
        sc1 = S["scene1"]
        draw_kinetic_heading(frame_img, 210, [
            [(sc1["h_top"], T["dark"], f_lg, "normal"), (sc1["h_highlight"], T["primary"], f_serif, "underline")],
            [(sc1["h_pill"], T["primary"], f_md, "pill")]
        ], lt)

        p_phone = ease_out_back(lt / 0.5)
        py = int(500 + (1 - p_phone) * 180)
        draw_shadow_card(frame_img, [230, py, 850, py + 940], radius=60, fill=(255, 255, 255), outline=T["dark"] + (255,), width=12)
        d = ImageDraw.Draw(frame_img)
        d.rounded_rectangle([242, py + 12, 838, py + 130], radius=48, fill=T["tint"] + (255,))
        d.ellipse([280, py + 38, 344, py + 102], fill=T["primary"] + (255,))
        d.text((302, py + 48), sc1["sender"][0].upper(), font=f_sm, fill=(255, 255, 255, 255))
        d.text((365, py + 48), sc1["sender"], font=f_xs, fill=T["dark"] + (255,))

        if lt > 0.6:
            b1 = ease_out_back((lt - 0.6) / 0.35)
            d.rounded_rectangle([280, py + 220, 280 + int(470 * clamp(b1)), py + 320], radius=26, fill=(241, 245, 249, 255))
            if b1 > 0.6:
                d.text((310, py + 252), sc1["msg1"], font=f_xs, fill=T["dark"] + (255,))

        if lt > 1.4:
            b2 = ease_out_back((lt - 1.4) / 0.35)
            d.rounded_rectangle([280, py + 360, 280 + int(520 * clamp(b2)), py + 520], radius=26, fill=T["primary"] + (255,))
            if b2 > 0.6:
                d.text((310, py + 395), sc1["msg2_line1"], font=f_xs, fill=(255, 255, 255, 255))
                d.text((310, py + 448), sc1["msg2_line2"], font=f_xs, fill=(255, 255, 255, 255))

        if lt > 2.1:
            ba = ease_out_back((lt - 2.1) / 0.3)
            r = int(58 * clamp(ba))
            d.ellipse([830 - r, py + 150 - r, 830 + r, py + 150 + r], fill=T["accent"] + (255,))
            if ba > 0.7:
                d.text((805, py + 122), "?!", font=f_md, fill=(255, 255, 255, 255))

    elif sid == "scene2":
        sc2 = S["scene2"]
        draw_centered_text(d, 440, sc2["sub"], f_sm, (71, 85, 105), shadow=False)
        draw_centered_text(d, 610, sc2["myth"], f_xl, T["dark"], shadow=True)

        if lt > 0.8:
            sp = ease_out_cubic((lt - 0.8) / 0.45)
            d.line([(200, 685), (200 + int(680 * sp), 685)], fill=T["accent"] + (255,), width=18)

        if lt > 1.8:
            st = ease_out_back((lt - 1.8) / 0.25)
            sw, sh = int(700 * clamp(st)), int(300 * clamp(st))
            cx, cy = W // 2, 980
            draw_shadow_card(frame_img, [cx - sw // 2, cy - sh // 2, cx + sw // 2, cy + sh // 2], radius=38, fill=(255, 255, 255), outline=T["primary"] + (255,), width=10)
            d = ImageDraw.Draw(frame_img)
            if st > 0.7:
                draw_centered_text(d, cy - 105, sc2["truth_big"], f_xl, T["primary"], shadow=True)
                draw_centered_text(d, cy + 40, sc2["truth_sub"], f_serif, T["dark"], shadow=False)

    elif sid == "scene3":
        sc3 = S["scene3"]
        draw_shadow_card(frame_img, [290, 210, 790, 285], radius=36, fill=(255, 255, 255), outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 230, sc3["badge"], f_xs, T["primary"], shadow=False)

        draw_kinetic_heading(frame_img, 340, [
            [(sc3["h_top"], T["dark"], f_lg, "normal"), (sc3["h_pill"], T["primary"], f_serif, "pill")],
            [(sc3["h_bottom"], T["dark"], f_lg, "normal")]
        ], lt)

        layers = [
            (sc3["layer1"], sc3["tag1"], (255, 255, 255), T["dark"], 0.35),
            (sc3["layer2"], sc3["tag2"], T["soft"], T["dark"], 1.05),
            (sc3["layer3"], sc3["tag3"], T["primary"], (255, 255, 255), 1.75)
        ]
        for idx, (label, tag, bg_c, fg_c, delay) in enumerate(layers):
            if lt > delay:
                lp = ease_out_back((lt - delay) / 0.4)
                ly = int(680 + idx * 210 - (1 - lp) * 90)
                draw_shadow_card(frame_img, [140, ly, 940, ly + 160], radius=32, fill=bg_c, outline=T["primary"] + (255,), width=4)
                d = ImageDraw.Draw(frame_img)
                d.text((195, ly + 56), label, font=f_sm, fill=fg_c + (255,))
                d.text((785, ly + 56), tag, font=f_sm, fill=fg_c + (255,))

    elif sid == "scene4":
        sc4 = S["scene4"]
        draw_shadow_card(frame_img, [290, 210, 790, 285], radius=36, fill=(255, 255, 255), outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 230, sc4["badge"], f_xs, T["primary"], shadow=False)

        draw_kinetic_heading(frame_img, 340, [
            [(sc4["h_top"], T["dark"], f_lg, "normal")],
            [(sc4["h_pill"], T["primary"], f_serif, "pill"), (sc4["h_tail"], T["dark"], f_lg, "normal")]
        ], lt)

        draw_shadow_card(frame_img, [120, 650, 960, 1280], radius=44, fill=(255, 255, 255), outline=(226, 232, 240, 255), width=3)
        d = ImageDraw.Draw(frame_img)

        slow_p = ease_out_cubic((lt - 0.3) / 1.6)
        d.text((180, 730), sc4["slow_label"], font=f_sm, fill=(100, 116, 139, 255))
        d.rounded_rectangle([180, 795, 900, 830], radius=16, fill=(226, 232, 240, 255))
        d.rounded_rectangle([180, 795, 180 + int(620 * slow_p), 830], radius=16, fill=(148, 163, 184, 255))

        fast_p = ease_out_cubic((lt - 1.7) / 0.45)
        d.text((180, 920), sc4["fast_label"], font=f_sm, fill=T["primary"] + (255,))
        d.rounded_rectangle([180, 985, 900, 1020], radius=16, fill=(226, 232, 240, 255))
        if fast_p > 0:
            d.rounded_rectangle([180, 985, 180 + int(720 * fast_p), 1020], radius=16, fill=T["primary"] + (255,))

        d.rounded_rectangle([180, 1100, 900, 1200], radius=22, fill=T["tint"] + (255,))
        draw_centered_text(d, 1132, sc4["footer"], f_xs, T["dark"], shadow=False)

    elif sid == "scene5":
        sc5 = S["scene5"]
        draw_shadow_card(frame_img, [290, 210, 790, 285], radius=36, fill=(255, 255, 255), outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 230, sc5["badge"], f_xs, T["primary"], shadow=False)

        draw_kinetic_heading(frame_img, 340, [
            [(sc5["h_top"], T["dark"], f_lg, "normal"), (sc5["h_highlight"], T["primary"], f_serif, "underline")],
            [(sc5["h_bottom"], T["dark"], f_lg, "normal")]
        ], lt)

        draw_shadow_card(frame_img, [120, 640, 960, 1340], radius=44, fill=(255, 255, 255), outline=(226, 232, 240, 255), width=3)
        d = ImageDraw.Draw(frame_img)
        d.text((180, 700), sc5["metric_title"], font=f_xs, fill=(100, 116, 139, 255))
        d.text((700, 695), sc5["metric_val"], font=f_sm, fill=(16, 185, 129, 255))

        orders = [
            (sc5["row1_left"], sc5["row1_right"], 0.45),
            (sc5["row2_left"], sc5["row2_right"], 1.2),
            (sc5["row3_left"], sc5["row3_right"], 1.95)
        ]
        for idx, (o_name, o_amt, delay) in enumerate(orders):
            if lt > delay:
                op = ease_out_back((lt - delay) / 0.38)
                oy = 800 + idx * 165
                ox = int(170 - (1 - op) * 80)
                d.rounded_rectangle([ox, oy, ox + 740, oy + 125], radius=24, fill=T["tint"] + (255,))
                d.text((ox + 35, oy + 44), o_name, font=f_xs, fill=T["dark"] + (255,))
                d.rounded_rectangle([ox + 480, oy + 32, ox + 710, oy + 92], radius=28, fill=(16, 185, 129, 255))
                d.text((ox + 515, oy + 46), o_amt, font=f_xs, fill=(255, 255, 255, 255))

    elif sid == "scene6":
        sc6 = S["scene6"]
        draw_kinetic_heading(frame_img, 230, [
            [(sc6["h_top"], T["dark"], f_lg, "normal")],
            [(sc6["h_pill"], T["primary"], f_serif, "pill"), (sc6["h_tail"], T["dark"], f_lg, "normal")]
        ], lt)

        draw_shadow_card(frame_img, [140, 560, 940, 1020], radius=44, fill=(255, 255, 255), outline=(226, 232, 240, 255), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 620, sc6["stat_title"], f_xs, (100, 116, 139), shadow=False)
        draw_centered_text(d, 705, sc6["stat_big"], f_xl, T["primary"], shadow=True)
        d.rounded_rectangle([250, 880, 830, 950], radius=34, fill=(236, 253, 245, 255))
        draw_centered_text(d, 898, sc6["stat_pill"], f_xs, (5, 150, 105), shadow=False)

        draw_shadow_card(frame_img, [160, 1140, 920, 1270], radius=64, fill=(255, 255, 255), outline=T["soft"] + (255,), width=4)
        d = ImageDraw.Draw(frame_img)
        kw = sc6["keyword"]
        typed = ""
        if lt > 2.7:
            chars = int(clamp((lt - 2.7) / 0.6) * len(kw)) + 1
            typed = kw[:chars]
        d.text((230, 1175), typed, font=f_md, fill=T["dark"] + (255,))
        d.ellipse([810, 1165, 890, 1245], fill=T["primary"] + (255,))
        d.text((836, 1180), ">", font=f_sm, fill=(255, 255, 255, 255))

        draw_centered_text(d, 1345, sc6["cta_text"], f_md, T["dark"], shadow=True)

    rem = (active_sc["start"] + active_sc["duration"]) - t
    if sc_idx < len(scenes) - 1 and rem < 0.35:
        wp = clamp((0.35 - rem) / 0.35)
        bar_w = W // 5
        for b in range(5):
            bh = int(H * wp)
            if b % 2 == 0:
                d.rectangle([b * bar_w, 0, (b + 1) * bar_w, bh], fill=T["primary"] + (255,))
            else:
                d.rectangle([b * bar_w, H - bh, (b + 1) * bar_w, H], fill=T["dark"] + (255,))

    ffmpeg.stdin.write(frame_img.tobytes())
    if frame % 300 == 0:
        print(f"Rendered {frame}/{total_frames} frames...")

ffmpeg.stdin.close()
ffmpeg.wait()
print("100% DONE! Auto-Topic Stylish Reel created successfully.")
