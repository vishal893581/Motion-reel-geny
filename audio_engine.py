import sys
import subprocess
import json
import os
import time
import re
import random
import urllib.parse
import requests

raw_topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "cute_viral"

rng = random.SystemRandom()

TRENDING_VIRAL_TOPICS = [
    "Kisi Ka Bhi Jhooth 5 Second Mein Kaise Pakdein",
    "Chup Rehne Ki Power: Kam Bolkar Logon Ko Apna Deewana Kaise Banayein",
    "Ratan Tata Ka Woh Ek Rule Jo Har Middle Class Ko Sikhna Chahiye",
    "Ameer Log Apni Salary Aate Hi Sabse Pehle Kya Karte Hain",
    "Mobile Charging Ki Woh Galti Jo Aapke Phone Ko Andar Se Kharab Kar Rahi Hai",
    "Neend Na Aane Par Dimaag Ko 2 Minute Mein Shant Karne Ki Military Trick",
    "Dark Psychology: Pehli Mulakat Mein Kisi Ka Bhi Dil Kaise Jeetein",
    "Overthinking Ko 60 Second Mein Rokne Ki Navy SEAL Breathing Trick",
    "Duniya Ke Sabse Amir Log Subah Uthkar Yeh 2 Kaam Kabhi Nahi Karte",
    "Kisi Bhi Conversation Mein Samne Wale Ko Apni Baat Manwane Ki Trick",
    "Instagram Aur Reels Ki Lat Chhodne Ka Sabse Aasan 48-Hour Reset",
    "Aapka Phone Chupke Se Aapki Baatein Kaise Sunta Hai Aur Kaise Rokein",
    "Middle Class Trap: EMI Aur Credit Card Se Bachne Ka Real Formula",
    "Body Language Secret: Bina Bole Room Mein Sabse Confident Kaise Dikhein",
    "Warren Buffett Ka 5-25 Rule Jo Aapki Life Ka Focus Badal Dega",
    "Log Aapko For Granted Kyun Lete Hain Aur Isse Turant Kaise Badlein"
]

topic = raw_topic if raw_topic else rng.choice(TRENDING_VIRAL_TOPICS)
print(f"Selected Viral Topic: {topic}")

PRO_PALETTES = [
    {
        "name": "apple_titanium_light",
        "is_light": True,
        "bg": [246, 248, 252],
        "bg_alt": [232, 238, 248],
        "card": [255, 255, 255],
        "card_border": [216, 224, 238],
        "text_main": [15, 23, 42],
        "text_muted": [100, 116, 139],
        "accent": [37, 99, 235],
        "secondary": [245, 158, 11],
        "positive": [16, 185, 129],
        "negative": [239, 68, 68]
    },
    {
        "name": "warm_editorial_cream",
        "is_light": True,
        "bg": [250, 247, 242],
        "bg_alt": [242, 235, 224],
        "card": [255, 254, 251],
        "card_border": [228, 218, 204],
        "text_main": [28, 25, 23],
        "text_muted": [120, 113, 108],
        "accent": [217, 70, 39],
        "secondary": [202, 138, 4],
        "positive": [21, 128, 61],
        "negative": [185, 28, 28]
    },
    {
        "name": "midnight_aurora_pro",
        "is_light": False,
        "bg": [11, 15, 28],
        "bg_alt": [18, 25, 46],
        "card": [20, 27, 48],
        "card_border": [46, 58, 92],
        "text_main": [248, 250, 252],
        "text_muted": [148, 163, 184],
        "accent": [56, 189, 248],
        "secondary": [251, 191, 36],
        "positive": [52, 211, 153],
        "negative": [251, 113, 133]
    },
    {
        "name": "obsidian_rose_gold",
        "is_light": False,
        "bg": [15, 13, 18],
        "bg_alt": [28, 22, 34],
        "card": [26, 23, 32],
        "card_border": [62, 54, 76],
        "text_main": [250, 248, 252],
        "text_muted": [168, 162, 178],
        "accent": [244, 63, 94],
        "secondary": [253, 224, 71],
        "positive": [52, 211, 153],
        "negative": [248, 113, 113]
    },
    {
        "name": "emerald_wealth_studio",
        "is_light": False,
        "bg": [9, 20, 18],
        "bg_alt": [15, 34, 30],
        "card": [16, 36, 32],
        "card_border": [36, 74, 66],
        "text_main": [240, 253, 250],
        "text_muted": [148, 184, 176],
        "accent": [16, 185, 129],
        "secondary": [250, 204, 21],
        "positive": [52, 211, 153],
        "negative": [248, 113, 113]
    }
]

