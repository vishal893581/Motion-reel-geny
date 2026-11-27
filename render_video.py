import json
import math
import os
import random
import subprocess
import urllib.request
from PIL import Image, ImageDraw, ImageFont

with open("timeline.json") as f:
    data = json.load(f)

total_dur = data["total_duration"]
beats = data["beats"]
THUMB_HERO = data.get("thumb_hero", "SMART PLAN")
THUMB_SUB = data.get("thumb_sub", "3-Step Formula")
THUMB_BADGE = data.get("thumb_badge", "3 STEPS")
DAY = data.get("day", 1)
SERIES = data.get("series", "PAISA REALITY")
NEXT_TEASER = data.get("next_teaser", "")

W, H = 1080, 1920
FPS = 30
CARD_SCALE = 1.4
HANDLE = "@sochbadlo.hq"

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


f_xs = load_font("fonts/Poppins-Bold.ttf", 22)
f_sm = load_font("fonts/Poppins-Bold.ttf", 29)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", 42)
f_sub = load_font("fonts/Poppins-ExtraBold.ttf", 62)
f_hero_lg = load_font("fonts/Poppins-Black.ttf", 168)
f_hero_md = load_font("fonts/Poppins-Black.ttf", 132)
f_hero_sm = load_font("fonts/Poppins-Black.ttf", 104)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158
    return 1 + (c1 + 1) * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - pow(1 - t, 3)


# Exact Palette: Warm Cream Paper + Deep Crimson Maroon + Burnt Orange + Gold
C_CREAM = (239, 230, 213)
C_MAROON_BG = (92, 16, 16)
C_MAROON = (112, 20, 20)
C_MAROON_DARK = (52, 8, 8)
C_ORANGE = (218, 92, 38)
C_ORANGE_DARK = (118, 42, 12)
C_GOLD = (238, 178, 46)
C_WHITE = (252, 249, 242)
C_INK = (45, 22, 18)


def make_textured_bg(base_rgb):
    img = Image.new("RGBA", (W, H), base_rgb + (255,))
    dr = ImageDraw.Draw(img)
    rng = random.Random(42)
    for _ in range(22000):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        d = rng.randint(-9, 9)
        c = tuple(clamp(base_rgb[k] + d, 0, 255) for k in range(3)) + (255,)
        dr.point((x, y), fill=c)
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for step in range(32):
        inset = step * 10
        a = int(50 * pow(1.0 - step / 32.0, 2.0))
        if a > 0:
            vd.rectangle([inset, inset, W - inset, H - inset], outline=(25, 10, 8, a), width=11)
    img.alpha_composite(vig)
    return img


BG_CREAM = make_textured_bg(C_CREAM)
BG_MAROON = make_textured_bg(C_MAROON_BG)


_HERO_CACHE = {}
_probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))


def choose_hero_font(text, max_w=900):
    """Auto-fit: biggest Poppins-Black size whose width fits the portrait frame."""
    if text in _HERO_CACHE:
        return _HERO_CACHE[text]
    chosen = None
    for size in range(200, 60, -8):
        f = load_font("fonts/Poppins-Black.ttf", size)
        bb = _probe.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= max_w:
            chosen = f
            break
    chosen = chosen or load_font("fonts/Poppins-Black.ttf", 60)
    _HERO_CACHE[text] = chosen
    return chosen


def draw_3d_hero_text(draw, cx, cy, text, color_key="maroon", strike_prog=0.0):
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

    for depth in range(13, 0, -1):
        draw.text((x + depth, y + depth), text, font=font, fill=side + (255,))
    draw.text((x, y), text, font=font, fill=front + (255,))

    if strike_prog > 0.02:
        sx1 = x - 20
        sx2 = x - 20 + int((tw + 40) * clamp(strike_prog))
        sy = y + int(th * 0.56)
        draw.rounded_rectangle([sx1, sy - 10, sx2, sy + 10], radius=8, fill=C_ORANGE + (255,))
    return x, y, tw, th


