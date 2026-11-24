import json
import math
import os
import re
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
    "is_light": False,
    "bg": [7, 11, 22],
    "card": [14, 22, 40],
    "card_border": [46, 78, 136],
    "text_main": [248, 250, 252],
    "text_muted": [148, 163, 184],
    "accent": [56, 189, 248],
    "secondary": [250, 204, 21],
    "positive": [52, 211, 153],
    "negative": [248, 113, 113]
})

IS_LIGHT = PAL.get("is_light", False)
BG_COL = tuple(PAL.get("bg", [7, 11, 22]))
CARD_BG = tuple(PAL.get("card", [14, 22, 40]))
CARD_BORDER = tuple(PAL.get("card_border", [46, 78, 136]))
TXT_MAIN = tuple(PAL.get("text_main", [248, 250, 252]))
TXT_MUTED = tuple(PAL.get("text_muted", [148, 163, 184]))
ACCENT = tuple(PAL.get("accent", [56, 189, 248]))
SECONDARY = tuple(PAL.get("secondary", [250, 204, 21]))
POSITIVE = tuple(PAL.get("positive", [52, 211, 153]))
NEGATIVE = tuple(PAL.get("negative", [248, 113, 113]))
TRANSITION = DNA.get("transition", "flash_zoom")
THUMB_HOOK = DNA.get("thumbnail_hook", scenes[0].get("headline", "SACH JAAN LO").upper())
THUMB_BADGE = DNA.get("thumbnail_badge", scenes[0].get("kicker", "REALITY CHECK").upper())

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


f_xxs = load_font("fonts/Poppins-SemiBold.ttf", 22)
f_xs = load_font("fonts/Poppins-SemiBold.ttf", 26)
f_sm = load_font("fonts/Poppins-SemiBold.ttf", 34)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", 44)
f_headline = load_font("fonts/Poppins-ExtraBold.ttf", 64)
f_thumb_title = load_font("fonts/Poppins-ExtraBold.ttf", 80)
f_big = load_font("fonts/Poppins-ExtraBold.ttf", 116)
f_thumb_stat = load_font("fonts/Poppins-ExtraBold.ttf", 136)
f_gauge = load_font("fonts/Poppins-ExtraBold.ttf", 96)
f_caption = load_font("fonts/Poppins-ExtraBold.ttf", 52)
f_caption_big = load_font("fonts/Poppins-ExtraBold.ttf", 72)


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


VIGNETTE = Image.new("RGBA", (W, H), (0, 0, 0, 0))
vd = ImageDraw.Draw(VIGNETTE)
vig_alpha = 55 if IS_LIGHT else 120
for step in range(45):
    inset = step * 8
    a = int(vig_alpha * pow(1.0 - step / 45.0, 2.2))
    if a > 0:
        vd.rectangle([inset, inset, W - inset, H - inset], outline=(0, 0, 0, a), width=9)

prng = random.Random(42)
PARTICLES = [
    {
        "x": prng.randint(40, W - 40),
        "y": prng.randint(100, H - 100),
        "r": prng.randint(4, 9),
        "vx": prng.uniform(-16, 16),
        "vy": prng.uniform(-50, -18),
        "phase": prng.uniform(0, 6.28),
        "use_sec": (i % 3 == 0)
    }
    for i in range(26)
]

bg_images = []
for sc in scenes:
    im = Image.open(sc["bg_path"]).convert("RGB")
    im = im.resize((1260, 2240), Image.Resampling.LANCZOS)
    bg_images.append(im)


