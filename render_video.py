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
scenes = data["scenes"]
DNA = data.get("edit_dna", {})
PAL = DNA.get("palette", {
    "is_light": True,
    "bg": [248, 250, 253],
    "card": [255, 255, 255],
    "card_border": [208, 220, 240],
    "text_main": [15, 23, 42],
    "text_muted": [95, 112, 136],
    "accent": [37, 99, 235],
    "secondary": [245, 158, 11],
    "positive": [16, 185, 129],
    "negative": [239, 68, 68]
})

IS_LIGHT = PAL.get("is_light", True)
BG_COL = tuple(PAL.get("bg", [248, 250, 253]))
CARD_BG = tuple(PAL.get("card", [255, 255, 255]))
CARD_BORDER = tuple(PAL.get("card_border", [208, 220, 240]))
TXT_MAIN = tuple(PAL.get("text_main", [15, 23, 42]))
TXT_MUTED = tuple(PAL.get("text_muted", [95, 112, 136]))
ACCENT = tuple(PAL.get("accent", [37, 99, 235]))
SECONDARY = tuple(PAL.get("secondary", [245, 158, 11]))
POSITIVE = tuple(PAL.get("positive", [16, 185, 129]))
NEGATIVE = tuple(PAL.get("negative", [239, 68, 68]))
TRANSITION = DNA.get("transition", "shutter_bars")

W, H = 1080, 1920
FPS = 30

os.makedirs("fonts", exist_ok=True)
FONT_URLS = {
    "fonts/Poppins-ExtraBold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-ExtraBold.ttf",
    "fonts/Poppins-SemiBold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-SemiBold.ttf",
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

f_xxs = load_font("fonts/Poppins-SemiBold.ttf", 21)
f_xs = load_font("fonts/Poppins-SemiBold.ttf", 25)
f_sm = load_font("fonts/Poppins-SemiBold.ttf", 33)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", 44)
f_headline = load_font("fonts/Poppins-ExtraBold.ttf", 62)
f_big = load_font("fonts/Poppins-ExtraBold.ttf", 112)
f_gauge = load_font("fonts/Poppins-ExtraBold.ttf", 96)
f_caption = load_font("fonts/Poppins-ExtraBold.ttf", 50)
f_caption_big = load_font("fonts/Poppins-ExtraBold.ttf", 58)

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

prng = random.Random(42)
PARTICLES = [
    {
        "x": prng.randint(40, W - 40),
        "y": prng.randint(100, H - 100),
        "r": prng.randint(4, 10),
        "vx": prng.uniform(-16, 16),
        "vy": prng.uniform(-48, -18),
        "phase": prng.uniform(0, 6.28),
        "use_sec": (i % 3 == 0)
    }
    for i in range(24)
]

bg_images = []
for sc in scenes:
    im = Image.open(sc["bg_path"]).convert("RGB")
    im = im.resize((1260, 2240), Image.Resampling.LANCZOS)
    bg_images.append(im)

def get_animated_bg(sc_idx, lt, sc_dur, t_global):
    src = bg_images[sc_idx]
    prog = clamp(lt / max(0.1, sc_dur))
    punch = 0.05 * (1.0 - ease_out_cubic(lt / 0.28)) if lt < 0.28 else 0.0

    mode = sc_idx % 4
    if mode == 0:
        scale = 1.0 + 0.10 * prog + punch
        cw, ch = int(W / scale), int(H / scale)
        x1, y1 = (1260 - cw) // 2, (2240 - ch) // 2
    elif mode == 1:
        scale = 1.0 + punch
        cw, ch = int(W / scale), int(H / scale)
        x1 = int((1260 - cw) * prog)
        y1 = (2240 - ch) // 2
    elif mode == 2:
        scale = 1.10 - 0.10 * prog + punch
        cw, ch = int(W / scale), int(H / scale)
        x1, y1 = (1260 - cw) // 2, (2240 - ch) // 2
    else:
        scale = 1.0 + punch
        cw, ch = int(W / scale), int(H / scale)
        x1 = int((1260 - cw) * (1.0 - prog))
        y1 = (2240 - ch) // 2

    cropped = src.crop((x1, y1, x1 + cw, y1 + ch))
    if (cw, ch) != (W, H):
        cropped = cropped.resize((W, H), Image.Resampling.BILINEAR)
    frame = cropped.convert("RGBA")

    p_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(p_layer)
    for pt in PARTICLES:
        px = int((pt["x"] + pt["vx"] * t_global + 16 * math.sin(t_global * 1.5 + pt["phase"])) % W)
        py = int((pt["y"] + pt["vy"] * t_global) % H)
        pa = int(45 + 35 * math.sin(t_global * 3 + pt["phase"]))
        col = SECONDARY if pt["use_sec"] else ACCENT
        r = pt["r"]
        pd.ellipse([px - r, py - r, px + r, py + r], fill=col + (pa,))
    frame.alpha_composite(p_layer)
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
    draw.text((int(pos[0]), int(pos[1])), text, font=font, fill=fill + (alpha,))

def draw_center_text(draw, y, text, font, fill, alpha=255):
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    x = (W - tw) // 2
    draw_text_clean(draw, (x, y), text, font, fill, alpha=alpha)

def draw_elevated_card(canvas, box, radius=38, border_col=CARD_BORDER, border_w=3, alpha=250, shimmer_t=-1.0):
    x1, y1, x2, y2 = [int(v) for v in box]
    if x2 - x1 < 12 or y2 - y1 < 12:
        return
    safe_r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sh_col = (15, 23, 42, 34) if IS_LIGHT else (0, 0, 0, 145)
    sd.rounded_rectangle([x1, y1 + 16, x2, y2 + 16], radius=safe_r, fill=sh_col)
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    canvas.alpha_composite(shadow)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x1, y1, x2, y2], radius=safe_r, fill=CARD_BG + (alpha,), outline=border_col + (255,), width=border_w)
    if (x2 - 36) > (x1 + 36) + 6:
        ld.rounded_rectangle([x1 + 36, y1 + 2, x2 - 36, y1 + 7], radius=2, fill=ACCENT + (235,))

    if 0.0 <= shimmer_t <= 1.0:
        sx = int(x1 + (x2 - x1) * shimmer_t)
        sh_w = (255, 255, 255, 160) if IS_LIGHT else (255, 255, 255, 38)
        ld.line([(sx, y1 + 10), (max(x1 + 10, sx - 65), y2 - 10)], fill=sh_w, width=18)

    canvas.alpha_composite(layer)

