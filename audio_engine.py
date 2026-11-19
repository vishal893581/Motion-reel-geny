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
    "Log Aapko For Granted Kyun Lete Hain Aur Isse Turant Kaise Badlein",
    "Subconscious Mind Reprogramming: Sone Se Pehle Ke 5 Minute Ka Jaadu",
    "Duniya Ke Top 1% Logon Ki Communication Habit Jo Unhe Har Jagah Jeetati Hai"
]

topic = raw_topic if raw_topic else rng.choice(TRENDING_VIRAL_TOPICS)
print(f"Selected Viral Topic: {topic}")

PRO_PALETTES = [
    {
        "name": "apple_titanium_light",
        "is_light": True,
        "bg": [244, 247, 252],
        "card": [255, 255, 255],
        "card_border": [212, 222, 238],
        "text_main": [15, 23, 42],
        "text_muted": [95, 112, 136],
        "accent": [37, 99, 235],
        "secondary": [245, 158, 11],
        "positive": [16, 185, 129],
        "negative": [239, 68, 68]
    },
    {
        "name": "warm_editorial_cream",
        "is_light": True,
        "bg": [250, 246, 240],
        "card": [255, 254, 250],
        "card_border": [228, 216, 200],
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
        "bg": [10, 14, 26],
        "card": [18, 25, 46],
        "card_border": [46, 62, 98],
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
        "bg": [14, 11, 18],
        "card": [25, 21, 32],
        "card_border": [64, 54, 80],
        "text_main": [250, 248, 252],
        "text_muted": [168, 162, 178],
        "accent": [244, 63, 94],
        "secondary": [253, 224, 71],
        "positive": [52, 211, 153],
        "negative": [248, 113, 113]
    },
    {
        "name": "cyber_violet_neon",
        "is_light": False,
        "bg": [12, 9, 24],
        "card": [24, 19, 44],
        "card_border": [62, 48, 104],
        "text_main": [248, 246, 255],
        "text_muted": [165, 158, 196],
        "accent": [168, 85, 247],
        "secondary": [250, 204, 21],
        "positive": [52, 211, 153],
        "negative": [244, 63, 94]
    },
    {
        "name": "emerald_wealth_studio",
        "is_light": False,
        "bg": [8, 19, 17],
        "card": [15, 34, 30],
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
    "stock_line_graph",
    "animated_bar_chart",
    "floating_checklist",
    "circular_gauge",
    "typing_terminal_hud",
    "waveform_pulse_card"
]
scene_widgets = rng.sample(WIDGET_POOL, 6)

edit_dna = {
    "palette": rng.choice(PRO_PALETTES),
    "widgets": scene_widgets,
    "transition": rng.choice(["shutter_bars", "iris_reveal", "prism_wipe", "flash_zoom"])
}

print(f"Chosen Studio Palette: {edit_dna['palette']['name']} | Widgets: {scene_widgets}")

def build_prompt(topic_str):
    lines = [
        "You are India's #1 viral Instagram Reel scriptwriter & motion graphics director (known for 5M+ view high-retention psychology, finance, and life-hack reels).",
        f'Topic: "{topic_str}"',
        "",
        "Write an addictive, punchy, high-retention 6-scene Hinglish Reel script (strictly 32 to 38 seconds total -> 11 to 14 words per scene, ~75 words total).",
        "",
        "STRICT CONTENT & VOICE RULES:",
        "1. Scene 1 MUST be a shocking scroll-stopping hook with a concrete insight or question. NEVER use generic intros like 'Hello friends' or 'Aaj hum baat karenge'.",
        "2. Every single scene must reveal a specific, practical, eye-opening truth or real-world example directly about the topic. Zero fluff!",
        "3. For EACH scene, return TWO text fields:",
        "   - 'tts_voice': Natural spoken Hindi-English mix where Hindi words are written in clean Devanagari script and English buzzwords in English (e.g., 'क्या आप जानते हैं Ratan Tata का वो एक rule जो हर middle class इंसान को सीखना चाहिए?') so ElevenLabs speaks with 100% authentic Indian emotion and accent!",
        "   - 'caption': The exact same spoken sentence written in clean, easy Roman Hinglish (e.g., 'Kya aap jaante hain Ratan Tata ka woh ek rule jo har middle class insaan ko seekhna chahiye?') for on-screen karaoke captions!",
        "4. Also return motion-graphic UI data per scene:",
        "   - 'kicker': 2-3 word top badge",
        "   - 'headline': 3-5 word bold screen title",
        "   - 'metric_big': Punchy 2-6 char hero stat (e.g. '5 SEC', '94%', 'TRAP', 'RULE #1', '3X', 'SAVE')",
        "   - 'metric_label': Short 2-3 word label under the stat",
        "   - 'left_label': Short mistake/point A (max 16 chars)",
        "   - 'right_label': Short smart move/point B (max 16 chars)",
        "   - 'pct': Integer between 76 and 98",
        "   - 'image_prompt': Vivid vertical 9:16 photorealistic cinematic background in English (clean aesthetic, soft depth of field, 8k, no text).",
        "",
        "Return ONLY valid JSON with key 'scenes' containing 6 objects."
    ]
    return "\n".join(lines)

def generate_ai_script(topic_str):
    prompt = build_prompt(topic_str)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        for model_name in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                resp = requests.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}
                    },
                    timeout=30
                )
                r_json = resp.json()
                if "candidates" not in r_json:
                    print(f"Gemini ({model_name}) response issue:", r_json.get("error", r_json))
                    continue
                raw = r_json["candidates"][0]["content"]["parts"][0]["text"]
                raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
                data = json.loads(raw)
                if "scenes" in data and len(data["scenes"]) == 6:
                    print(f"Viral Script + Motion Graphics Data generated via {model_name}!")
                    return data
            except Exception as e:
                print(f"Gemini ({model_name}) skip:", e)

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
            {
                "tts_voice": f"क्या आप जानते हैं {topic_str} के पीछे का सबसे बड़ा psychological secret क्या है?",
                "caption": f"Kya aap jaante hain {topic_str} ke peeche ka sabse bada psychological secret kya hai?",
                "kicker": "SHOCKING TRUTH", "headline": "Asli Raaz Kya Hai?",
                "metric_big": "94%", "metric_label": "LOG IGNORE KARTE HAIN",
                "left_label": "Aam Soch", "right_label": "Asli Sach", "pct": 94,
                "image_prompt": "Minimalist modern luxury studio architecture with dramatic rim light, 8k, no text"
            },
            {
                "tts_voice": "ज़्यादातर लोग बिना सोचे समझे वही पुरानी गलती बार-बार दोहराते रहते हैं।",
                "caption": "Zyaadatar log bina soche samjhe wahi purani galti baar-baar dohrate rehte hain.",
                "kicker": "COMMON TRAP", "headline": "Yeh Galti Mat Karo",
                "metric_big": "TRAP", "metric_label": "90% LOG PHASTE HAIN",
                "left_label": "Purana Tareeka", "right_label": "Smart Shift", "pct": 86,
                "image_prompt": "Close up of sleek glass chess pieces on minimalist table, soft bokeh, 8k, no text"
            },
            {
                "tts_voice": "लेकिन जो लोग सही pattern पकड़ लेते हैं, उनका control हर situation पर होता है।",
                "caption": "Lekin jo log sahi pattern pakad lete hain, unka control har situation par hota hai.",
                "kicker": "MINDSET SHIFT", "headline": "Pattern Samajhna Seekho",
                "metric_big": "3X", "metric_label": "FASTER CLARITY",
                "left_label": "Blind Reaction", "right_label": "Calm Control", "pct": 91,
                "image_prompt": "Clean futuristic minimalist workspace with warm ambient lighting, 8k, no text"
            },
            {
                "tts_voice": "जब आप सही वक़्त पर सही कदम उठाते हैं, तो सब कुछ आपके हक़ में होता है।",
                "caption": "Jab aap sahi waqt par sahi kadam uthate hain, toh sab kuch aapke haq mein hota hai.",
                "kicker": "POWER MOVE", "headline": "Sahi Waqt Aur Faisla",
                "metric_big": "5 SEC", "metric_label": "DECISION WINDOW",
                "left_label": "Overthinking", "right_label": "Instant Action", "pct": 95,
                "image_prompt": "Golden hour light rays over modern city skyline, serene aesthetic, 8k, no text"
            },
            {
                "tts_voice": "इससे आपका confidence बढ़ता है और लोग आपकी बातों को गंभीरता से सुनते हैं।",
                "caption": "Isse aapka confidence badhta hai aur log aapki baaton ko gambhirta se sunte hain.",
                "kicker": "REAL RESULT", "headline": "Confidence Aur Respect",
                "metric_big": "97%", "metric_label": "HIGH IMPACT SCORE",
                "left_label": "Self Doubt", "right_label": "Unshakable", "pct": 97,
                "image_prompt": "Elegant golden hourglass on clean stone pedestal, soft studio lighting, 8k, no text"
            },
            {
                "tts_voice": "अगर यह बात काम की लगी हो, तो इस reel को अभी save ज़रूर करें!",
                "caption": "Agar yeh baat kaam ki lagi ho, toh iss reel ko abhi save zaroor karein!",
                "kicker": "SAVE & SHARE", "headline": "Abhi Save Karein",
                "metric_big": "SAVE", "metric_label": "DAILY REMINDER",
                "left_label": "Scroll Past", "right_label": "Apply Today", "pct": 99,
                "image_prompt": "Sleek metallic compass on minimalist surface with soft warm glow, 8k, no text"
            }
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
                r = requests.get(f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&seed={seed}&nologo=true", timeout=22)
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
    [{"type": "sub_boom", "offset": 0.02}, {"type": "rise", "offset": 0.08}, {"type": "pop", "offset": 0.55}, {"type": "whoosh", "offset": 2.1}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "impact", "offset": 0.55}, {"type": "pop", "offset": 1.15}, {"type": "ping", "offset": 2.0}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "ping", "offset": 0.65}, {"type": "pop", "offset": 1.45}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "impact", "offset": 0.70}, {"type": "ping", "offset": 1.80}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "pop", "offset": 0.45}, {"type": "ping", "offset": 1.10}, {"type": "pop", "offset": 1.85}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "sub_boom", "offset": 0.85}, {"type": "ping", "offset": 1.95}]
]

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())

