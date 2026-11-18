import json
import math
import os
import subprocess
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

theme_name = sys.argv[1] if len(sys.argv) > 1 else "royal_indigo"

THEMES = {
    "royal_indigo": {
        "primary": (29, 78, 216),
        "dark": (30, 58, 138),
        "soft": (219, 234, 254),
        "tint": (239, 246, 255),
        "accent": (220, 38, 38),
        "bg": (248, 250, 252),
        "grid": (215, 223, 234)
    },
    "emerald_tech": {
        "primary": (5, 150, 105),
        "dark": (6, 78, 59),
        "soft": (209, 250, 229),
        "tint": (236, 253, 245),
        "accent": (225, 29, 72),
        "bg": (248, 250, 252),
        "grid": (195, 235, 215)
    },
    "midnight_gold": {
        "primary": (79, 70, 229),
        "dark": (30, 27, 75),
        "soft": (224, 231, 255),
        "tint": (238, 242, 255),
        "accent": (234, 88, 12),
        "bg": (250, 250, 250),
        "grid": (215, 220, 245)
    }
}

T = THEMES.get(theme_name, THEMES["royal_indigo"])
W, H = 1080, 1920
FPS = 30

FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, int(size))
    except:
        return ImageFont.load_default()

f_xs = get_font(FONT_BOLD, 28)
f_sm = get_font(FONT_BOLD, 34)
f_md = get_font(FONT_BOLD, 44)
f_lg = get_font(FONT_BOLD, 66)
f_xl = get_font(FONT_BOLD, 104)
f_reg = get_font(FONT_REG, 32)

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
    bg_draw.line([(x, 0), (x, H)], fill=T["grid"] + (180,), width=2)
for y in range(0, H, 64):
    bg_draw.line([(0, y), (W, y)], fill=T["grid"] + (180,), width=2)

def draw_shadow_card(canvas, box, radius=40, fill=(255, 255, 255), outline=None, width=0):
    x1, y1, x2, y2 = [int(v) for v in box]
    if x2 <= x1 or y2 <= y1:
        return
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([x1, y1 + 18, x2, y2 + 18], radius=radius, fill=(15, 23, 42, 38))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow)

    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill + (255,), outline=outline, width=width)

def draw_centered_text(draw, y, text, font, fill, alpha=255):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x, int(y)), text, font=font, fill=fill + (int(alpha),))

def draw_kinetic_heading(canvas, y_start, lines, local_t):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    word_idx = 0
    for line_idx, segments in enumerate(lines):
        total_w = 0
        rendered_segs = []
        for txt, col, fnt in segments:
            bbox = d.textbbox((0, 0), txt, font=fnt)
            w = bbox[2] - bbox[0]
            rendered_segs.append((txt, col, fnt, w))
            total_w += w + 16
        cur_x = (W - total_w) // 2
        for txt, col, fnt, w in rendered_segs:
            p = ease_out_back((local_t - word_idx * 0.08) / 0.38)
            dy = (1.0 - p) * 35
            alpha = int(clamp(p) * 255)
            d.text((int(cur_x), int(y_start + line_idx * 84 + dy)), txt, font=fnt, fill=col + (alpha,))
            cur_x += w + 16
            word_idx += 1
    canvas.alpha_composite(layer)

with open("timeline.json") as f:
    timeline = json.load(f)