WIDGET_POOL = [
    "radar_scanner",
    "vs_clash_cards",
    "animated_bar_chart",
    "floating_checklist",
    "circular_gauge",
    "waveform_pulse_card"
]
scene_widgets = rng.sample(WIDGET_POOL, 6)

edit_dna = {
    "palette": rng.choice(PRO_PALETTES),
    "widgets": scene_widgets,
    "bg_style": rng.choice(["soft_mesh_grid", "floating_bokeh_rings", "diagonal_architectural"]),
    "transition": rng.choice(["smooth_curtain", "iris_reveal", "prism_wipe"])
}

print(f"Chosen Studio Palette: {edit_dna['palette']['name']} | Light Mode: {edit_dna['palette']['is_light']}")

def build_prompt(topic_str):
    lines = [
        "You are India's #1 viral Instagram Reel scriptwriter & motion graphics director.",
        f'Topic: "{topic_str}"',
        "",
        "Write an addictive, high-retention 6-scene Hinglish Reel script (strictly 32 to 38 seconds total -> 11 to 14 words per scene, ~75 words total).",
        "",
        "STRICT RULES:",
        "1. Scene 1 MUST be a shocking scroll-stopping hook. Never use Hello friends or Aaj hum baat karenge.",
        "2. Every scene must deliver concrete, sharp, real-world value about the topic.",
        "3. Write 100% NATURAL, EASY, GRAMMATICALLY CLEAN spoken Hinglish (NO gibberish, NO broken English).",
        "4. Spell Hindi words phonetically for Indian TTS ('isse', 'hee', 'logon', 'kyunki', 'samajhiye').",
        "5. For EACH scene, also return motion-graphic data so the editor can animate live UI cards, charts, and comparisons on screen:",
        "   - kicker: 2-3 word top badge",
        "   - headline: 3-5 word bold title",
        "   - metric_big: A punchy 2-6 char hero stat/word (e.g. '5 SEC', '87%', 'TRAP', 'RULE #1', '2X FAST', 'SAVE')",
        "   - metric_label: Short 2-3 word label under the big stat",
        "   - left_label: Short comparison/point A (max 16 chars)",
        "   - right_label: Short comparison/point B (max 16 chars)",
        "   - pct: Integer between 74 and 98",
        "   - image_prompt: Vivid vertical 9:16 photorealistic cinematic background in English (clean aesthetic, soft depth of field, 8k, no text).",
        "",
        "Return ONLY valid JSON with key 'scenes' containing 6 objects."
    ]
    return "\n".join(lines)

