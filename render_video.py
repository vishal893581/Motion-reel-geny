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
STYLE = DNA.get("style", "theme_1")
THUMB_HOOK = DNA.get("thumbnail_hook", "SACH JAAN LO")
THUMB_BADGE = DNA.get("thumbnail_badge", "BILL EVIDENCE")

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


f_xs = load_font("fonts/Poppins-SemiBold.ttf", 24)
f_sm = load_font("fonts/Poppins-SemiBold.ttf", 32)
f_md = load_font("fonts/Poppins-ExtraBold.ttf", 46)
f_sub = load_font("fonts/Poppins-ExtraBold.ttf", 52)
f_thumb = load_font("fonts/Poppins-ExtraBold.ttf", 72)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(t):
    t = clamp(t)
    return 1 - pow(1 - t, 3)


def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158
    return 1 + (c1 + 1) * pow(t - 1, 3) + c1 * pow(t - 1, 2)


# Subtle film vignette for Theme 5
VIGNETTE = Image.new("RGBA", (W, H), (0, 0, 0, 0))
vd = ImageDraw.Draw(VIGNETTE)
for step in range(42):
    inset = step * 9
    a = int(125 * pow(1.0 - step / 42.0, 2.2))
    if a > 0:
        vd.rectangle([inset, inset, W - inset, H - inset], outline=(24, 18, 14, a), width=10)

# Theme 1: Warm Newspaper Ivory Paper (#F3EFE6) with archival grain
PAPER_BG = Image.new("RGBA", (W, H), (243, 239, 230, 255))
pd = ImageDraw.Draw(PAPER_BG)
prng = random.Random(108)
for _ in range(15000):
    gx = prng.randint(0, W - 1)
    gy = prng.randint(0, H - 1)
    v = prng.randint(226, 249)
    pd.point((gx, gy), fill=(v, v - 4, v - 13, 255))

photos = []
for sc in scenes:
    im = Image.open(sc["bg_path"]).convert("RGB").resize((1200, 2133), Image.Resampling.LANCZOS)
    photos.append(im)


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


def draw_center_text(draw, y, text, font, fill, alpha=255):
    bb = draw.textbbox((0, 0), text, font=font)
    x = (W - (bb[2] - bb[0])) // 2
    draw.text((int(x), int(y)), text, font=font, fill=fill + (alpha,))