def draw_center_motion_graphic(canvas, sc, lt, sc_dur):
    w_type = sc.get("widget", "radar_scanner")
    p_in = ease_out_back(lt / 0.40)
    alpha = int(clamp(p_in) * 255)
    float_y = int(7 * math.sin(lt * 3.4))
    cy_mid = 885 + float_y
    shim = (lt % 2.4) / 0.9 if (lt % 2.4) < 0.9 else -1.0
    track_c = (226, 232, 240) if IS_LIGHT else (38, 50, 74)

    if w_type == "radar_scanner":
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cx, cy = W // 2, cy_mid
        for r_idx, base_r in enumerate([165, 250, 335]):
            pulse = int(base_r + 14 * math.sin(lt * 5.5 - r_idx))
            ld.ellipse([cx - pulse, cy - pulse, cx + pulse, cy + pulse], outline=ACCENT + (155 - r_idx * 35,), width=4)
        ang = int((lt * 230) % 360)
        ld.pieslice([cx - 325, cy - 325, cx + 325, cy + 325], start=ang, end=ang + 52, fill=ACCENT + (36,))
        for k in range(4):
            oa = lt * 2.4 + k * 1.57
            ox = int(cx + 250 * math.cos(oa))
            oy = int(cy + 250 * math.sin(oa))
            ld.ellipse([ox - 13, oy - 13, ox + 13, oy + 13], fill=SECONDARY + (255,))
        canvas.alpha_composite(layer)

        draw_elevated_card(canvas, [215, cy - 140, 865, cy + 140], radius=42, border_col=ACCENT, border_w=4, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        draw_center_text(d, cy - 92, sc["metric_big"], f_big, ACCENT, alpha=alpha)
        draw_center_text(d, cy + 48, sc["metric_label"], f_xs, TXT_MUTED, alpha=alpha)

    elif w_type == "vs_clash_cards":
        p1 = ease_out_back(lt / 0.36)
        p2 = ease_out_back((lt - 0.42) / 0.36)
        off1 = int((1.0 - p1) * -460)
        off2 = int((1.0 - p2) * 460)

        draw_elevated_card(canvas, [95 + off1, 610 + float_y, 505 + off1, 1085 + float_y], radius=36, border_col=CARD_BORDER, border_w=3)
        d = ImageDraw.Draw(canvas)
        d.text((140 + off1, 658 + float_y), "X  AVOID THIS", font=f_xs, fill=NEGATIVE + (255,))
        for idx, ln in enumerate(wrap_text(d, sc["left_label"], f_md, 340)[:2]):
            draw_text_clean(d, (140 + off1, 740 + idx * 58 + float_y), ln, f_md, TXT_MAIN)
        d.rounded_rectangle([140 + off1, 955 + float_y, 460 + off1, 988 + float_y], radius=14, fill=track_c + (255,))
        if int(115 * clamp(p1)) > 8:
            d.rounded_rectangle([140 + off1, 955 + float_y, 140 + off1 + int(115 * clamp(p1)), 988 + float_y], radius=14, fill=NEGATIVE + (255,))

        if lt > 0.32:
            draw_elevated_card(canvas, [575 + off2, 610 + float_y, 985 + off2, 1085 + float_y], radius=36, border_col=ACCENT, border_w=4, shimmer_t=shim)
            d = ImageDraw.Draw(canvas)
            d.text((620 + off2, 658 + float_y), "+  SMART MOVE", font=f_xs, fill=POSITIVE + (255,))
            for idx, ln in enumerate(wrap_text(d, sc["right_label"], f_md, 340)[:2]):
                draw_text_clean(d, (620 + off2, 740 + idx * 58 + float_y), ln, f_md, TXT_MAIN)
            d.rounded_rectangle([620 + off2, 955 + float_y, 940 + off2, 988 + float_y], radius=14, fill=track_c + (255,))
            if int(320 * clamp(p2)) > 8:
                d.rounded_rectangle([620 + off2, 955 + float_y, 620 + off2 + int(320 * clamp(p2)), 988 + float_y], radius=14, fill=POSITIVE + (255,))

        if lt > 0.55:
            vp = ease_out_back((lt - 0.55) / 0.25)
            vr = max(4, int(48 * clamp(vp)))
            d.ellipse([W // 2 - vr, 848 + float_y - vr, W // 2 + vr, 848 + float_y + vr], fill=ACCENT + (255,))
            if vp > 0.7:
                bb = d.textbbox((0, 0), "VS", font=f_sm)
                d.text(((W - (bb[2] - bb[0])) // 2, 828 + float_y), "VS", font=f_sm, fill=(255, 255, 255, 255))

    elif w_type == "stock_line_graph":
        draw_elevated_card(canvas, [105, 580 + float_y, 975, 1135 + float_y], radius=40, border_col=ACCENT, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        d.text((160, 628 + float_y), f"IMPACT CURVE • {sc['metric_label']}", font=f_xs, fill=TXT_MUTED + (255,))
        d.text((735, 618 + float_y), sc["metric_big"], font=f_md, fill=POSITIVE + (255,))

        pts_raw = [(175, 1020), (315, 975), (455, 995), (595, 875), (735, 815), (890, 715)]
        pts = [(x, y + float_y) for (x, y) in pts_raw]
        gp = ease_out_cubic(lt / 1.15)
        max_seg = gp * (len(pts) - 1)
        drawn_pts = [pts[0]]
        for s_i in range(len(pts) - 1):
            if max_seg >= s_i + 1:
                drawn_pts.append(pts[s_i + 1])
            elif max_seg > s_i:
                frac = max_seg - s_i
                ix = int(pts[s_i][0] + (pts[s_i + 1][0] - pts[s_i][0]) * frac)
                iy = int(pts[s_i][1] + (pts[s_i + 1][1] - pts[s_i][1]) * frac)
                drawn_pts.append((ix, iy))

        for gy in [760, 860, 960, 1040]:
            d.line([(160, gy + float_y), (915, gy + float_y)], fill=track_c + (255,), width=2)

        if len(drawn_pts) >= 2:
            poly = drawn_pts + [(drawn_pts[-1][0], 1045 + float_y), (drawn_pts[0][0], 1045 + float_y)]
            fill_l = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(fill_l).polygon(poly, fill=ACCENT + (42,))
            canvas.alpha_composite(fill_l)
            d = ImageDraw.Draw(canvas)
            d.line(drawn_pts, fill=ACCENT + (255,), width=10)
            for px, py in drawn_pts:
                d.ellipse([px - 10, py - 10, px + 10, py + 10], fill=SECONDARY + (255,), outline=CARD_BG + (255,), width=3)
            lx, ly = drawn_pts[-1]
            halo = int(18 + 8 * math.sin(lt * 10))
            d.ellipse([lx - halo, ly - halo, lx + halo, ly + halo], outline=POSITIVE + (220,), width=4)

    elif w_type == "animated_bar_chart":
        draw_elevated_card(canvas, [105, 580 + float_y, 975, 1135 + float_y], radius=40, border_col=CARD_BORDER, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        d.text((160, 628 + float_y), f"GROWTH INDEX • {sc['metric_label']}", font=f_xs, fill=TXT_MUTED + (255,))
        d.text((735, 618 + float_y), sc["metric_big"], font=f_md, fill=ACCENT + (255,))

        heights = [0.30, 0.46, 0.64, 0.82, 1.0]
        base_y = 1050 + float_y
        for i, h_mul in enumerate(heights):
            bp = ease_out_cubic((lt - i * 0.12) / 0.50)
            bh = int(315 * h_mul * bp)
            if bh > 6:
                bx = 180 + i * 152
                col = ACCENT if i == 4 else (SECONDARY if i == 3 else track_c)
                d.rounded_rectangle([bx, base_y - bh, bx + 96, base_y], radius=min(20, bh // 2), fill=col + (255,))

    elif w_type == "circular_gauge":
        pct = sc.get("pct", 94)
        gp = ease_out_cubic(lt / 1.10)
        cur_val = int(pct * gp)
        draw_elevated_card(canvas, [155, 555 + float_y, 925, 1165 + float_y], radius=44, border_col=CARD_BORDER, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        cx, cy, r = W // 2, 855 + float_y, 205
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=track_c + (255,), width=26)
        d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + int(360 * (cur_val / 100.0)), fill=ACCENT + (255,), width=26)
        draw_center_text(d, cy - 68, f"{cur_val}%", f_gauge, TXT_MAIN)
        draw_center_text(d, cy + 48, sc["metric_label"][:14], f_xxs, ACCENT)

    elif w_type == "typing_terminal_hud":
        draw_elevated_card(canvas, [115, 595 + float_y, 965, 1115 + float_y], radius=38, border_col=ACCENT, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        for di, dc in enumerate([NEGATIVE, SECONDARY, POSITIVE]):
            d.ellipse([160 + di * 32, 635 + float_y, 178 + di * 32, 653 + float_y], fill=dc + (255,))
        d.text((280, 630 + float_y), f"AI ANALYSIS // {sc['kicker']}", font=f_xxs, fill=TXT_MUTED + (255,))
        d.line([(145, 680 + float_y), (935, 680 + float_y)], fill=CARD_BORDER + (255,), width=2)

        full_str = f"> {sc['right_label'].upper()} : {sc['metric_big']}"
        vis_chars = max(1, int(len(full_str) * clamp(lt / 0.85)))
        cursor = " |" if int(lt * 6) % 2 == 0 else ""
        d.text((160, 735 + float_y), full_str[:vis_chars] + cursor, font=f_md, fill=ACCENT + (255,))
        d.text((160, 825 + float_y), f"STATUS: {sc['metric_label']}", font=f_sm, fill=TXT_MAIN + (255,))

        d.rounded_rectangle([160, 960 + float_y, 920, 1005 + float_y], radius=18, fill=track_c + (255,))
        fill_w = int(760 * ease_out_cubic(lt / 1.2) * (sc.get("pct", 94) / 100.0))
        d.rounded_rectangle([160, 960 + float_y, 160 + max(36, fill_w), 1005 + float_y], radius=18, fill=POSITIVE + (255,))

    elif w_type == "floating_checklist":
        rows = [
            ("01", sc["left_label"], TXT_MUTED, 0.12),
            ("02", sc["right_label"], ACCENT, 0.58),
            ("03", sc["metric_label"], POSITIVE, 1.05)
        ]
        for idx, (num, label, badge_c, delay) in enumerate(rows):
            if lt > delay:
                rp = ease_out_back((lt - delay) / 0.34)
                ry = int(585 + idx * 185 + (1.0 - rp) * 55 + float_y)
                draw_elevated_card(canvas, [115, ry, 965, ry + 148], radius=32, border_col=badge_c if idx > 0 else CARD_BORDER, border_w=3)
                d = ImageDraw.Draw(canvas)
                d.rounded_rectangle([155, ry + 34, 235, ry + 114], radius=22, fill=badge_c + (255,))
                d.text((174, ry + 52), num, font=f_sm, fill=(255, 255, 255, 255))
                draw_text_clean(d, (270, ry + 50), label, f_md, TXT_MAIN)

    elif w_type == "split_duel_banner":
        draw_elevated_card(canvas, [105, 595 + float_y, 975, 830 + float_y], radius=34, border_col=NEGATIVE, border_w=3)
        d = ImageDraw.Draw(canvas)
        d.text((155, 632 + float_y), "OLD MISTAKE", font=f_xs, fill=NEGATIVE + (255,))
        draw_text_clean(d, (155, 695 + float_y), sc["left_label"], f_md, TXT_MAIN)

        if lt > 0.30:
            draw_elevated_card(canvas, [105, 880 + float_y, 975, 1130 + float_y], radius=34, border_col=POSITIVE, border_w=4, shimmer_t=shim)
            d = ImageDraw.Draw(canvas)
            d.text((155, 918 + float_y), f"WINNING SHIFT • {sc['metric_big']}", font=f_xs, fill=POSITIVE + (255,))
            draw_text_clean(d, (155, 982 + float_y), sc["right_label"], f_md, TXT_MAIN)

    elif w_type == "neon_orbit_rings":
        draw_elevated_card(canvas, [135, 575 + float_y, 945, 1145 + float_y], radius=44, border_col=ACCENT, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        cx, cy = W // 2, 860 + float_y
        for ri, rad in enumerate([165, 215, 265]):
            start_a = int((lt * (140 if ri % 2 == 0 else -110) + ri * 60) % 360)
            col = ACCENT if ri == 0 else (SECONDARY if ri == 1 else POSITIVE)
            d.arc([cx - rad, cy - rad, cx + rad, cy + rad], start=start_a, end=start_a + 230, fill=col + (255,), width=10)
        draw_center_text(d, cy - 62, sc["metric_big"], f_gauge, TXT_MAIN)
        draw_center_text(d, cy + 48, sc["metric_label"][:14], f_xxs, ACCENT)

    elif w_type == "step_pyramid_stack":
        widths = [540, 690, 840]
        labels = [sc["left_label"], sc["right_label"], f"{sc['metric_big']} • {sc['metric_label']}"]
        cols = [TXT_MUTED, SECONDARY, ACCENT]
        for i in range(3):
            if lt > i * 0.25:
                sp = ease_out_back((lt - i * 0.25) / 0.35)
                bw = int(widths[i] * clamp(sp))
                if bw > 20:
                    bx1 = (W - bw) // 2
                    by1 = 620 + i * 172 + float_y
                    draw_elevated_card(canvas, [bx1, by1, bx1 + bw, by1 + 136], radius=28, border_col=cols[i], border_w=3)
                    if sp > 0.75:
                        d = ImageDraw.Draw(canvas)
                        draw_center_text(d, by1 + 44, labels[i], f_sm, TXT_MAIN if i < 2 else ACCENT)

    elif w_type == "spotlight_stat_pill":
        draw_elevated_card(canvas, [120, 600 + float_y, 960, 1120 + float_y], radius=46, border_col=SECONDARY, border_w=4, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        draw_center_text(d, 650 + float_y, sc["kicker"], f_xs, SECONDARY)
        draw_center_text(d, 725 + float_y, sc["metric_big"], f_big, TXT_MAIN)
        d.rounded_rectangle([240, 915 + float_y, 840, 995 + float_y], radius=40, fill=ACCENT + (255,))
        draw_center_text(d, 935 + float_y, sc["metric_label"], f_sm, (255, 255, 255))

    else:
        draw_elevated_card(canvas, [125, 595 + float_y, 955, 1115 + float_y], radius=42, border_col=CARD_BORDER, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        draw_center_text(d, 648 + float_y, sc["metric_big"], f_big, ACCENT)
        draw_center_text(d, 795 + float_y, sc["metric_label"], f_sm, TXT_MUTED)
        for b in range(18):
            bh = int(18 + 75 * abs(math.sin(lt * 10 + b * 0.65)))
            bx = 192 + b * 39
            bar_c = ACCENT if b % 3 != 0 else SECONDARY
            d.rounded_rectangle([bx, 1035 + float_y - bh, bx + 22, 1035 + float_y], radius=9, fill=bar_c + (240,))

def draw_top_header(canvas, sc, lt):
    d = ImageDraw.Draw(canvas)
    p = ease_out_back(lt / 0.30)
    dy = int((1.0 - p) * 28)
    alpha = int(clamp(p) * 255)

    kb = d.textbbox((0, 0), sc["kicker"], font=f_xs)
    kw = kb[2] - kb[0]
    pill_bg = tuple(int(BG_COL[i] * 0.85 + ACCENT[i] * 0.15) for i in range(3))
    d.rounded_rectangle([(W - kw)//2 - 30, 128 + dy, (W + kw)//2 + 30, 184 + dy], radius=28, fill=pill_bg + (alpha,), outline=ACCENT + (alpha,), width=2)
    d.text(((W - kw) // 2, 140 + dy), sc["kicker"], font=f_xs, fill=ACCENT + (alpha,))

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
    cap_bg = (15, 23, 42, 240) if IS_LIGHT else (10, 14, 26, 242)
    d.rounded_rectangle([max(45, (W - tot_w)//2 - 36), cy - 20, min(W - 45, (W + tot_w)//2 + 36), cy + 86], radius=32, fill=cap_bg, outline=ACCENT + (220,), width=3)

    cx = (W - tot_w) // 2
    for i, (w, ww, fnt) in enumerate(boxes):
        is_act = (i == active_idx)
        col = SECONDARY if is_act else (255, 255, 255)
        y_shift = -5 if is_act else 0
        d.text((int(cx), int(cy + y_shift)), w, font=fnt, fill=col + (255,))
        cx += ww + 22

total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) of Multi-Theme 12-Layout Studio Reel v15...")

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
    frame_img = get_animated_bg(sc_idx, lt, active_sc["duration"], t)
    d = ImageDraw.Draw(frame_img)

    prog_w = int((t / total_dur) * W)
    track_top = (212, 222, 238, 220) if IS_LIGHT else (30, 41, 59, 220)
    d.rectangle([0, 0, W, 12], fill=track_top)
    d.rectangle([0, 0, prog_w, 12], fill=ACCENT + (255,))
    for i in range(6):
        eh = int(12 + 24 * abs(math.sin(t * 12 + i * 1.2)))
        d.rounded_rectangle([910 + i * 16, 68 - eh // 2, 910 + i * 16 + 9, 68 + eh // 2], radius=4, fill=ACCENT + (235,))

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
        elif TRANSITION == "flash_zoom":
            flash_c = (255, 255, 255, int(205 * wp)) if IS_LIGHT else (15, 23, 42, int(215 * wp))
            overlay = Image.new("RGBA", (W, H), flash_c)
            frame_img.alpha_composite(overlay)
        else:
            bar_w = W // 5
            for b in range(5):
                bh = int(H * wp)
                if b % 2 == 0:
                    d.rectangle([b * bar_w, 0, (b + 1) * bar_w, bh], fill=ACCENT + (255,))
                else:
                    d.rectangle([b * bar_w, H - bh, (b + 1) * bar_w, H], fill=SECONDARY + (255,))

    ffmpeg.stdin.write(frame_img.tobytes())
    if frame % 300 == 0:
        print(f"Rendered {frame}/{total_frames} frames...")

ffmpeg.stdin.close()
ffmpeg.wait()
print("100% DONE! Multi-Theme 12-Layout Studio Reel v15 rendered successfully.")