def generate_ai_script(topic_str):
    prompt = build_prompt(topic_str)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            resp = requests.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}
                },
                timeout=30
            )
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data = json.loads(raw)
            if "scenes" in data and len(data["scenes"]) == 6:
                print("Script + Motion Graphics Data generated via Gemini 2.5 Flash!")
                return data
        except Exception as e:
            print("Gemini API skip:", e)

    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.9},
                timeout=30
            )
            raw = resp.json()["choices"][0]["message"]["content"]
            raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data = json.loads(raw)
            if "scenes" in data and len(data["scenes"]) == 6:
                print("Script generated via OpenAI API!")
                return data
        except Exception as e:
            print("OpenAI API skip:", e)

    return {
        "scenes": [
            {"voice": f"Kya aap jaante hain {topic_str} ke peeche ka asli psychological raaz kya hai?", "kicker": "SHOCKING TRUTH", "headline": "Asli Raaz Kya Hai?", "metric_big": "92%", "metric_label": "LOG IGNORE KARTE HAIN", "left_label": "Aam Soch", "right_label": "Asli Sach", "pct": 92, "image_prompt": "Minimalist modern luxury studio architecture with soft sunlight shadows, 8k, no text"},
            {"voice": "Zyaadatar log bina soche samjhe wahi purani galti baar-baar dohrate rehte hain.", "kicker": "COMMON TRAP", "headline": "Yeh Galti Mat Karo", "metric_big": "TRAP", "metric_label": "90% LOG PHASTE HAIN", "left_label": "Purana Tareeka", "right_label": "Smart Shift", "pct": 84, "image_prompt": "Close up of sleek glass chess pieces on minimalist marble table, soft bokeh, 8k, no text"},
            {"voice": "Lekin jo log sahi pattern samajh lete hain, unka control har situation par hota hai.", "kicker": "MINDSET SHIFT", "headline": "Pattern Samajhna Seekho", "metric_big": "3X", "metric_label": "FASTER CLARITY", "left_label": "Blind Reaction", "right_label": "Calm Control", "pct": 91, "image_prompt": "Clean futuristic minimalist workspace with warm ambient lighting, 8k, no text"},
            {"voice": "Jab aap sahi waqt par sahi kadam uthate hain, toh sab kuch aapke haq mein hota hai.", "kicker": "POWER MOVE", "headline": "Sahi Waqt Aur Faisla", "metric_big": "5 SEC", "metric_label": "DECISION WINDOW", "left_label": "Overthinking", "right_label": "Instant Action", "pct": 95, "image_prompt": "Golden hour light rays over modern city skyline, serene aesthetic, 8k, no text"},
            {"voice": "Isse aapka confidence badhta hai aur log aapki baaton ko gambhirta se sunte hain.", "kicker": "REAL RESULT", "headline": "Confidence Aur Respect", "metric_big": "97%", "metric_label": "HIGH IMPACT SCORE", "left_label": "Self Doubt", "right_label": "Unshakable", "pct": 97, "image_prompt": "Elegant golden hourglass on clean stone pedestal, soft studio lighting, 8k, no text"},
            {"voice": "Agar yeh baat kaam ki lagi ho, toh iss reel ko abhi save zaroor karein!", "kicker": "SAVE & SHARE", "headline": "Abhi Save Karein", "metric_big": "SAVE", "metric_label": "DAILY REMINDER", "left_label": "Scroll Past", "right_label": "Apply Today", "pct": 99, "image_prompt": "Sleek metallic compass on minimalist surface with soft warm glow, 8k, no text"}
        ]
    }

