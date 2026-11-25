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

W, H = 1920, 1080
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


f_xs = load_font("fonts/Poppins-Bold.ttf", 22)
f_sm = load_font("fonts/Poppins-Bold.ttf", 29)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", 42)
f_sub = load_font("fonts/Poppins-Bold.ttf", 46)
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


def choose_hero_font(text):
    n = len(text)
    if n <= 6:
        return f_hero_lg
    elif n <= 10:
        return f_hero_md
    return f_hero_sm


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


def draw_pill_subtitle(draw, cx, cy, sub_text, pill_word, is_dark_bg=False, max_w=860):
    words = sub_text.split()
    if not words:
        return
    pill_clean = pill_word.strip().lower()

    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if draw.textbbox((0, 0), test, font=f_sub)[2] <= max_w:
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
        y = int(cy + l_idx * 72)
        for w, ww, is_p, pad in items:
            if is_p:
                draw.rounded_rectangle([x, y - 6, x + ww + pad, y + 60], radius=28, fill=pill_bg + (255,))
                draw.text((x + pad // 2, y), w, font=f_sub, fill=pill_fg + (255,))
            else:
                draw.text((x, y), w, font=f_sub, fill=txt_col + (255,))
            x += ww + pad + 16


def draw_card_shell(d, cw, ch, title, use_gold_hdr=False):
    d.rounded_rectangle([20, 24, cw + 20, ch + 24], radius=30, fill=(35, 15, 10, 48))
    d.rounded_rectangle([12, 12, cw + 12, ch + 12], radius=30, fill=C_WHITE + (255,), outline=(218, 206, 188, 255), width=4)
    hdr_col = C_GOLD if use_gold_hdr else C_MAROON
    hdr_txt = C_INK if use_gold_hdr else C_WHITE
    d.rounded_rectangle([34, 30, cw - 10, 86], radius=16, fill=hdr_col + (255,))
    tbb = d.textbbox((0, 0), title, font=f_xs)
    d.text((12 + (cw - (tbb[2] - tbb[0])) // 2, 43), title, font=f_xs, fill=hdr_txt + (255,))


def draw_dynamic_visual(canvas, cx, cy, b, pop_t):
    """18 distinct script-matched vector illustrations & diagrams using exact Maroon/Orange/Gold/Cream palette."""
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

    # 1. Floating Donut / Ring Breakdown (no generic white box — direct floating diagram!)
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
        # Legend pills below ring
        cols = [C_MAROON, C_ORANGE, C_GOLD]
        for idx, pt in enumerate(parts[:3]):
            lx = 24 + idx * ((cw - 20) // 3)
            d.rounded_rectangle([lx, 405, lx + (cw - 36) // 3, 456], radius=14, fill=cols[idx] + (255,))
            fg = C_INK if idx == 2 else C_WHITE
            d.text((lx + 12, 417), pt[:11], font=f_xs, fill=fg + (255,))

    # 2. Upward Growth Bar Chart (Compounding / Income / Progress)
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

    # 3. Wallet / Salary Drain Meter
    elif vtype == "wallet_empty":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        parts = val.split("|") if "|" in val else ["₹30,000", "₹420"]
        d.text((52, 125), f"Start: {parts[0].strip()[:12]}", font=f_sm, fill=C_INK + (255,))
        d.rounded_rectangle([52, 175, cw - 32, 225], radius=16, fill=(235, 226, 212, 255))
        rem_w = max(28, int((cw - 84) * (1.0 - 0.88 * clamp(pop_t))))
        d.rounded_rectangle([52, 175, 52 + rem_w, 225], radius=16, fill=C_ORANGE + (255,))
        d.text((52, 265), f"Left: {parts[1].strip()[:12]}", font=f_md, fill=C_MAROON + (255,))

    # 4. Coin / Wealth Stack Comparison
    elif vtype == "coin_stack":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        parts = val.split("|") if "|" in val else ["₹6L", "₹12.4L"]
        # Left small stack, Right tall gold stack
        for c in range(3):
            cy_s = 360 - c * 28
            d.ellipse([85, cy_s, 195, cy_s + 24], fill=C_MAROON + (255,), outline=C_WHITE, width=2)
        d.text((70, 400), parts[0].strip()[:14], font=f_xs, fill=C_INK + (255,))
        tall_n = max(1, int(7 * clamp(pop_t)))
        for c in range(tall_n):
            cy_s = 360 - c * 28
            d.ellipse([275, cy_s, 395, cy_s + 24], fill=C_GOLD + (255,), outline=C_ORANGE, width=2)
        d.text((260, 400), parts[1].strip()[:14], font=f_xs, fill=C_MAROON + (255,))

    # 5. Microphone & Voice/Heartbeat Waveform
    elif vtype == "mic_wave":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        mcx = 12 + cw // 2
        d.rounded_rectangle([mcx - 28, 120, mcx + 28, 220], radius=26, fill=C_MAROON + (255,))
        d.arc([mcx - 46, 150, mcx + 46, 240], 0, 180, fill=C_ORANGE + (255,), width=6)
        d.line([(mcx, 240), (mcx, 278)], fill=C_INK + (255,), width=6)
        # Animated soundwave bars
        wave_h = [24, 52, 80, 42, 92, 60, 30, 74, 46, 26]
        for i, wh in enumerate(wave_h):
            wx = 65 + i * 35
            anim_h = int(wh * (0.5 + 0.5 * abs(math.sin(pop_t * 5 + i))))
            d.rounded_rectangle([wx, 345 - anim_h // 2, wx + 18, 345 + anim_h // 2], radius=8, fill=C_ORANGE if i % 2 == 0 else C_MAROON)
        d.text((135, 405), val[:18], font=f_sm, fill=C_MAROON + (255,))

    # 6. Eye-Contact / 3-Point Focus Triangle
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

    # 7. 4-Quadrant Breakdown Grid
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

    # 8. Speaker Avatar + Speech Bubble
    elif vtype == "bubble":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        ax, ay = 105, 285
        d.ellipse([ax - 34, ay - 72, ax + 34, ay - 4], fill=C_ORANGE + (255,))
        d.pieslice([ax - 62, ay + 6, ax + 62, ay + 110], 180, 360, fill=C_MAROON + (255,))
        d.rounded_rectangle([185, 165, cw - 18, 290], radius=26, fill=(246, 240, 230, 255), outline=C_MAROON + (255,), width=4)
        d.polygon([(185, 220), (160, 235), (185, 250)], fill=C_MAROON + (255,))
        d.text((206, 210), val[:22], font=f_xs, fill=C_INK + (255,))

    # 9. Animated Tick Checklist
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

    # 10. Side-by-Side Comparison
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

    # 11. Analog Clock
    elif vtype == "clock":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=True)
        ocx, ocy, rad = 12 + cw // 2, 260, 120
        d.ellipse([ocx - rad, ocy - rad, ocx + rad, ocy + rad], fill=(252, 248, 240, 255), outline=C_ORANGE + (255,), width=14)
        ang = -math.pi / 3 + pop_t * 1.4
        d.line([(ocx, ocy), (ocx + int(82 * math.cos(ang)), ocy + int(82 * math.sin(ang)))], fill=C_MAROON + (255,), width=8)
        d.line([(ocx, ocy), (ocx, ocy - 64)], fill=C_INK + (255,), width=8)
        d.ellipse([ocx - 10, ocy - 10, ocx + 10, ocy + 10], fill=C_ORANGE + (255,))

    # 12. Phone Illustration
    elif vtype == "phone":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        px1, px2 = 12 + cw // 2 - 90, 12 + cw // 2 + 90
        d.rounded_rectangle([px1, 115, px2, 415], radius=26, fill=(32, 24, 22, 255), outline=C_MAROON + (255,), width=6)
        d.rounded_rectangle([px1 + 14, 145, px2 - 14, 385], radius=16, fill=(246, 238, 226, 255))
        d.text((px1 + 28, 240), val[:12], font=f_xs, fill=C_MAROON + (255,))

    # 13. Crossed-Out Mistake Warning
    elif vtype == "trap_cross":
        draw_card_shell(d, cw, ch, title, use_gold_hdr=False)
        vbb = d.textbbox((0, 0), val[:18], font=f_sm)
        d.text((12 + (cw - (vbb[2] - vbb[0])) // 2, 230), val[:18], font=f_sm, fill=C_MAROON + (255,))
        if pop_t > 0.25:
            p = clamp((pop_t - 0.25) / 0.5)
            d.line([(55, 130), (55 + int((cw - 90) * p), 130 + int(260 * p))], fill=C_ORANGE + (255,), width=14)
            d.line([(cw - 35, 130), (cw - 35 - int((cw - 90) * p), 130 + int(260 * p))], fill=C_ORANGE + (255,), width=14)

    # 14. Save / Share / Comment CTA Visuals
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


def render_cover_frame():
    canvas = BG_CREAM.copy()
    d = ImageDraw.Draw(canvas)
    draw_3d_hero_text(d, 580, 440, THUMB_HERO, color_key="maroon")
    draw_pill_subtitle(d, 580, 620, THUMB_SUB, THUMB_SUB.split()[0], is_dark_bg=False, max_w=780)
    fake_b = {"visual": "timer", "v_title": "MUST WATCH", "v_data": THUMB_BADGE, "v_sub": "@sochbadlo.hq"}
    draw_dynamic_visual(canvas, 1420, 540, fake_b, 1.0)
    return canvas


def render_frame(b, lt, dur):
    is_maroon = (b.get("bg") == "maroon")
    canvas = (BG_MAROON if is_maroon else BG_CREAM).copy()
    d = ImageDraw.Draw(canvas)

    enter_t = ease_out_back(lt / 0.28)
    has_vis = (b.get("visual", "none") != "none")

    if has_vis:
        left_mode = (b["index"] % 2 == 0)
        hero_x = 580 if left_mode else 1340
        vis_x = 1420 if left_mode else 500
        hero_y = 430 - int((1.0 - enter_t) * 45)
        draw_3d_hero_text(
            d, hero_x, hero_y, b["hero"],
            color_key=b.get("hero_color", "maroon"),
            strike_prog=(lt - 0.25) / 0.35 if b.get("strike") else 0.0
        )
        draw_pill_subtitle(d, hero_x, hero_y + 165, b["sub"], b["pill"], is_dark_bg=is_maroon, max_w=820)
        draw_dynamic_visual(canvas, vis_x, 540, b, clamp((lt - 0.10) / 0.34))
    else:
        hero_y = 450 - int((1.0 - enter_t) * 50)
        draw_3d_hero_text(
            d, W // 2, hero_y, b["hero"],
            color_key=b.get("hero_color", "maroon"),
            strike_prog=(lt - 0.25) / 0.35 if b.get("strike") else 0.0
        )
        draw_pill_subtitle(d, W // 2, hero_y + 175, b["sub"], b["pill"], is_dark_bg=is_maroon, max_w=1200)

    if b.get("wipe"):
        draw_diagonal_wipe(canvas, lt)

    wbb = d.textbbox((0, 0), "@sochbadlo.hq", font=f_xs)
    wcol = (220, 200, 190, 150) if is_maroon else (120, 95, 85, 150)
    d.text(((W - (wbb[2] - wbb[0])) // 2, H - 56), "@sochbadlo.hq", font=f_xs, fill=wcol)
    return canvas


total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) of V23 Script-Matched Motion Graphics...")

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
print("100% DONE! V23 Video rendered successfully.")