def render_human_cover_thumbnail(sc0):
    """Frame 0 Cover Thumbnail matching Theme 1, Theme 3, or Theme 5 exact palette."""
    if STYLE == "theme_1":
        # Theme 1: Warm Newspaper (#F3EFE6) + Burnt Orange Text (#D9531E) + Yellow Highlighter (#FACC15) + Red Circle (#DC2626)
        canvas = PAPER_BG.copy()
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([330, 175, 750, 244], radius=12, outline=(220, 38, 38, 255), width=6)
        draw_center_text(d, 192, THUMB_BADGE, f_sm, (220, 38, 38))

        cut = photos[0].crop((150, 320, 1050, 1220)).resize((820, 820), Image.Resampling.LANCZOS)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([138, 328, 958, 1148], fill=(24, 18, 14, 85))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        canvas.alpha_composite(sh)
        canvas.paste(cut, (130, 315))

        d = ImageDraw.Draw(canvas)
        d.rectangle([165, 675, 915, 765], fill=(250, 204, 21, 240))
        draw_center_text(d, 694, sc0.get("highlight", "SACH DEKHO"), f_md, (20, 20, 20))
        d.ellipse([540, 655, 920, 785], outline=(220, 38, 38, 245), width=8)

        # Bold Burnt Orange hook below (user-requested orange text on newspaper theme!)
        lines = wrap_text(d, THUMB_HOOK, f_thumb, 920)[:2]
        for idx, ln in enumerate(lines):
            draw_center_text(d, 1220 + idx * 88, ln, f_thumb, (217, 83, 30))
        return canvas

    elif STYLE == "theme_3":
        # Theme 3: Charcoal Slate (#161618) + Warm Cream (#FAF5EB) + Coral Red (#EF4444)
        canvas = Image.new("RGBA", (W, H), (22, 22, 24, 255))
        pol = Image.new("RGBA", (780, 920), (250, 245, 235, 255))
        pic = photos[0].crop((180, 350, 1020, 1190)).resize((700, 700), Image.Resampling.LANCZOS)
        pol.paste(pic, (40, 42))
        pd_loc = ImageDraw.Draw(pol)
        pd_loc.text((420, 795), sc0.get("doc_tag", "Dusk, 6:14 PM"), font=f_sm, fill=(55, 55, 55, 255))
        rot_pol = pol.rotate(-3.0, resample=Image.Resampling.BICUBIC, expand=True)
        canvas.alpha_composite(rot_pol, ((W - rot_pol.width) // 2, 270))

        d = ImageDraw.Draw(canvas)
        lines = wrap_text(d, THUMB_HOOK, f_thumb, 920)[:2]
        for idx, ln in enumerate(lines):
            draw_center_text(d, 1265 + idx * 88, ln, f_thumb, (250, 245, 235))
        d.line([(280, 1455), (800, 1455)], fill=(239, 68, 68, 255), width=9)
        return canvas

    else:
        # Theme 5: Espresso Brown (#18120E) + Warm Sand (#F5EBE0) + Burnt Orange (#FB923C)
        canvas = photos[0].crop((60, 106, 60 + W, 106 + H)).convert("RGBA")
        tint = Image.new("RGBA", (W, H), (24, 18, 14, 95))
        canvas.alpha_composite(tint)
        canvas.alpha_composite(VIGNETTE)
        d = ImageDraw.Draw(canvas)
        lines = wrap_text(d, THUMB_HOOK, f_thumb, 920)[:3]
        y_start = 1140
        for idx, ln in enumerate(lines):
            col = (251, 146, 60) if idx == len(lines) - 1 else (245, 235, 224)
            draw_center_text(d, y_start + idx * 88 + 4, ln, f_thumb, (24, 18, 14), alpha=230)
            draw_center_text(d, y_start + idx * 88, ln, f_thumb, col)
        return canvas


def draw_clean_human_subtitles(canvas, sc, lt, sc_dur):
    """Box-free editorial subtitles matching Theme 1 (Orange text), Theme 3 (Cream+Coral), Theme 5 (Sand+Burnt Orange)."""
    words = sc["voice"].split()
    if not words:
        return
    hl_tokens = set(re.sub(r"[^a-zA-Z0-9₹%]", "", w).lower() for w in sc.get("highlight", "").split() if w)

    d = ImageDraw.Draw(canvas)
    lines = wrap_text(d, sc["voice"], f_sub, 920)[:3]
    total_words = len(words)
    vis_words = max(2, int(total_words * clamp((lt + 0.25) / max(0.35, sc_dur * 0.82))))

    if STYLE == "theme_1":
        # User-requested Burnt Orange primary text on Warm Newspaper Paper (#F3EFE6)
        base_txt_col = (217, 83, 30)
    elif STYLE == "theme_3":
        # Warm Cream text on Charcoal Slate (#161618)
        base_txt_col = (250, 245, 235)
    else:
        # Warm Sand Beige text on Espresso Brown (#18120E)
        base_txt_col = (245, 235, 224)

    y_base = 1350 if STYLE != "theme_5" else 1380

    word_counter = 0
    for l_idx, line in enumerate(lines):
        l_words = line.split()
        spaced = []
        tot_w = 0
        for w in l_words:
            bb = d.textbbox((0, 0), w, font=f_sub)
            ww = bb[2] - bb[0]
            spaced.append((w, ww))
            tot_w += ww + 16
        tot_w -= 16

        cx = (W - tot_w) // 2
        cy = y_base + l_idx * 72
        for w, ww in spaced:
            if word_counter < vis_words:
                clean_w = re.sub(r"[^a-zA-Z0-9₹%]", "", w).lower()
                is_hl = (clean_w in hl_tokens) or any(c.isdigit() or c in "₹%" for c in w)
                if is_hl:
                    if STYLE == "theme_1":
                        # Yellow highlighter marker + deep ink contrast on key word
                        d.rectangle([int(cx - 6), int(cy + 8), int(cx + ww + 6), int(cy + 58)], fill=(250, 204, 21, 245))
                        d.text((int(cx), int(cy)), w, font=f_sub, fill=(20, 20, 20, 255))
                    elif STYLE == "theme_3":
                        # Coral Red brush underline + Coral highlight
                        d.text((int(cx + 3), int(cy + 3)), w, font=f_sub, fill=(0, 0, 0, 230))
                        d.text((int(cx), int(cy)), w, font=f_sub, fill=(239, 68, 68, 255))
                        d.line([(int(cx), int(cy + 62)), (int(cx + ww), int(cy + 62))], fill=(239, 68, 68, 255), width=6)
                    else:
                        # Theme 5: Burnt Orange pop (#FB923C)
                        d.text((int(cx + 3), int(cy + 3)), w, font=f_sub, fill=(24, 18, 14, 240))
                        d.text((int(cx), int(cy)), w, font=f_sub, fill=(251, 146, 60, 255))
                else:
                    if STYLE != "theme_1":
                        d.text((int(cx + 3), int(cy + 3)), w, font=f_sub, fill=(15, 12, 10, 235))
                    d.text((int(cx), int(cy)), w, font=f_sub, fill=base_txt_col + (255,))
            cx += ww + 16
            word_counter += 1


def render_frame(sc_idx, sc, lt, sc_dur):
    prog = clamp(lt / max(0.1, sc_dur))
    punch = 0.045 * (1.0 - ease_out_cubic(lt / 0.24)) if lt < 0.24 else 0.0

    if STYLE == "theme_1":
        # Theme 1: Newspaper Documentary Cutout (#F3EFE6 + Orange Text + Yellow Highlighter + Red Circle)
        canvas = PAPER_BG.copy()
        scale = 1.0 + 0.08 * prog + punch
        cw, ch = int(840 / scale), int(840 / scale)
        x1 = (1200 - cw) // 2
        y1 = (2133 - ch) // 2
        cut = photos[sc_idx].crop((x1, y1, x1 + cw, y1 + ch)).resize((840, 840), Image.Resampling.BILINEAR)

        slide_y = int((1.0 - ease_out_cubic(lt / 0.25)) * 45)
        px, py = 120, 310 + slide_y

        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rectangle([px + 10, py + 14, px + 850, py + 854], fill=(24, 18, 14, 75))
        sh = sh.filter(ImageFilter.GaussianBlur(16))
        canvas.alpha_composite(sh)
        canvas.paste(cut, (px, py))

        d = ImageDraw.Draw(canvas)
        eff = sc.get("effect", "yellow_highlight")
        hp = ease_out_cubic((lt - 0.18) / 0.35)
        if hp > 0.05 and sc.get("highlight"):
            hl_txt = sc["highlight"]
            bb = d.textbbox((0, 0), hl_txt, font=f_md)
            hw = bb[2] - bb[0]
            bx1 = (W - hw) // 2 - 26
            bx2 = bx1 + int((hw + 52) * hp)
            by1 = py + 660
            if eff in ("yellow_highlight", "highlighter_circle"):
                d.rectangle([bx1, by1, max(bx1 + 10, bx2), by1 + 76], fill=(250, 204, 21, 240))
                if hp > 0.65:
                    draw_center_text(d, by1 + 12, hl_txt, f_md, (20, 20, 20))
            if eff in ("red_circle", "highlighter_circle") and hp > 0.5:
                d.ellipse([bx1 - 18, by1 - 14, (W + hw) // 2 + 44, by1 + 90], outline=(220, 38, 38, 245), width=7)

        d.text((px + 540, py + 862), sc.get("doc_tag", "BILL EVIDENCE"), font=f_xs, fill=(95, 90, 82, 220))
        draw_clean_human_subtitles(canvas, sc, lt, sc_dur)
        return canvas

    elif STYLE == "theme_3":
        # Theme 3: Charcoal Slate (#161618) + Tilted Polaroid + Cream & Coral Red Typography
        canvas = Image.new("RGBA", (W, H), (22, 22, 24, 255))
        scale = 1.0 + 0.07 * prog + punch
        cw, ch = int(700 / scale), int(700 / scale)
        x1 = (1200 - cw) // 2
        y1 = (2133 - ch) // 2
        pic = photos[sc_idx].crop((x1, y1, x1 + cw, y1 + ch)).resize((700, 700), Image.Resampling.BILINEAR)

        pol = Image.new("RGBA", (780, 910), (250, 245, 235, 255))
        pol.paste(pic, (40, 42))
        pd_loc = ImageDraw.Draw(pol)
        pd_loc.text((440, 790), sc.get("doc_tag", "POV"), font=f_sm, fill=(65, 65, 65, 255))

        tilt = -2.8 if sc_idx % 2 == 0 else 2.5
        rot_pol = pol.rotate(tilt, resample=Image.Resampling.BICUBIC, expand=True)
        drop_y = int((1.0 - ease_out_back(lt / 0.28)) * 40)
        canvas.alpha_composite(rot_pol, ((W - rot_pol.width) // 2, 265 + drop_y))

        draw_clean_human_subtitles(canvas, sc, lt, sc_dur)
        return canvas

    else:
        # Theme 5: Espresso Brown (#18120E) + Full-Bleed 35mm Candid Film + Warm Sand & Burnt Orange Text
        scale = 1.0 + 0.09 * prog + punch
        cw, ch = int(W / scale), int(H / scale)
        x1 = int((1200 - cw) * (0.35 + 0.30 * prog)) if sc_idx % 2 == 1 else (1200 - cw) // 2
        y1 = (2133 - ch) // 2
        cropped = photos[sc_idx].crop((x1, y1, x1 + cw, y1 + ch)).resize((W, H), Image.Resampling.BILINEAR)
        canvas = cropped.convert("RGBA")
        tint = Image.new("RGBA", (W, H), (24, 18, 14, 70))
        canvas.alpha_composite(tint)
        canvas.alpha_composite(VIGNETTE)
        draw_clean_human_subtitles(canvas, sc, lt, sc_dur)
        return canvas


total_frames = math.ceil(total_dur * FPS)
print(f"Rendering {total_frames} frames ({total_dur}s) of V20 Human Style [{STYLE}]...")

ffmpeg = subprocess.Popen([
    "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{W}x{H}", "-pix_fmt", "rgba", "-r", str(FPS),
    "-i", "-", "-i", "final_audio.m4a",
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "final_reel.mp4"
], stdin=subprocess.PIPE)

cover_0 = render_human_cover_thumbnail(scenes[0])

for frame in range(total_frames):
    if frame == 0:
        ffmpeg.stdin.write(cover_0.tobytes())
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
    frame_img = render_frame(sc_idx, active_sc, lt, active_sc["duration"])
    ffmpeg.stdin.write(frame_img.tobytes())

    if frame % 300 == 0:
        print(f"Rendered {frame}/{total_frames} frames...")

ffmpeg.stdin.close()
ffmpeg.wait()
print("100% DONE! V20 Reel rendered successfully.")