def generate_scene_visuals(scenes_list):
    os.makedirs("bg_assets", exist_ok=True)
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()
    pal = edit_dna["palette"]
    is_light = pal["is_light"]

    for idx, sc in enumerate(scenes_list):
        out_img = f"bg_assets/bg_{idx}.jpg"
        prompt = sc.get("image_prompt", "clean aesthetic studio architecture 8k")
        saved = False

        if not is_light:
            encoded = urllib.parse.quote(prompt + ", vertical 9:16, soft bokeh, 8k, no text")
            seed = rng.randint(1, 999999)
            try:
                r = requests.get(f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&seed={seed}&nologo=true", timeout=24)
                if r.status_code == 200 and len(r.content) > 14000:
                    with open(out_img, "wb") as f:
                        f.write(r.content)
                    saved = True
                    print(f"Downloaded Studio B-Roll {idx+1}/6")
            except Exception as e:
                print(f"B-roll fetch skip {idx+1}:", e)

        if not saved and pexels_key:
            try:
                q = urllib.parse.quote(" ".join(prompt.split()[:3]))
                r = requests.get(
                    f"https://api.pexels.com/v1/search?query={q}&orientation=portrait&per_page=5",
                    headers={"Authorization": pexels_key},
                    timeout=15
                )
                photos = r.json().get("photos", [])
                if photos:
                    p_url = rng.choice(photos)["src"]["large2x"]
                    with open(out_img, "wb") as f:
                        f.write(requests.get(p_url, timeout=20).content)
                    saved = True
                    print(f"Downloaded Pexels HD visual {idx+1}/6")
            except Exception as e:
                print("Pexels skip:", e)

        if not saved:
            from PIL import Image, ImageDraw, ImageFilter
            bg_c = tuple(pal["bg"])
            ac = tuple(pal["accent"])
            sc_c = tuple(pal["secondary"])

            base = Image.new("RGB", (768, 1344), bg_c)
            gd = ImageDraw.Draw(base)
            if is_light:
                orb1 = tuple(int(bg_c[i] * 0.78 + ac[i] * 0.22) for i in range(3))
                orb2 = tuple(int(bg_c[i] * 0.80 + sc_c[i] * 0.20) for i in range(3))
                grid_c = tuple(int(bg_c[i] * 0.91) for i in range(3))
            else:
                orb1 = tuple(int(bg_c[i] * 0.65 + ac[i] * 0.35) for i in range(3))
                orb2 = tuple(int(bg_c[i] * 0.72 + sc_c[i] * 0.28) for i in range(3))
                grid_c = tuple(min(255, int(bg_c[i] + 18)) for i in range(3))

            gd.ellipse([rng.randint(-120, 120), rng.randint(-80, 180), rng.randint(520, 820), rng.randint(520, 820)], fill=orb1)
            gd.ellipse([rng.randint(80, 320), rng.randint(680, 920), rng.randint(620, 880), rng.randint(1180, 1450)], fill=orb2)
            im = base.filter(ImageFilter.GaussianBlur(115))
            dr = ImageDraw.Draw(im)

            for gx in range(0, 768, 56):
                dr.line([(gx, 0), (gx, 1344)], fill=grid_c, width=1)
            for gy in range(0, 1344, 56):
                dr.line([(0, gy), (768, gy)], fill=grid_c, width=1)
            for rad in range(160, 520, 110):
                dr.ellipse([384 - rad, 672 - rad, 384 + rad, 672 + rad], outline=grid_c, width=2)

            im.save(out_img, quality=94)
            print(f"Generated Designer Studio Canvas {idx+1}/6")

script_obj = generate_ai_script(topic)
scenes_data = script_obj["scenes"]
generate_scene_visuals(scenes_data)

sfx_bank_plan = [
    [{"type": "rise", "offset": 0.05}, {"type": "pop", "offset": 0.8}, {"type": "whoosh", "offset": 2.2}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "impact", "offset": 1.1}, {"type": "pop", "offset": 2.1}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 0.9}, {"type": "pop", "offset": 1.9}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "impact", "offset": 1.2}, {"type": "ping", "offset": 2.2}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 1.0}, {"type": "pop", "offset": 2.0}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "impact", "offset": 1.5}]
]

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())

def generate_sfx_bank():
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.35:c=pink:a=0.45", "-af", "bandpass=f=850:width_type=h:w=1200,afade=t=in:ss=0:d=0.08,afade=t=out:st=0.14:d=0.21", "sfx_whoosh.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=780:d=0.10", "-af", "asetrate=44100*0.68,aresample=44100,afade=t=out:st=0.02:d=0.08,volume=0.60", "sfx_pop.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=75:d=0.38", "-af", "afade=t=out:st=0.04:d=0.34,volume=1.0", "sfx_impact.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1174:d=0.22", "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.05:d=0.17,volume=0.50", "sfx_ping.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.30", "-af", "highpass=f=600,afade=t=in:ss=0:d=0.35,afade=t=out:st=0.35:d=0.10", "sfx_rise.wav"], check=True)