def get_animated_bg(sc_idx, lt, sc_dur, t_global):
    src = bg_images[sc_idx]
    prog = clamp(lt / max(0.1, sc_dur))
    punch = 0.06 * (1.0 - ease_out_cubic(lt / 0.25)) if lt < 0.25 else 0.0

    mode = sc_idx % 4
    if mode == 0:
        scale = 1.0 + 0.11 * prog + punch
        cw, ch = int(W / scale), int(H / scale)
        x1, y1 = (1260 - cw) // 2, (2240 - ch) // 2
    elif mode == 1:
        scale = 1.0 + punch
        cw, ch = int(W / scale), int(H / scale)
        x1 = int((1260 - cw) * prog)
        y1 = (2240 - ch) // 2
    elif mode == 2:
        scale = 1.11 - 0.11 * prog + punch
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
        pa = int(50 + 40 * math.sin(t_global * 3 + pt["phase"]))
        col = SECONDARY if pt["use_sec"] else ACCENT
        r = pt["r"]
        pd.ellipse([px - r, py - r, px + r, py + r], fill=col + (pa,))
    frame.alpha_composite(p_layer)
    frame.alpha_composite(VIGNETTE)
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
    sh_col = (15, 23, 42, 36) if IS_LIGHT else (0, 0, 0, 155)
    sd.rounded_rectangle([x1, y1 + 18, x2, y2 + 18], radius=safe_r, fill=sh_col)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.alpha_composite(shadow)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x1, y1, x2, y2], radius=safe_r, fill=CARD_BG + (alpha,), outline=border_col + (255,), width=border_w)
    if (x2 - 36) > (x1 + 36) + 6:
        ld.rounded_rectangle([x1 + 36, y1 + 2, x2 - 36, y1 + 7], radius=2, fill=ACCENT + (240,))

    if 0.0 <= shimmer_t <= 1.0:
        sx = int(x1 + (x2 - x1) * shimmer_t)
        sh_w = (255, 255, 255, 165) if IS_LIGHT else (255, 255, 255, 42)
        ld.line([(sx, y1 + 10), (max(x1 + 10, sx - 65), y2 - 10)], fill=sh_w, width=20)

    canvas.alpha_composite(layer)