def generate_sfx_bank():
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.38:c=pink:a=0.52", "-af", "bandpass=f=900:width_type=h:w=1300,afade=t=in:ss=0:d=0.07,afade=t=out:st=0.14:d=0.24", "sfx_whoosh.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=820:d=0.11", "-af", "asetrate=44100*0.72,aresample=44100,afade=t=out:st=0.02:d=0.09,volume=0.65", "sfx_pop.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=82:d=0.40", "-af", "afade=t=out:st=0.04:d=0.36,volume=1.0", "sfx_impact.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=52:d=0.55", "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.08:d=0.47,volume=1.1", "sfx_sub_boom.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1318:d=0.24", "-af", "afade=t=in:ss=0:d=0.015,afade=t=out:st=0.04:d=0.20,volume=0.55", "sfx_ping.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.48:c=pink:a=0.34", "-af", "highpass=f=650,afade=t=in:ss=0:d=0.36,afade=t=out:st=0.36:d=0.12", "sfx_rise.wav"], check=True)

def generate_elevenlabs_tts(text, out_file):
    el_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not el_key:
        return False

    voice_id = "EXAVITQu4vr4xnSDxMaL" if voice_style == "cute_viral" else "pNInz6obpgDQGcFmaJgB"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": el_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.42,
            "similarity_boost": 0.80,
            "style": 0.45,
            "use_speaker_boost": True
        }
    }

    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(out_file, "wb") as f:
                    f.write(r.content)
                return True
            else:
                print(f"ElevenLabs HTTP {r.status_code}: {r.text[:160]}")
                if r.status_code in (401, 402, 429):
                    break
        except Exception as e:
            print(f"ElevenLabs retry {attempt+1}/3:", e)
        time.sleep(1.5)
    return False