total_dur = timeline["total_duration"]
scenes = timeline["scenes"]
total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) directly via Python + FFmpeg...")

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
        draw_kinetic_heading(frame_img, 240, [
            [("Ek client ka", (15, 23, 42), f_lg), ("message", T["primary"], f_lg)],
            [("24/7 AI Support App", T["primary"], f_lg)]
        ], lt)

        p_phone = ease_out_back(lt / 0.55)
        py = int(520 + (1 - p_phone) * 180)
        draw_shadow_card(frame_img, [230, py, 850, py + 940], radius=60, fill=(255, 255, 255), outline=T["dark"] + (255,), width=12)
        d = ImageDraw.Draw(frame_img)
        d.rounded_rectangle([242, py + 12, 838, py + 130], radius=48, fill=T["tint"] + (255,))
        d.ellipse([280, py + 38, 344, py + 102], fill=T["primary"] + (255,))
        d.text((302, py + 50), "R", font=f_sm, fill=(255, 255, 255, 255))
        d.text((365, py + 45), "Rahul (Client)  • Online", font=f_xs, fill=(15, 23, 42, 255))

        if lt > 0.7:
            b1 = ease_out_back((lt - 0.7) / 0.35)
            d.rounded_rectangle([280, py + 220, 280 + int(460 * clamp(b1)), py + 320], radius=26, fill=(241, 245, 249, 255))
            if b1 > 0.6:
                d.text((310, py + 250), "Hi! Urgent project hai", font=f_xs, fill=(15, 23, 42, 255))

        if lt > 1.7:
            b2 = ease_out_back((lt - 1.7) / 0.35)
            d.rounded_rectangle([280, py + 360, 280 + int(510 * clamp(b2)), py + 520], radius=26, fill=T["primary"] + (255,))
            if b2 > 0.6:
                d.text((310, py + 395), "WhatsApp & Insta pe 24/7", font=f_xs, fill=(255, 255, 255, 255))
                d.text((310, py + 445), "AI reply system chahiye!", font=f_xs, fill=(255, 255, 255, 255))

        if lt > 2.5:
            ba = ease_out_back((lt - 2.5) / 0.3)
            r = int(58 * clamp(ba))
            d.ellipse([830 - r, py + 150 - r, 830 + r, py + 150 + r], fill=T["accent"] + (255,))
            if ba > 0.7:
                d.text((805, py + 122), "?!", font=f_md, fill=(255, 255, 255, 255))

    elif sid == "scene2":
        draw_centered_text(d, 460, "Pehli baar suno toh lagta hai...", f_md, (71, 85, 105))
        draw_centered_text(d, 640, "MUSHKIL?", f_xl, (15, 23, 42))

        if lt > 0.9:
            sp = ease_out_cubic((lt - 0.9) / 0.5)
            d.line([(220, 710), (220 + int(640 * sp), 710)], fill=T["accent"] + (255,), width=16)

        if lt > 2.1:
            st = ease_out_back((lt - 2.1) / 0.25)
            sw, sh = int(680 * clamp(st)), int(280 * clamp(st))
            cx, cy = W // 2, 980
            draw_shadow_card(frame_img, [cx - sw // 2, cy - sh // 2, cx + sw // 2, cy + sh // 2], radius=34, fill=(255, 255, 255), outline=T["primary"] + (255,), width=10)
            d = ImageDraw.Draw(frame_img)
            if st > 0.7:
                draw_centered_text(d, cy - 95, "100%", f_xl, T["primary"])
                draw_centered_text(d, cy + 35, "POSSIBLE", f_md, (15, 23, 42))

    elif sid == "scene3":
        draw_shadow_card(frame_img, [290, 220, 790, 295], radius=36, fill=(255, 255, 255), outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 238, "01 • 3 SMART LAYERS", f_xs, T["primary"])

        draw_kinetic_heading(frame_img, 360, [
            [("Hum ise", (15, 23, 42), f_lg), ("3 layers", T["primary"], f_lg)],
            [("mein banate hain", (15, 23, 42), f_lg)]
        ], lt)

        layers = [
            ("01 • WhatsApp & Insta API", "LIVE", (255, 255, 255), (15, 23, 42), 0.4),
            ("02 • Custom AI Brain", "24/7", T["soft"], T["dark"], 1.2),
            ("03 • Auto Booking & Pay", "100%", T["primary"], (255, 255, 255), 2.0)
        ]
        for idx, (label, tag, bg_c, fg_c, delay) in enumerate(layers):
            if lt > delay:
                lp = ease_out_back((lt - delay) / 0.45)
                ly = int(680 + idx * 210 - (1 - lp) * 90)
                draw_shadow_card(frame_img, [150, ly, 930, ly + 160], radius=32, fill=bg_c, outline=T["primary"] + (255,), width=4)
                d = ImageDraw.Draw(frame_img)
                d.text((200, ly + 55), label, font=f_sm, fill=fg_c + (255,))
                d.text((780, ly + 55), tag, font=f_sm, fill=fg_c + (255,))

    elif sid == "scene4":
        draw_shadow_card(frame_img, [290, 220, 790, 295], radius=36, fill=(255, 255, 255), outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 238, "02 • LAYER 02 • AI BRAIN", f_xs, T["primary"])

        draw_kinetic_heading(frame_img, 360, [
            [("Human team nahi,", (15, 23, 42), f_lg)],
            [("AI Brain", T["primary"], f_lg), ("se turant", (15, 23, 42), f_lg)]
        ], lt)

        draw_shadow_card(frame_img, [120, 650, 960, 1280], radius=44, fill=(255, 255, 255), outline=(226, 232, 240, 255), width=3)
        d = ImageDraw.Draw(frame_img)

        slow_p = ease_out_cubic((lt - 0.4) / 2.0)
        d.text((180, 730), f"Manual Support Reply:  {int(slow_p * 45)} min", font=f_sm, fill=(100, 116, 139, 255))
        d.rounded_rectangle([180, 795, 900, 830], radius=16, fill=(226, 232, 240, 255))
        d.rounded_rectangle([180, 795, 180 + int(620 * slow_p), 830], radius=16, fill=(148, 163, 184, 255))

        fast_p = ease_out_cubic((lt - 2.2) / 0.45)
        speed_txt = "0.8 sec FAST" if fast_p > 0.8 else "0.0 sec"
        d.text((180, 920), f"AI Knowledge Base:  {speed_txt}", font=f_sm, fill=T["primary"] + (255,))
        d.rounded_rectangle([180, 985, 900, 1020], radius=16, fill=(226, 232, 240, 255))
        if fast_p > 0:
            d.rounded_rectangle([180, 985, 180 + int(720 * fast_p), 1020], radius=16, fill=T["primary"] + (255,))

        d.rounded_rectangle([180, 1100, 900, 1200], radius=22, fill=T["tint"] + (255,))
        draw_centered_text(d, 1130, "Business data se 100% exact jawab", f_xs, T["dark"])

    elif sid == "scene5":
        draw_shadow_card(frame_img, [290, 220, 790, 295], radius=36, fill=(255, 255, 255), outline=T["primary"] + (255,), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 238, "03 • LAYER 03 • AUTO SALES", f_xs, T["primary"])

        draw_kinetic_heading(frame_img, 360, [
            [("Har order", (15, 23, 42), f_lg), ("chat mein", T["primary"], f_lg)],
            [("khud book hota hai", (15, 23, 42), f_lg)]
        ], lt)

        draw_shadow_card(frame_img, [120, 640, 960, 1340], radius=44, fill=(255, 255, 255), outline=(226, 232, 240, 255), width=3)
        d = ImageDraw.Draw(frame_img)
        rev = int(ease_out_cubic((lt - 0.5) / 2.2) * 9397)
        d.text((180, 700), "LIVE AI SALES", font=f_xs, fill=(100, 116, 139, 255))
        d.text((710, 695), f"Rs. {rev:,}", font=f_sm, fill=(16, 185, 129, 255))

        orders = [
            ("Order #4081 • Aman", "Paid Rs.2,499", 0.6),
            ("Order #4082 • Priya", "Paid Rs.4,999", 1.5),
            ("Order #4083 • Rohan", "Paid Rs.1,899", 2.4)
        ]
        for idx, (o_name, o_amt, delay) in enumerate(orders):
            if lt > delay:
                op = ease_out_back((lt - delay) / 0.4)
                oy = 800 + idx * 165
                ox = int(170 - (1 - op) * 80)
                d.rounded_rectangle([ox, oy, ox + 740, oy + 125], radius=24, fill=T["tint"] + (255,))
                d.text((ox + 35, oy + 42), o_name, font=f_xs, fill=(15, 23, 42, 255))
                d.rounded_rectangle([ox + 480, oy + 32, ox + 710, oy + 92], radius=28, fill=(16, 185, 129, 255))
                d.text((ox + 505, oy + 45), o_amt, font=f_xs, fill=(255, 255, 255, 255))

    elif sid == "scene6":
        draw_kinetic_heading(frame_img, 260, [
            [("Aapko bhi aisa", (15, 23, 42), f_lg)],
            [("AI System", T["primary"], f_lg), ("chahiye?", (15, 23, 42), f_lg)]
        ], lt)

        draw_shadow_card(frame_img, [140, 560, 940, 1020], radius=44, fill=(255, 255, 255), outline=(226, 232, 240, 255), width=3)
        d = ImageDraw.Draw(frame_img)
        draw_centered_text(d, 620, "MONTHLY REVENUE SAVED", f_xs, (100, 116, 139))
        saved = int(ease_out_cubic((lt - 0.3) / 1.6) * 125000)
        draw_centered_text(d, 710, f"Rs. {saved:,}", f_xl, T["primary"])
        d.rounded_rectangle([250, 880, 830, 950], radius=34, fill=(236, 253, 245, 255))
        draw_centered_text(d, 898, "24/7 Uptime • Zero Missed Leads", f_xs, (5, 150, 105))

        draw_shadow_card(frame_img, [160, 1140, 920, 1270], radius=64, fill=(255, 255, 255), outline=T["soft"] + (255,), width=4)
        d = ImageDraw.Draw(frame_img)
        typed = ""
        if lt > 3.6: typed = "A"
        if lt > 3.9: typed = "AI"
        d.text((230, 1175), typed, font=f_md, fill=(15, 23, 42, 255))
        d.ellipse([810, 1165, 890, 1245], fill=T["primary"] + (255,))
        d.text((836, 1182), ">", font=f_sm, fill=(255, 255, 255, 255))

        draw_centered_text(d, 1350, "Comment karo  [ AI ]", f_md, (15, 23, 42))

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
print("100% DONE! final_reel.mp4 created successfully.")