def draw_live_kinetic_captions(draw, cx, cy, sub_text, pill_word, lt, dur, is_dark_bg=False, max_w=940, word_times=None):
    """Karaoke captions. If word_times (seconds from beat start, one per word) is given the
    active word follows the REAL voice timing; otherwise falls back to an even spread."""
    words = sub_text.split()
    if not words:
        return
    pill_clean = pill_word.strip().lower()
    n = len(words)

    if word_times and len(word_times) == n:
        active_word_idx = 0
        for i, wt in enumerate(word_times):
            if lt >= wt - 0.04:
                active_word_idx = i
        visible_limit = active_word_idx + 1
        word_age_of = lambda g: clamp((lt - (word_times[g] - 0.04)) * 7.0)
    else:
        speak_prog = clamp(lt / max(0.35, dur * 0.85))
        active_word_idx = min(n - 1, int(speak_prog * n))
        visible_limit = max(1, int(math.ceil(speak_prog * n + 0.35)))
        word_age_of = lambda g: clamp((speak_prog * n - g) * 2.5)

    lines, cur = [], []
    for g, w in enumerate(words):
        test = " ".join([item[0] for item in cur] + [w])
        if draw.textbbox((0, 0), test, font=f_sub)[2] <= max_w - 60:
            cur.append((w, g))
        else:
            if cur:
                lines.append(cur)
            cur = [(w, g)]
    if cur:
        lines.append(cur)

    # keep the line that holds the active word + previous one (max 3 visible lines)
    act_line = 0
    for li, lw in enumerate(lines):
        if any(g == active_word_idx for _, g in lw):
            act_line = li
    first = max(0, act_line - 2)
    lines = lines[first:first + 3]

    txt_col = C_CREAM if is_dark_bg else C_MAROON
    dim_col = (195, 175, 165) if is_dark_bg else (150, 100, 90)
    LH = 96

    for l_idx, l_words in enumerate(lines):
        items, tot_w = [], 0
        for w, g_idx in l_words:
            bb = draw.textbbox((0, 0), w, font=f_sub)
            ww = bb[2] - bb[0]
            is_key = bool(pill_clean) and (pill_clean in w.lower() or w.lower() in pill_clean)
            is_active = (g_idx == active_word_idx)
            pad = 30 if (is_key or is_active) else 0
            items.append((w, g_idx, ww, is_key, is_active, pad))
            tot_w += ww + pad + 18
        tot_w -= 18

        x = int(cx - tot_w // 2)
        y = int(cy + l_idx * LH)
        for w, g_idx, ww, is_key, is_active, pad in items:
            if g_idx < visible_limit:
                lift_y = int((1.0 - ease_out_back(word_age_of(g_idx))) * 14)
                if is_active:
                    hl_bg = C_GOLD if not is_dark_bg else C_ORANGE
                    hl_fg = C_INK if not is_dark_bg else C_WHITE
                    draw.rounded_rectangle([x, y - 8 + lift_y, x + ww + pad, y + 82 + lift_y], radius=32, fill=hl_bg + (255,))
                    draw.text((x + pad // 2, y + lift_y), w, font=f_sub, fill=hl_fg + (255,))
                elif is_key:
                    kw_bg = C_ORANGE if is_dark_bg else C_MAROON
                    draw.rounded_rectangle([x, y - 6 + lift_y, x + ww + pad, y + 80 + lift_y], radius=32, fill=kw_bg + (255,))
                    draw.text((x + pad // 2, y + lift_y), w, font=f_sub, fill=C_WHITE + (255,))
                else:
                    draw.text((x, y + lift_y), w, font=f_sub, fill=txt_col + (255,))
            x += ww + pad + 18


def draw_card_shell(d, cw, ch, title, use_gold_hdr=False):
    d.rounded_rectangle([20, 24, cw + 20, ch + 24], radius=30, fill=(35, 15, 10, 48))
    d.rounded_rectangle([12, 12, cw + 12, ch + 12], radius=30, fill=C_WHITE + (255,), outline=(218, 206, 188, 255), width=4)
    hdr_col = C_GOLD if use_gold_hdr else C_MAROON
    hdr_txt = C_INK if use_gold_hdr else C_WHITE
    d.rounded_rectangle([34, 30, cw - 10, 86], radius=16, fill=hdr_col + (255,))
    tbb = d.textbbox((0, 0), title, font=f_xs)
    d.text((12 + (cw - (tbb[2] - tbb[0])) // 2, 43), title, font=f_xs, fill=hdr_txt + (255,))


def draw_dynamic_visual(canvas, cx, cy, b, pop_t):
    vtype = b.get("visual", "none")
    if vtype == "none":
        return

    scale = 0.78 + 0.22 * ease_out_back(pop_t)
    cw = int((560 if vtype in ("grid4", "compare_bars", "growth_chart", "donut_split") else 470) * scale)
    ch = int(510 * scale)
    card = Image.new("RGBA", (cw + 36, ch + 36), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)

    title = b.get("v_title", "INSIGHT")
    val = b.get("v_data", "")
    sub = b.get("v_sub", "")

    if vtype == "donut_split":
        ocx, ocy, rad = (cw + 36) // 2, 235, 138
        parts = [p.strip() for p in val.split("|") if p.strip()]
        while len(parts) < 3:
            parts.append("Part")
        sweep = int(360 * clamp(pop_t * 1.2))
        d.pieslice([ocx - rad, ocy - rad, ocx + rad, ocy + rad], -90, -90 + min(180, sweep), fill=C_MAROON + (255,))
        if sweep > 180:
            d.pieslice([ocx - rad, ocy - rad, ocx + rad, ocy + rad], 90, 90 + min(108, sweep - 180), fill=C_ORANGE + (255,))
        if sweep > 288:
            d.pieslice([ocx - rad, ocy - rad, ocx + rad, ocy + rad], 198, -90 + sweep, fill=C_GOLD + (255,))
        d.ellipse([ocx - 68, ocy - 68, ocx + 68, ocy + 68], fill=C_CREAM + (255,))
        d.text((ocx - 42, ocy - 14), "100%", font=f_sm, fill=C_INK + (255,))
        cols = [C_MAROON, C_ORANGE, C_GOLD]
        for idx, pt in enumerate(parts[:3]):
            lx = 24 + idx * ((cw - 20) // 3)
            d.rounded_rectangle([lx, 405, lx + (cw - 36) // 3, 456], radius=14, fill=cols[idx] + (255,))
            fg = C_INK if idx == 2 else C_WHITE
            d.text((lx + 12, 417), pt[:11], font=f_xs, fill=fg + (255,))

    elif vtype == "growth_chart":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        bars = [p.strip() for p in val.split("|") if p.strip()][:3]
        while len(bars) < 3:
            bars.append("Step")
        heights = [95, 175, 265]
        bar_cols = [C_MAROON, C_ORANGE, C_GOLD]
        for i in range(3):
            bx = 75 + i * 155
            bh = int(heights[i] * clamp(pop_t * 1.25 - i * 0.12))
            by = 410 - bh
            if bh > 6:
                d.rounded_rectangle([bx, by, bx + 95, 410], radius=14, fill=bar_cols[i] + (255,))
            d.text((bx - 8, 420), bars[i][:13], font=f_xs, fill=C_INK + (255,))

    elif vtype == "wallet_empty":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        parts = val.split("|") if "|" in val else ["₹30,000", "₹420"]
        d.text((52, 125), f"Start: {parts[0].strip()[:12]}", font=f_sm, fill=C_INK + (255,))
        d.rounded_rectangle([52, 175, cw - 32, 225], radius=16, fill=(235, 226, 212, 255))
        rem_w = max(28, int((cw - 84) * (1.0 - 0.88 * clamp(pop_t))))
        d.rounded_rectangle([52, 175, 52 + rem_w, 225], radius=16, fill=C_ORANGE + (255,))
        d.text((52, 265), f"Left: {parts[1].strip()[:12]}", font=f_md, fill=C_MAROON + (255,))

    elif vtype == "coin_stack":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        parts = val.split("|") if "|" in val else ["₹6L", "₹12.4L"]
        for c in range(3):
            cy_s = 360 - c * 28
            d.ellipse([85, cy_s, 195, cy_s + 24], fill=C_MAROON + (255,), outline=C_WHITE, width=2)
        d.text((70, 400), parts[0].strip()[:14], font=f_xs, fill=C_INK + (255,))
        tall_n = max(1, int(7 * clamp(pop_t)))
        for c in range(tall_n):
            cy_s = 360 - c * 28
            d.ellipse([275, cy_s, 395, cy_s + 24], fill=C_GOLD + (255,), outline=C_ORANGE, width=2)
        d.text((260, 400), parts[1].strip()[:14], font=f_xs, fill=C_MAROON + (255,))

    elif vtype == "mic_wave":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        mcx = 12 + cw // 2
        d.rounded_rectangle([mcx - 28, 120, mcx + 28, 220], radius=26, fill=C_MAROON + (255,))
        d.arc([mcx - 46, 150, mcx + 46, 240], 0, 180, fill=C_ORANGE + (255,), width=6)
        d.line([(mcx, 240), (mcx, 278)], fill=C_INK + (255,), width=6)
        wave_h = [24, 52, 80, 42, 92, 60, 30, 74, 46, 26]
        for i, wh in enumerate(wave_h):
            wx = 65 + i * 35
            anim_h = int(wh * (0.5 + 0.5 * abs(math.sin(pop_t * 5 + i))))
            d.rounded_rectangle([wx, 345 - anim_h // 2, wx + 18, 345 + anim_h // 2], radius=8, fill=C_ORANGE if i % 2 == 0 else C_MAROON)
        d.text((135, 405), val[:18], font=f_sm, fill=C_MAROON + (255,))

    elif vtype == "eye_triangle":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        pts = [p.strip() for p in val.split("|") if p.strip()]
        while len(pts) < 3:
            pts.append("Point")
        p_top = (12 + cw // 2, 145)
        p_bl = (105, 345)
        p_br = (cw - 80, 345)
        d.line([p_top, p_bl, p_br, p_top], fill=C_ORANGE + (255,), width=7)
        for pt_xy, lbl, col in [(p_top, pts[1], C_MAROON), (p_bl, pts[0], C_GOLD), (p_br, pts[2], C_GOLD)]:
            d.ellipse([pt_xy[0] - 28, pt_xy[1] - 28, pt_xy[0] + 28, pt_xy[1] + 28], fill=col + (255,))
            d.text((pt_xy[0] - 42, pt_xy[1] + 34), lbl[:10], font=f_xs, fill=C_INK + (255,))

    elif vtype == "grid4":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        cells = [r.strip() for r in val.split("|") if r.strip()]
        while len(cells) < 4:
            cells.append("Point")
        box_w = (cw - 76) // 2
        box_h = 148
        box_cols = [(255, 246, 224), (244, 238, 228), (244, 238, 228), (255, 246, 224)]
        for i in range(4):
            bx = 34 + (i % 2) * (box_w + 16)
            by = 110 + (i // 2) * (box_h + 16)
            if pop_t > 0.12 + i * 0.12:
                d.rounded_rectangle([bx, by, bx + box_w, by + box_h], radius=18, fill=box_cols[i] + (255,), outline=C_GOLD if i in (0, 3) else C_MAROON, width=3)
                d.rounded_rectangle([bx + 14, by + 14, bx + 52, by + 48], radius=10, fill=C_ORANGE if i % 2 == 0 else C_MAROON)
                d.text((bx + 25, by + 18), f"0{i+1}", font=f_xs, fill=C_WHITE + (255,))
                d.text((bx + 16, by + 68), cells[i][:14], font=f_sm, fill=C_INK + (255,))

    elif vtype == "bubble":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        ax, ay = 105, 285
        d.ellipse([ax - 34, ay - 72, ax + 34, ay - 4], fill=C_ORANGE + (255,))
        d.pieslice([ax - 62, ay + 6, ax + 62, ay + 110], 180, 360, fill=C_MAROON + (255,))
        d.rounded_rectangle([185, 165, cw - 18, 290], radius=26, fill=(246, 240, 230, 255), outline=C_MAROON + (255,), width=4)
        d.polygon([(185, 220), (160, 235), (185, 250)], fill=C_MAROON + (255,))
        d.text((206, 210), val[:22], font=f_xs, fill=C_INK + (255,))

    elif vtype in ("checklist", "sheet"):
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        rows = [r.strip() for r in val.split("|") if r.strip()][:3]
        for idx, r in enumerate(rows):
            ry = 122 + idx * 96
            d.rounded_rectangle([38, ry, 82, ry + 44], radius=10, outline=C_MAROON + (255,), width=4)
            if pop_t > 0.28 + idx * 0.15:
                d.line([(47, ry + 22), (58, ry + 34), (75, ry + 11)], fill=C_ORANGE + (255,), width=6)
            d.text((98, ry + 5), r[:20], font=f_sm, fill=C_INK + (255,))
        d.rounded_rectangle([38, ch - 82, cw - 14, ch - 58], radius=10, fill=(228, 220, 206, 255))
        pw = int((cw - 52) * clamp(pop_t))
        if pw > 12:
            d.rounded_rectangle([38, ch - 82, 38 + pw, ch - 58], radius=10, fill=C_GOLD + (255,))

    elif vtype == "compare_bars":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        parts = val.split("|") if "|" in val else (val.split("vs") if "vs" in val else [val, "SMART"])
        p1, p2 = parts[0].strip()[:14], parts[1].strip()[:14]
        d.rounded_rectangle([34, 120, cw // 2 - 6, ch - 78], radius=20, fill=(244, 238, 228, 255), outline=(210, 198, 180, 255), width=3)
        d.rounded_rectangle([cw // 2 + 18, 120, cw - 10, ch - 78], radius=20, fill=(255, 246, 224, 255), outline=C_GOLD + (255,), width=4)
        d.text((50, 175), p1, font=f_xs, fill=C_INK + (255,))
        d.text((cw // 2 + 34, 175), p2, font=f_xs, fill=C_MAROON + (255,))
        d.rounded_rectangle([cw // 2 - 24, 255, cw // 2 + 44, 310], radius=26, fill=C_ORANGE + (255,))
        d.text((cw // 2 - 7, 268), "VS", font=f_xs, fill=C_WHITE + (255,))

    elif vtype == "clock":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        ocx, ocy, rad = 12 + cw // 2, 260, 120
        d.ellipse([ocx - rad, ocy - rad, ocx + rad, ocy + rad], fill=(252, 248, 240, 255), outline=C_ORANGE + (255,), width=14)
        ang = -math.pi / 3 + pop_t * 1.4
        d.line([(ocx, ocy), (ocx + int(82 * math.cos(ang)), ocy + int(82 * math.sin(ang)))], fill=C_MAROON + (255,), width=8)
        d.line([(ocx, ocy), (ocx, ocy - 64)], fill=C_INK + (255,), width=8)
        d.ellipse([ocx - 10, ocy - 10, ocx + 10, ocy + 10], fill=C_ORANGE + (255,))

    elif vtype == "phone":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        px1, px2 = 12 + cw // 2 - 90, 12 + cw // 2 + 90
        d.rounded_rectangle([px1, 115, px2, 415], radius=26, fill=(32, 24, 22, 255), outline=C_MAROON + (255,), width=6)
        d.rounded_rectangle([px1 + 14, 145, px2 - 14, 385], radius=16, fill=(246, 238, 226, 255))
        d.text((px1 + 28, 240), val[:12], font=f_xs, fill=C_MAROON + (255,))

    elif vtype == "trap_cross":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        vbb = d.textbbox((0, 0), val[:18], font=f_sm)
        d.text((12 + (cw - (vbb[2] - vbb[0])) // 2, 230), val[:18], font=f_sm, fill=C_MAROON + (255,))
        if pop_t > 0.25:
            p = clamp((pop_t - 0.25) / 0.5)
            d.line([(55, 130), (55 + int((cw - 90) * p), 130 + int(260 * p))], fill=C_ORANGE + (255,), width=14)
            d.line([(cw - 35, 130), (cw - 35 - int((cw - 90) * p), 130 + int(260 * p))], fill=C_ORANGE + (255,), width=14)

    elif vtype == "save":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        d.rounded_rectangle([46, 118, cw - 22, 335], radius=22, fill=C_GOLD + (255,))
        vbb = d.textbbox((0, 0), title[:16], font=f_sm)
        d.text((12 + (cw - (vbb[2] - vbb[0])) // 2, 205), title[:16], font=f_sm, fill=C_INK + (255,))
        d.rounded_rectangle([120, 362, cw - 96, 418], radius=26, fill=C_MAROON + (255,))
        d.text((168, 375), "Saved ✓", font=f_xs, fill=C_WHITE + (255,))

    elif vtype == "share":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        for ax, ay in [(135, 310), (cw - 115, 195)]:
            d.ellipse([ax - 28, ay - 60, ax + 28, ay - 4], fill=C_ORANGE + (255,))
            d.pieslice([ax - 52, ay + 2, ax + 52, ay + 88], 180, 360, fill=C_MAROON + (255,))
        d.line([(195, 285), (cw - 175, 215)], fill=C_ORANGE + (255,), width=7)

    elif vtype == "comment":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        d.rounded_rectangle([38, 190, cw - 14, 275], radius=38, fill=(246, 240, 230, 255), outline=C_MAROON + (255,), width=4)
        d.text((64, 218), val[:22], font=f_xs, fill=C_INK + (255,))
        d.ellipse([cw - 84, 203, cw - 26, 261], fill=C_ORANGE + (255,))

    else:
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        vfont = f_md if len(val) <= 10 else f_sm
        vbb = d.textbbox((0, 0), val[:16], font=vfont)
        d.text((12 + (cw - (vbb[2] - vbb[0])) // 2, 225), val[:16], font=vfont, fill=C_INK + (255,))

    if sub and vtype != "donut_split":
        sbb = d.textbbox((0, 0), sub, font=f_xs)
        d.text((12 + (cw - (sbb[2] - sbb[0])) // 2, ch - 42), sub, font=f_xs, fill=C_ORANGE + (255,))

    if CARD_SCALE != 1.0:
        card = card.resize((int(card.width * CARD_SCALE), int(card.height * CARD_SCALE)), Image.LANCZOS)
    canvas.alpha_composite(card, (int(cx - card.width // 2), int(cy - card.height // 2)))


def draw_diagonal_wipe(canvas, lt):
    if lt > 0.34:
        return
    p = lt / 0.34
    d = ImageDraw.Draw(canvas)
    shift = int((1.0 - ease_out_cubic(p)) * (W + 600))
    d.polygon([
        (-400 + shift, 0),
        (240 + shift, 0),
        (-120 + shift, H),
        (-760 + shift, H)
    ], fill=C_MAROON + (235,))
    d.polygon([
        (240 + shift, 0),
        (330 + shift, 0),
        (-30 + shift, H),
        (-120 + shift, H)
    ], fill=C_GOLD + (245,))


def _fit(text, max_w, start=210, floor=70, path="fonts/Poppins-Black.ttf"):
    for size in range(start, floor, -8):
        f = load_font(path, size)
        bb = _probe.textbbox((0, 0), text, font=f)
        if bb[2] - bb[0] <= max_w:
            return f
    return load_font(path, floor)


def render_cover_frame():
    """Series cover. Key content sits inside the centre 3:4 area so the profile grid crop never cuts it."""
    canvas = BG_CREAM.copy()
    d = ImageDraw.Draw(canvas)

    # series ribbon
    rib = f"{SERIES}  •  DAY {DAY}"
    f_rib = load_font("fonts/Poppins-ExtraBold.ttf", 44)
    rb = d.textbbox((0, 0), rib, font=f_rib)
    rw = rb[2] - rb[0]
    d.rounded_rectangle([W // 2 - rw // 2 - 44, 290, W // 2 + rw // 2 + 44, 380], radius=45, fill=C_MAROON + (255,))
    d.text((W // 2 - rw // 2, 300), rib, font=f_rib, fill=C_GOLD + (255,))

    # hero (1-2 lines, auto-fit, 3D)
    words = THUMB_HERO.split()
    lines = [THUMB_HERO] if (len(words) < 2 or len(THUMB_HERO) <= 9) else [" ".join(words[:len(words) // 2 or 1]), " ".join(words[len(words) // 2 or 1:])]
    y0 = 600 if len(lines) == 1 else 470
    for i, ln in enumerate(lines):
        font = _fit(ln, 900)
        bb = d.textbbox((0, 0), ln, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        x, y = W // 2 - tw // 2, y0 + i * 215
        for depth in range(14, 0, -1):
            d.text((x + depth, y + depth), ln, font=font, fill=C_MAROON_DARK + (255,))
        d.text((x, y), ln, font=font, fill=(C_ORANGE if i == len(lines) - 1 and len(lines) > 1 else C_MAROON) + (255,))

    # subtitle
    sub_words, sub_lines, cur = THUMB_SUB.split(), [], ""
    for w_ in sub_words:
        t_ = (cur + " " + w_).strip()
        if d.textbbox((0, 0), t_, font=f_sub)[2] <= 900:
            cur = t_
        else:
            sub_lines.append(cur)
            cur = w_
    if cur:
        sub_lines.append(cur)
    for li, ln in enumerate(sub_lines[:2]):
        lb = d.textbbox((0, 0), ln, font=f_sub)
        d.text((W // 2 - (lb[2] - lb[0]) // 2, 960 + li * 84), ln, font=f_sub, fill=C_INK + (255,))

    # DAY badge
    cx, cy, R = W // 2, 1395, 165
    d.ellipse([cx - R + 12, cy - R + 14, cx + R + 12, cy + R + 14], fill=C_MAROON_DARK + (255,))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=C_GOLD + (255,), outline=C_MAROON + (255,), width=10)
    f_day = load_font("fonts/Poppins-ExtraBold.ttf", 46)
    f_num = _fit(str(DAY), 230, start=190, floor=90)
    tb = d.textbbox((0, 0), "DAY", font=f_day)
    d.text((cx - (tb[2] - tb[0]) // 2, cy - 130), "DAY", font=f_day, fill=C_INK + (255,))
    nb = d.textbbox((0, 0), str(DAY), font=f_num)
    d.text((cx - (nb[2] - nb[0]) // 2, cy - 78), str(DAY), font=f_num, fill=C_MAROON + (255,))

    # badge pill
    f_b = load_font("fonts/Poppins-ExtraBold.ttf", 40)
    bb = d.textbbox((0, 0), THUMB_BADGE, font=f_b)
    bw = bb[2] - bb[0]
    d.rounded_rectangle([cx - bw // 2 - 34, 1620, cx + bw // 2 + 34, 1696], radius=38, fill=C_ORANGE + (255,))
    d.text((cx - bw // 2, 1628), THUMB_BADGE, font=f_b, fill=C_WHITE + (255,))
    return canvas


CAP_Y = 1300      # captions block (stays above Instagram's bottom UI)


def render_frame(b, lt, dur):
    is_maroon = (b.get("bg") == "maroon")
    canvas = (BG_MAROON if is_maroon else BG_CREAM).copy()
    d = ImageDraw.Draw(canvas)

    enter_t = ease_out_back(lt / 0.28)
    has_vis = (b.get("visual", "none") != "none")
    strike = (lt - 0.25) / 0.35 if b.get("strike") else 0.0
    cap_text = b.get("cap") or b.get("sub", "")
    wt = b.get("word_times")

    if has_vis:
        hero_y = 310 - int((1.0 - enter_t) * 60)
        draw_3d_hero_text(d, W // 2, hero_y, b["hero"], color_key=b.get("hero_color", "maroon"), strike_prog=strike)
        draw_dynamic_visual(canvas, W // 2, 890, b, clamp((lt - 0.10) / 0.34))
    else:
        hero_y = 620 - int((1.0 - enter_t) * 70)
        draw_3d_hero_text(d, W // 2, hero_y, b["hero"], color_key=b.get("hero_color", "maroon"), strike_prog=strike)
    draw_live_kinetic_captions(d, W // 2, CAP_Y, cap_text, b.get("pill", ""), lt, dur,
                               is_dark_bg=is_maroon, word_times=wt)

    tag = f"{SERIES}  \u2022  DAY {DAY}"
    f_tag = load_font("fonts/Poppins-ExtraBold.ttf", 30)
    tb = d.textbbox((0, 0), tag, font=f_tag)
    tw_ = tb[2] - tb[0]
    d.rounded_rectangle([W // 2 - tw_ // 2 - 26, 150, W // 2 + tw_ // 2 + 26, 206], radius=28,
                        fill=(C_GOLD if is_maroon else C_MAROON) + (255,))
    d.text((W // 2 - tw_ // 2, 156), tag, font=f_tag, fill=(C_INK if is_maroon else C_GOLD) + (255,))

    if b.get("wipe"):
        draw_diagonal_wipe(canvas, lt)

    wbb = d.textbbox((0, 0), HANDLE, font=f_xs)
    wcol = (220, 200, 190, 150) if is_maroon else (120, 95, 85, 150)
    d.text(((W - (wbb[2] - wbb[0])) // 2, 1640), HANDLE, font=f_xs, fill=wcol)

    # slow punch-in (camera push) so no beat ever feels static
    z = 1.0 + 0.045 * clamp(lt / max(0.8, dur))
    zw, zh = int(W * z), int(H * z)
    zoomed = canvas.resize((zw, zh), Image.BILINEAR)
    ox, oy = (zw - W) // 2, (zh - H) // 2
    return zoomed.crop((ox, oy, ox + W, oy + H))


total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) of V25 portrait 9:16...")

ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(FPS),
    "-i", "-", "-i", "final_audio.m4a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "final_reel.mp4"
], stdin=subprocess.PIPE)

cover_0 = render_cover_frame()
cover_0.convert("RGB").save("cover.png")

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
print("100% DONE! V25 9:16 video rendered successfully.")