def run_edge_tts_fallback(text, out_file):
    voice_name = "hi-IN-SwaraNeural" if voice_style == "cute_viral" else "hi-IN-MadhurNeural"
    rate = "+12%"
    pitch = "+2Hz" if voice_style == "cute_viral" else "-2Hz"
    for attempt in range(5):
        res = subprocess.run([
            "edge-tts", "--voice", voice_name,
            "--rate", rate, "--pitch", pitch,
            "--text", text, "--write-media", out_file
        ])
        if res.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 500:
            return
        time.sleep(2.0)
    raise RuntimeError(f"Failed TTS fallback for {out_file}")

generate_sfx_bank()

timeline = []
current_time = 0.0
voice_files = []
sfx_inputs = []
filter_complex = []
sfx_counter = 0

using_elevenlabs = bool(os.environ.get("ELEVENLABS_API_KEY", "").strip())
print("Voice Engine Mode:", "ElevenLabs Multilingual v2 (Human Studio Voice)" if using_elevenlabs else "Edge-TTS Devanagari Tuned")

for idx, sc in enumerate(scenes_data):
    v_file = f"voice_{idx}.mp3"
    raw_v = f"raw_voice_{idx}.mp3"
    tts_text = sc.get("tts_voice", sc.get("caption", sc.get("voice", "")))
    cap_text = sc.get("caption", sc.get("voice", tts_text))

    ok = generate_elevenlabs_tts(tts_text, raw_v)
    if ok:
        print(f"Generated ElevenLabs Human Voice for Scene {idx+1}/6")
        af_str = "atempo=1.07,highpass=f=85,equalizer=f=200:width_type=h:width=120:g=2.5,equalizer=f=3600:width_type=h:width=1600:g=3.0,acompressor=threshold=-16dB:ratio=2.8:attack=5:release=50"
    else:
        run_edge_tts_fallback(tts_text, raw_v)
        af_str = "highpass=f=90,equalizer=f=220:width_type=h:width=120:g=3,equalizer=f=3400:width_type=h:width=1600:g=3.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50"

    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)

    dur = get_duration(v_file) + 0.14
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "index": idx,
        "start": round(current_time, 3),
        "duration": round(dur, 3),
        "voice": cap_text,
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

print(f"V12 ElevenLabs + Heavy Motion Studio Ready! ({round(current_time, 2)}s)")