def run_edge_tts_with_retry(text, out_file):
    voice_name = "hi-IN-SwaraNeural" if voice_style == "cute_viral" else "hi-IN-MadhurNeural"
    rate = "+16%"
    pitch = "+10Hz" if voice_style == "cute_viral" else "-2Hz"
    for attempt in range(5):
        res = subprocess.run([
            "edge-tts", "--voice", voice_name,
            "--rate", rate, "--pitch", pitch,
            "--text", text, "--write-media", out_file
        ])
        if res.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 500:
            return
        print(f"TTS retry {attempt + 1}/5 for {out_file}...")
        time.sleep(2.0)
    raise RuntimeError(f"Failed to generate {out_file} after 5 attempts")

generate_sfx_bank()

timeline = []
current_time = 0.0
voice_files = []
sfx_inputs = []
filter_complex = []
sfx_counter = 0

for idx, sc in enumerate(scenes_data):
    v_file = f"voice_{idx}.mp3"
    raw_v = f"raw_voice_{idx}.mp3"
    run_edge_tts_with_retry(sc["voice"], raw_v)
    time.sleep(0.8)

    af_str = "highpass=f=90,equalizer=f=220:width_type=h:width=120:g=3,equalizer=f=3400:width_type=h:width=1600:g=3.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50"
    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)

    dur = get_duration(v_file) + 0.15
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "index": idx,
        "start": round(current_time, 3),
        "duration": round(dur, 3),
        "voice": sc["voice"],
        "kicker": sc.get("kicker", "INSIGHT"),
        "headline": sc.get("headline", ""),
        "metric_big": sc.get("metric_big", "95%"),
        "metric_label": sc.get("metric_label", "PROVEN IMPACT"),
        "left_label": sc.get("left_label", "Old Way"),
        "right_label": sc.get("right_label", "Smart Way"),
        "pct": int(sc.get("pct", 92)),
        "widget": scene_widgets[idx],
        "bg_path": f"bg_assets/bg_{idx}.jpg"
    })

    for s in sfx_bank_plan[idx]:
        offset = min(s["offset"], max(0.05, dur - 0.25))
        sfx_time_ms = int((current_time + offset) * 1000)
        sfx_inputs.extend(["-i", f"sfx_{s['type']}.wav"])
        sfx_counter += 1
        filter_complex.append(f"[{sfx_counter}:a]adelay={sfx_time_ms}|{sfx_time_ms}[s{sfx_counter}]")

    current_time += dur

with open("vlist.txt", "w") as f:
    for vf in voice_files:
        f.write(f"file '{vf}'\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "vlist.txt", "full_voice.wav"], check=True)

bass_hz = rng.choice([55, 65, 73])
subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi",
    "-i", f"aevalsrc=0.055*sin(2*PI*{bass_hz}*t)*(0.5+0.5*sin(2*PI*4*t))+0.025*sin(2*PI*{bass_hz*4}*t)*(0.5+0.5*sin(2*PI*2*t))+0.015*sin(2*PI*{bass_hz*6}*t)*(0.5+0.5*cos(2*PI*2*t)):d={current_time+1}",
    "-af", "lowpass=f=420,afade=t=in:ss=0:d=0.5,afade=t=out:st=" + str(max(0.5, current_time - 0.5)) + ":d=0.5",
    "bgm.wav"
], check=True)

bgm_idx = sfx_counter + 1
sfx_inputs.extend(["-i", "bgm.wav"])
mix_inputs = "".join([f"[s{i}]" for i in range(1, sfx_counter + 1)]) + f"[{bgm_idx}:a]"
filter_str = ";".join(filter_complex) + f";[0:a]{mix_inputs}amix=inputs={sfx_counter+2}:duration=first:normalize=0[out]"

subprocess.run([
    "ffmpeg", "-y", "-i", "full_voice.wav", *sfx_inputs,
    "-filter_complex", filter_str, "-map", "[out]", "final_audio.m4a"
], check=True)

with open("timeline.json", "w") as f:
    json.dump({
        "total_duration": round(current_time, 3),
        "edit_dna": edit_dna,
        "scenes": timeline
    }, f, indent=2)

print(f"V11 Pro Studio Ready! Palette: {edit_dna['palette']['name']} | Duration: {round(current_time, 2)}s")