def render_script_matched_thumbnail(sc0):
    base = bg_images[0].crop((90, 160, 90 + W, 160 + H)).convert("RGBA")
    dark_tint = Image.new("RGBA", (W, H), (8, 12, 24, 155) if IS_LIGHT else (4, 6, 14, 110))
    base.alpha_composite(dark_tint)
    base.alpha_composite(VIGNETTE)
    d = ImageDraw.Draw(base)

    d.rounded_rectangle([320, 165, 760, 225], radius=30, fill=(15, 23, 42, 235), outline=ACCENT + (255,), width=3)
    draw_center_text(d, 179, "@SOCHBADLO.HQ  •  REALITY", f_xxs, (255, 255, 255))

    bb_b = d.textbbox((0, 0), THUMB_BADGE, font=f_sm)
    bw = bb_b[2] - bb_b[0]
    d.rounded_rectangle([(W - bw) // 2 - 42, 285, (W + bw) // 2 + 42, 355], radius=20, fill=NEGATIVE + (255,))
    draw_center_text(d, 300, THUMB_BADGE, f_sm, (255, 255, 255))

    hook_lines = wrap_text(d, THUMB_HOOK, f_thumb_title, 940)[:3]
    y_cursor = 415
    for idx, ln in enumerate(hook_lines):
        col = SECONDARY if idx == 0 else (255, 255, 255)
        draw_center_text(d, y_cursor + 6, ln, f_thumb_title, (0, 0, 0), alpha=220)
        draw_center_text(d, y_cursor, ln, f_thumb_title, col)
        y_cursor += 96

    card_y1 = max(760, y_cursor + 45)
    card_y2 = card_y1 + 430
    draw_elevated_card(base, [110, card_y1, 970, card_y2], radius=48, border_col=SECONDARY, border_w=5, alpha=248)
    d = ImageDraw.Draw(base)

    bar_cols = [NEGATIVE, SECONDARY, ACCENT, POSITIVE]
    for bi in range(4):
        bh = 65 + bi * 32
        bx = 165 + bi * 52
        d.rounded_rectangle([bx, card_y2 - 60 - bh, bx + 34, card_y2 - 60], radius=10, fill=bar_cols[bi] + (220,))

    stat_txt = sc0.get("metric_big", "99%")
    lbl_txt = sc0.get("metric_label", "SACH JAAN LO")
    d.text((425, card_y1 + 65), stat_txt, font=f_thumb_stat, fill=SECONDARY + (255,))
    d.rounded_rectangle([425, card_y1 + 235, 915, card_y1 + 305], radius=22, fill=ACCENT + (255,))
    d.text((452, card_y1 + 250), lbl_txt, font=f_sm, fill=(255, 255, 255, 255))

    d.rounded_rectangle([180, card_y2 + 65, 900, card_y2 + 145], radius=40, fill=SECONDARY + (255,))
    draw_center_text(d, card_y2 + 83, "POORI VIDEO DEKHO  >>>", f_md, (12, 16, 28))
    return base


def draw_center_motion_graphic(canvas, sc, lt, sc_dur):
    w_type = sc.get("widget", "rupee_counter_shock")
    p_in = ease_out_back(lt / 0.30)
    alpha = int(clamp(p_in) * 255)
    float_y = int(7 * math.sin(lt * 3.5))
    shim = (lt % 2.2) / 0.85 if (lt % 2.2) < 0.85 else -1.0
    track_c = (226, 232, 240) if IS_LIGHT else (38, 50, 74)

    if w_type == "rupee_counter_shock":
        draw_elevated_card(canvas, [105, 575 + float_y, 975, 1140 + float_y], radius=44, border_col=SECONDARY, border_w=4, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([155, 620 + float_y, 515, 672 + float_y], radius=22, fill=NEGATIVE + (40,), outline=NEGATIVE + (220,), width=2)
        d.text((180, 632 + float_y), f"LIVE IMPACT • {sc['kicker']}", font=f_xxs, fill=NEGATIVE + (255,))

        raw_m = sc["metric_big"]
        m_match = re.search(r"(\d[\d,]*)", raw_m)
        if m_match and lt < 0.85:
            num_str = m_match.group(1)
            clean_num = int(num_str.replace(",", ""))
            cur_num = int(clean_num * ease_out_cubic(lt / 0.85))
            fmt_num = f"{cur_num:,}" if "," in num_str else str(cur_num)
            disp_m = raw_m.replace(num_str, fmt_num, 1)
        else:
            disp_m = raw_m

        draw_center_text(d, 710 + float_y, disp_m, f_big, SECONDARY, alpha=alpha)
        draw_center_text(d, 860 + float_y, sc["metric_label"], f_sm, TXT_MAIN, alpha=alpha)

        d.rounded_rectangle([160, 955 + float_y, 920, 1005 + float_y], radius=22, fill=track_c + (255,))
        bar_w = int(760 * ease_out_cubic(lt / 0.90) * (sc.get("pct", 92) / 100.0))
        d.rounded_rectangle([160, 955 + float_y, 160 + max(40, bar_w), 1005 + float_y], radius=22, fill=NEGATIVE + (255,))
        d.text((165, 1035 + float_y), f"{sc['left_label']}  →  {sc['right_label']}", font=f_xs, fill=TXT_MUTED + (255,))

    elif w_type == "phone_upi_alert":
        px1, py1, px2, py2 = 220, 560 + float_y, 860, 1165 + float_y
        draw_elevated_card(canvas, [px1, py1, px2, py2], radius=54, border_col=ACCENT, border_w=4)
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([W // 2 - 85, py1 + 24, W // 2 + 85, py1 + 52], radius=14, fill=(10, 12, 20, 255))

        pop_p = ease_out_back((lt - 0.12) / 0.32)
        ny1 = int(py1 + 105 + (1.0 - pop_p) * 60)
        ny2 = ny1 + 235
        notif_bg = (241, 245, 249, 255) if IS_LIGHT else (28, 38, 64, 255)
        d.rounded_rectangle([px1 + 34, ny1, px2 - 34, ny2], radius=30, fill=notif_bg, outline=NEGATIVE + (240,), width=3)
        d.rounded_rectangle([px1 + 58, ny1 + 28, px1 + 114, ny1 + 84], radius=16, fill=NEGATIVE + (255,))
        d.text((px1 + 76, ny1 + 36), "!", font=f_md, fill=(255, 255, 255, 255))
        d.text((px1 + 135, ny1 + 26), sc["kicker"], font=f_xs, fill=NEGATIVE + (255,))
        d.text((px1 + 135, ny1 + 60), "JUST NOW • ALERT", font=f_xxs, fill=TXT_MUTED + (255,))
        draw_text_clean(d, (px1 + 58, ny1 + 118), f"{sc['metric_big']}  •  {sc['right_label']}", f_md, TXT_MAIN)

        d.rounded_rectangle([px1 + 50, py2 - 165, px2 - 50, py2 - 65], radius=28, fill=ACCENT + (255,))
        draw_center_text(d, py2 - 138, sc["metric_label"], f_sm, (255, 255, 255))

    elif w_type == "scam_warning_stamp":
        draw_elevated_card(canvas, [110, 580 + float_y, 970, 1135 + float_y], radius=42, border_col=NEGATIVE, border_w=4, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        draw_center_text(d, 625 + float_y, sc["kicker"], f_xs, NEGATIVE)
        draw_center_text(d, 685 + float_y, sc["left_label"], f_md, TXT_MUTED)
        draw_center_text(d, 995 + float_y, sc["right_label"], f_md, TXT_MAIN)

        stamp_p = ease_out_back((lt - 0.18) / 0.26)
        if stamp_p > 0.05:
            st_layer = Image.new("RGBA", (680, 240), (0, 0, 0, 0))
            sd = ImageDraw.Draw(st_layer)
            sd.rounded_rectangle([20, 20, 660, 220], radius=28, fill=NEGATIVE + (38,), outline=NEGATIVE + (255,), width=10)
            st_txt = sc["metric_big"]
            bb = sd.textbbox((0, 0), st_txt, font=f_gauge)
            sd.text(((680 - (bb[2] - bb[0])) // 2, 52), st_txt, font=f_gauge, fill=NEGATIVE + (255,))
            rot_st = st_layer.rotate(-8, resample=Image.Resampling.BICUBIC, expand=True)
            canvas.alpha_composite(rot_st, ((W - rot_st.width) // 2, 745 + float_y))

    elif w_type == "vs_clash_cards":
        p1 = ease_out_back(lt / 0.28)
        p2 = ease_out_back((lt - 0.28) / 0.28)
        off1 = int((1.0 - p1) * -460)
        off2 = int((1.0 - p2) * 460)

        draw_elevated_card(canvas, [95 + off1, 610 + float_y, 505 + off1, 1085 + float_y], radius=36, border_col=NEGATIVE, border_w=3)
        d = ImageDraw.Draw(canvas)
        d.text((140 + off1, 658 + float_y), "X  GALAT MOVE", font=f_xs, fill=NEGATIVE + (255,))
        for idx, ln in enumerate(wrap_text(d, sc["left_label"], f_md, 340)[:2]):
            draw_text_clean(d, (140 + off1, 740 + idx * 58 + float_y), ln, f_md, TXT_MAIN)
        d.rounded_rectangle([140 + off1, 955 + float_y, 460 + off1, 988 + float_y], radius=14, fill=track_c + (255,))
        if int(115 * clamp(p1)) > 8:
            d.rounded_rectangle([140 + off1, 955 + float_y, 140 + off1 + int(115 * clamp(p1)), 988 + float_y], radius=14, fill=NEGATIVE + (255,))

        if lt > 0.22:
            draw_elevated_card(canvas, [575 + off2, 610 + float_y, 985 + off2, 1085 + float_y], radius=36, border_col=POSITIVE, border_w=4, shimmer_t=shim)
            d = ImageDraw.Draw(canvas)
            d.text((620 + off2, 658 + float_y), "+  SMART MOVE", font=f_xs, fill=POSITIVE + (255,))
            for idx, ln in enumerate(wrap_text(d, sc["right_label"], f_md, 340)[:2]):
                draw_text_clean(d, (620 + off2, 740 + idx * 58 + float_y), ln, f_md, TXT_MAIN)
            d.rounded_rectangle([620 + off2, 955 + float_y, 940 + off2, 988 + float_y], radius=14, fill=track_c + (255,))
            if int(320 * clamp(p2)) > 8:
                d.rounded_rectangle([620 + off2, 955 + float_y, 620 + off2 + int(320 * clamp(p2)), 988 + float_y], radius=14, fill=POSITIVE + (255,))

        if lt > 0.42:
            vp = ease_out_back((lt - 0.42) / 0.22)
            vr = max(4, int(48 * clamp(vp)))
            d.ellipse([W // 2 - vr, 848 + float_y - vr, W // 2 + vr, 848 + float_y + vr], fill=SECONDARY + (255,))
            if vp > 0.7:
                bb = d.textbbox((0, 0), "VS", font=f_sm)
                d.text(((W - (bb[2] - bb[0])) // 2, 828 + float_y), "VS", font=f_sm, fill=(15, 23, 42, 255))

    elif w_type == "stock_line_graph":
        draw_elevated_card(canvas, [105, 580 + float_y, 975, 1135 + float_y], radius=40, border_col=ACCENT, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        d.text((160, 628 + float_y), f"CURVE • {sc['metric_label']}", font=f_xs, fill=TXT_MUTED + (255,))
        d.text((710, 618 + float_y), sc["metric_big"], font=f_md, fill=POSITIVE + (255,))

        pts_raw = [(175, 1020), (315, 975), (455, 995), (595, 875), (735, 815), (890, 715)]
        pts = [(x, y + float_y) for (x, y) in pts_raw]
        gp = ease_out_cubic(lt / 0.90)
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
            ImageDraw.Draw(fill_l).polygon(poly, fill=ACCENT + (48,))
            canvas.alpha_composite(fill_l)
            d = ImageDraw.Draw(canvas)
            d.line(drawn_pts, fill=ACCENT + (255,), width=11)
            for px, py in drawn_pts:
                d.ellipse([px - 10, py - 10, px + 10, py + 10], fill=SECONDARY + (255,), outline=CARD_BG + (255,), width=3)
            lx, ly = drawn_pts[-1]
            halo = int(18 + 8 * math.sin(lt * 10))
            d.ellipse([lx - halo, ly - halo, lx + halo, ly + halo], outline=POSITIVE + (220,), width=4)

    elif w_type == "animated_bar_chart":
        draw_elevated_card(canvas, [105, 580 + float_y, 975, 1135 + float_y], radius=40, border_col=CARD_BORDER, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        d.text((160, 628 + float_y), f"METER • {sc['metric_label']}", font=f_xs, fill=TXT_MUTED + (255,))
        d.text((710, 618 + float_y), sc["metric_big"], font=f_md, fill=ACCENT + (255,))

        heights = [0.30, 0.46, 0.64, 0.82, 1.0]
        base_y = 1050 + float_y
        for i, h_mul in enumerate(heights):
            bp = ease_out_cubic((lt - i * 0.09) / 0.40)
            bh = int(315 * h_mul * bp)
            if bh > 6:
                bx = 180 + i * 152
                col = ACCENT if i == 4 else (SECONDARY if i == 3 else track_c)
                d.rounded_rectangle([bx, base_y - bh, bx + 96, base_y], radius=min(20, bh // 2), fill=col + (255,))

    elif w_type == "circular_gauge":
        pct = sc.get("pct", 94)
        gp = ease_out_cubic(lt / 0.90)
        cur_val = int(pct * gp)
        draw_elevated_card(canvas, [155, 555 + float_y, 925, 1165 + float_y], radius=44, border_col=ACCENT, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        cx, cy, r = W // 2, 855 + float_y, 205
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=track_c + (255,), width=26)
        d.arc([cx - r, cy - r, cx + r, cy + r], start=-90, end=-90 + int(360 * (cur_val / 100.0)), fill=ACCENT + (255,), width=26)
        draw_center_text(d, cy - 68, f"{cur_val}%", f_gauge, TXT_MAIN)
        draw_center_text(d, cy + 48, sc["metric_label"][:16], f_xxs, SECONDARY)

    elif w_type == "typing_terminal_hud":
        draw_elevated_card(canvas, [115, 595 + float_y, 965, 1115 + float_y], radius=38, border_col=ACCENT, border_w=3, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        for di, dc in enumerate([NEGATIVE, SECONDARY, POSITIVE]):
            d.ellipse([160 + di * 32, 635 + float_y, 178 + di * 32, 653 + float_y], fill=dc + (255,))
        d.text((280, 630 + float_y), f"FACT CHECK // {sc['kicker']}", font=f_xxs, fill=TXT_MUTED + (255,))
        d.line([(145, 680 + float_y), (935, 680 + float_y)], fill=CARD_BORDER + (255,), width=2)

        full_str = f"> {sc['right_label'].upper()} : {sc['metric_big']}"
        vis_chars = max(1, int(len(full_str) * clamp(lt / 0.70)))
        cursor = " |" if int(lt * 6) % 2 == 0 else ""
        d.text((160, 735 + float_y), full_str[:vis_chars] + cursor, font=f_md, fill=ACCENT + (255,))
        d.text((160, 825 + float_y), f"STATUS: {sc['metric_label']}", font=f_sm, fill=TXT_MAIN + (255,))

        d.rounded_rectangle([160, 960 + float_y, 920, 1005 + float_y], radius=18, fill=track_c + (255,))
        fill_w = int(760 * ease_out_cubic(lt / 0.95) * (sc.get("pct", 94) / 100.0))
        d.rounded_rectangle([160, 960 + float_y, 160 + max(36, fill_w), 1005 + float_y], radius=18, fill=POSITIVE + (255,))

    elif w_type == "floating_checklist":
        rows = [
            ("01", sc["left_label"], SECONDARY, 0.06),
            ("02", sc["right_label"], ACCENT, 0.36),
            ("03", sc["metric_label"], POSITIVE, 0.66)
        ]
        for idx, (num, label, badge_c, delay) in enumerate(rows):
            if lt > delay:
                rp = ease_out_back((lt - delay) / 0.28)
                ry = int(585 + idx * 185 + (1.0 - rp) * 55 + float_y)
                draw_elevated_card(canvas, [115, ry, 965, ry + 148], radius=32, border_col=badge_c, border_w=3)
                d = ImageDraw.Draw(canvas)
                d.rounded_rectangle([155, ry + 34, 235, ry + 114], radius=22, fill=badge_c + (255,))
                d.text((174, ry + 52), num, font=f_sm, fill=(255, 255, 255, 255))
                draw_text_clean(d, (270, ry + 50), label, f_md, TXT_MAIN)

    elif w_type == "split_duel_banner":
        draw_elevated_card(canvas, [105, 595 + float_y, 975, 830 + float_y], radius=34, border_col=NEGATIVE, border_w=3)
        d = ImageDraw.Draw(canvas)
        d.text((155, 632 + float_y), "PURANI GALTI", font=f_xs, fill=NEGATIVE + (255,))
        draw_text_clean(d, (155, 695 + float_y), sc["left_label"], f_md, TXT_MAIN)

        if lt > 0.22:
            draw_elevated_card(canvas, [105, 880 + float_y, 975, 1130 + float_y], radius=34, border_col=POSITIVE, border_w=4, shimmer_t=shim)
            d = ImageDraw.Draw(canvas)
            d.text((155, 918 + float_y), f"SMART SHIFT • {sc['metric_big']}", font=f_xs, fill=POSITIVE + (255,))
            draw_text_clean(d, (155, 982 + float_y), sc["right_label"], f_md, TXT_MAIN)

    elif w_type == "step_pyramid_stack":
        widths = [540, 690, 840]
        labels = [sc["left_label"], sc["right_label"], f"{sc['metric_big']} • {sc['metric_label']}"]
        cols = [TXT_MUTED, SECONDARY, ACCENT]
        for i in range(3):
            if lt > i * 0.18:
                sp = ease_out_back((lt - i * 0.18) / 0.28)
                bw = int(widths[i] * clamp(sp))
                if bw > 20:
                    bx1 = (W - bw) // 2
                    by1 = 620 + i * 172 + float_y
                    draw_elevated_card(canvas, [bx1, by1, bx1 + bw, by1 + 136], radius=28, border_col=cols[i], border_w=3)
                    if sp > 0.75:
                        d = ImageDraw.Draw(canvas)
                        draw_center_text(d, by1 + 44, labels[i], f_sm, TXT_MAIN if i < 2 else ACCENT)

    else:
        draw_elevated_card(canvas, [120, 600 + float_y, 960, 1120 + float_y], radius=46, border_col=SECONDARY, border_w=4, shimmer_t=shim)
        d = ImageDraw.Draw(canvas)
        draw_center_text(d, 650 + float_y, sc["kicker"], f_xs, SECONDARY)
        draw_center_text(d, 725 + float_y, sc["metric_big"], f_big, TXT_MAIN)
        d.rounded_rectangle([240, 915 + float_y, 840, 995 + float_y], radius=40, fill=ACCENT + (255,))
        draw_center_text(d, 935 + float_y, sc["metric_label"], f_sm, (255, 255, 255))


def draw_top_header(canvas, sc, lt):
    d = ImageDraw.Draw(canvas)
    p = ease_out_back(lt / 0.24)
    dy = int((1.0 - p) * 26)
    alpha = int(clamp(p) * 255)

    kb = d.textbbox((0, 0), sc["kicker"], font=f_xs)
    kw = kb[2] - kb[0]
    pill_bg = tuple(int(BG_COL[i] * 0.82 + ACCENT[i] * 0.18) for i in range(3))
    d.rounded_rectangle([(W - kw) // 2 - 32, 128 + dy, (W + kw) // 2 + 32, 184 + dy], radius=28, fill=pill_bg + (alpha,), outline=ACCENT + (alpha,), width=2)
    d.text(((W - kw) // 2, 140 + dy), sc["kicker"], font=f_xs, fill=ACCENT + (alpha,))

    lines = wrap_text(d, sc["headline"], f_headline, 940)[:2]
    for idx, line in enumerate(lines):
        lb = d.textbbox((0, 0), line, font=f_headline)
        lw = lb[2] - lb[0]
        lx = (W - lw) // 2
        ly = 214 + idx * 80 + dy
        draw_text_clean(d, (lx, ly), line, f_headline, TXT_MAIN, alpha=alpha)


POWER_WORDS = {
    "scam", "trap", "loss", "gayab", "barbaad", "free", "secret", "galti",
    "ameer", "gareeb", "paisa", "paise", "lakh", "crore", "emi", "upi",
    "sip", "gst", "cibil", "dopamine", "focus", "dimag", "save", "share"
}


def draw_viral_captions(canvas, text, lt, sc_dur):
    """Hormozi / Premiere Pro Style Bouncing Word-Pop Captions with Neon Highlight Pill."""
    words = text.split()
    if not words:
        return
    chunk_size = 3
    total_chunks = math.ceil(len(words) / chunk_size)
    chunk_idx = min(total_chunks - 1, int((lt / max(0.1, sc_dur)) * total_chunks))
    chunk = words[chunk_idx * chunk_size : (chunk_idx + 1) * chunk_size]

    chunk_dur = sc_dur / max(1, total_chunks)
    chunk_local = lt - chunk_idx * chunk_dur
    word_dur = chunk_dur / max(1, len(chunk))
    active_idx = min(len(chunk) - 1, int(chunk_local / max(0.05, word_dur)))
    word_local = chunk_local - active_idx * word_dur

    # Pop bounce animation on active word
    pop_ease = ease_out_back(word_local / min(0.16, max(0.06, word_dur)))
    d = ImageDraw.Draw(canvas)

    boxes = []
    tot_w = 0
    for i, w in enumerate(chunk):
        is_act = (i == active_idx)
        fnt = f_caption_big if is_act else f_caption
        disp_w = w.upper() if is_act else w
        bb = d.textbbox((0, 0), disp_w, font=fnt)
        ww = bb[2] - bb[0]
        wh = bb[3] - bb[1]
        boxes.append((disp_w, ww, wh, fnt, is_act))
        tot_w += ww + 34
    tot_w -= 34

    # Subtle vertical alternation per chunk so captions feel alive & dynamic
    cy = 1355 + (-10 if chunk_idx % 2 == 1 else 6)

    # Dark backdrop plate behind whole phrase
    plate_bg = (10, 14, 26, 225) if IS_LIGHT else (6, 10, 20, 225)
    d.rounded_rectangle(
        [max(34, (W - tot_w) // 2 - 42), cy - 26, min(W - 34, (W + tot_w) // 2 + 42), cy + 104],
        radius=34, fill=plate_bg, outline=CARD_BORDER + (190,), width=2
    )

    cx = (W - tot_w) // 2
    for disp_w, ww, wh, fnt, is_act in boxes:
        clean_low = re.sub(r"[^a-zA-Z0-9₹%]", "", disp_w).lower()
        is_power = any(ch.isdigit() or ch in "₹%" for ch in disp_w) or (clean_low in POWER_WORDS)

        if is_act:
            bounce_y = int(-14 * pop_ease)
            pill_col = NEGATIVE if (clean_low in {"scam", "trap", "loss", "gayab", "barbaad", "galti"}) else SECONDARY
            # Glowing Neon Highlight Box behind the spoken active word
            d.rounded_rectangle(
                [int(cx - 16), int(cy + bounce_y - 12), int(cx + ww + 16), int(cy + bounce_y + 84)],
                radius=22, fill=pill_col + (255,)
            )
            txt_col = (255, 255, 255) if pill_col == NEGATIVE else (10, 14, 24)
            d.text((int(cx), int(cy + bounce_y - 4)), disp_w, font=fnt, fill=txt_col + (255,))
        else:
            col = SECONDARY if is_power else (245, 248, 255)
            # Crisp dark outline for high contrast
            for ox, oy in [(-2, 2), (2, 2), (0, 3)]:
                d.text((int(cx + ox), int(cy + 8 + oy)), disp_w, font=fnt, fill=(0, 0, 0, 220))
            d.text((int(cx), int(cy + 8)), disp_w, font=fnt, fill=col + (255,))

        cx += ww + 34

    draw_center_text(d, 1515, "@sochbadlo.hq", f_xxs, TXT_MUTED, alpha=170)


total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) of V18 Premiere-Pro Motion Studio + Custom Cover...")

ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(FPS),
    "-i", "-", "-i", "final_audio.m4a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "final_reel.mp4"
], stdin=subprocess.PIPE)

cover_frame_0 = render_script_matched_thumbnail(scenes[0])

for frame in range(total_frames):
    if frame == 0:
        ffmpeg.stdin.write(cover_frame_0.tobytes())
        continue

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
    if sc_idx < len(scenes) - 1 and rem < 0.20:
        wp = clamp((0.20 - rem) / 0.20)
        if TRANSITION == "iris_reveal":
            rad = int(1250 * wp)
            d.ellipse([W // 2 - rad, H // 2 - rad, W // 2 + rad, H // 2 + rad], fill=ACCENT + (255,))
        elif TRANSITION == "prism_wipe":
            bw = int((W // 2) * wp)
            d.rectangle([0, 0, bw, H], fill=ACCENT + (255,))
            d.rectangle([W - bw, 0, W, H], fill=SECONDARY + (255,))
        elif TRANSITION == "flash_zoom":
            flash_c = (255, 255, 255, int(195 * wp)) if IS_LIGHT else (10, 15, 28, int(215 * wp))
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
print("100% DONE! V18 Premiere-Pro Motion Studio + Custom Cover Reel rendered successfully.")
