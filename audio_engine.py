import sys
import subprocess
import json
import os
import time
import re
import random
import requests
from PIL import Image, ImageDraw, ImageFilter

raw_topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "bunny_punch_male"

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
    "Instagram Aur Reels Ki Lat Chhodne Ka Sabse Aasan 48-Hour Reset",
    "Middle Class Trap: EMI Aur Credit Card Se Bachne Ka Real Formula",
    "Body Language Secret: Bina Bole Room Mein Sabse Confident Kaise Dikhein",
    "Warren Buffett Ka 5-25 Rule Jo Aapki Life Ka Focus Badal Dega"
]

topic = raw_topic if raw_topic else rng.choice(TRENDING_VIRAL_TOPICS)
print(f"Selected Viral Topic: {topic}")

WHITE_GRID_PALETTES = [
    {
        "name": "apple_white_cobalt",
        "is_light": True,
        "bg": [248, 250, 253],
        "grid": [224, 232, 245],
        "card": [255, 255, 255],
        "card_border": [208, 220, 240],
        "text_main": [15, 23, 42],
        "text_muted": [95, 112, 136],
        "accent": [37, 99, 235],
        "secondary": [245, 158, 11],
        "positive": [16, 185, 129],
        "negative": [239, 68, 68]
    },
    {
        "name": "pure_paper_emerald",
        "is_light": True,
        "bg": [247, 252, 250],
        "grid": [218, 238, 230],
        "card": [255, 255, 255],
        "card_border": [200, 230, 218],
        "text_main": [14, 30, 26],
        "text_muted": [86, 115, 106],
        "accent": [5, 150, 105],
        "secondary": [217, 119, 6],
        "positive": [16, 185, 129],
        "negative": [225, 29, 72]
    },
    {
        "name": "swiss_grid_crimson",
        "is_light": True,
        "bg": [252, 250, 250],
        "grid": [238, 226, 228],
        "card": [255, 255, 255],
        "card_border": [232, 214, 218],
        "text_main": [24, 20, 24],
        "text_muted": [115, 105, 112],
        "accent": [225, 29, 72],
        "secondary": [37, 99, 235],
        "positive": [16, 185, 129],
        "negative": [220, 38, 38]
    },
    {
        "name": "studio_white_violet",
        "is_light": True,
        "bg": [249, 248, 254],
        "grid": [228, 224, 246],
        "card": [255, 255, 255],
        "card_border": [216, 210, 242],
        "text_main": [22, 18, 42],
        "text_muted": [104, 98, 134],
        "accent": [124, 58, 237],
        "secondary": [245, 158, 11],
        "positive": [16, 185, 129],
        "negative": [239, 68, 68]
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
    "palette": rng.choice(WHITE_GRID_PALETTES),
    "widgets": scene_widgets,
    "transition": rng.choice(["shutter_bars", "iris_reveal", "prism_wipe", "flash_zoom"])
}

print(f"Chosen White-Grid Palette: {edit_dna['palette']['name']} | Widgets: {scene_widgets}")

def build_prompt(topic_str):
    lines = [
        "You are India's #1 viral Instagram Reel scriptwriter & motion graphics director (known for 5M+ view high-retention psychology, finance, and life-hack reels).",
        f'Topic: "{topic_str}"',
        "",
        "Write an addictive, punchy, high-retention 6-scene Hinglish Reel script (strictly 32 to 38 seconds total -> 11 to 14 words per scene, ~75 words total).",
        "",
        "STRICT CONTENT & VOICE RULES:",
        "1. Scene 1 MUST be a shocking scroll-stopping hook with a concrete insight or question. NEVER use generic intros like 'Hello friends' or 'Aaj hum baat karenge'.",
        "2. Every single scene (Scenes 2, 3, 4, 5) MUST give a concrete, real-world actionable step, psychological cue, or real example directly solving the topic! Zero vague filler!",
        "3. For EACH scene, return TWO text fields:",
        "   - 'tts_voice': Natural spoken Hindi-English mix where Hindi words are written in clean Devanagari script and English buzzwords in English (e.g., 'क्या आप जानते हैं Ratan Tata का वो एक rule जो हर middle class इंसान को सीखना चाहिए?') so ElevenLabs speaks with 100% natural Indian emotion and punch!",
        "   - 'caption': The exact same spoken sentence written in clean, easy Roman Hinglish (e.g., 'Kya aap jaante hain Ratan Tata ka woh ek rule jo har middle class insaan ko seekhna chahiye?') for on-screen karaoke captions!",
        "4. Also return motion-graphic UI data per scene:",
        "   - 'kicker': 2-3 word top badge",
        "   - 'headline': 3-5 word bold screen title",
        "   - 'metric_big': Punchy 2-6 char hero stat (e.g. '5 SEC', '94%', 'TRAP', 'RULE #1', '3X', 'SAVE')",
        "   - 'metric_label': Short 2-3 word label under the stat",
        "   - 'left_label': Short mistake/point A (max 16 chars)",
        "   - 'right_label': Short smart move/point B (max 16 chars)",
        "   - 'pct': Integer between 76 and 98",
        "",
        "Return ONLY valid JSON with key 'scenes' containing 6 objects."
    ]
    return "\n".join(lines)

def call_gemini_any_key(gemini_key, prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}
    }
    models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    for model_name in models:
        endpoints = [
            (f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent", {"Content-Type": "application/json", "x-goog-api-key": gemini_key}),
            (f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}", {"Content-Type": "application/json"}),
            (f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model_name}:generateContent?key={gemini_key}", {"Content-Type": "application/json"})
        ]
        for url, hdrs in endpoints:
            try:
                resp = requests.post(url, headers=hdrs, json=payload, timeout=30)
                r_json = resp.json()
                if "candidates" not in r_json:
                    print(f"Gemini endpoint check ({model_name}):", str(r_json.get("error", r_json))[:200])
                    continue
                raw = r_json["candidates"][0]["content"]["parts"][0]["text"]
                raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
                data = json.loads(raw)
                if "scenes" in data and len(data["scenes"]) == 6:
                    print(f"SUCCESS! Gemini API connected & generated real script via {model_name}!")
                    return data
            except Exception as e:
                print(f"Gemini call retry ({model_name}):", e)
    return None

def generate_ai_script(topic_str):
    prompt = build_prompt(topic_str)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        data = call_gemini_any_key(gemini_key, prompt)
        if data:
            return data

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

    print("Using high-retention structured fallback script...")
    return {
        "scenes": [
            {
                "tts_voice": f"क्या आप जानते हैं {topic_str} के पीछे का सबसे बड़ा psychological secret क्या है?",
                "caption": f"Kya aap jaante hain {topic_str} ke peeche ka sabse bada psychological secret kya hai?",
                "kicker": "SHOCKING TRUTH", "headline": "Asli Raaz Kya Hai?",
                "metric_big": "94%", "metric_label": "LOG IGNORE KARTE HAIN",
                "left_label": "Aam Soch", "right_label": "Asli Sach", "pct": 94
            },
            {
                "tts_voice": "पहला नियम: किसी भी decision से पहले 5 सेकंड का pause लेने से दिमाग का emotional trap रुक जाता है।",
                "caption": "Pehla niyam: kisi bhi decision se pehle 5 second ka pause lene se dimaag ka emotional trap ruk jaata hai.",
                "kicker": "STEP 01", "headline": "5-Second Pause Rule",
                "metric_big": "5 SEC", "metric_label": "IMPULSE CONTROL",
                "left_label": "Instant Reaction", "right_label": "5-Sec Pause", "pct": 88
            },
            {
                "tts_voice": "दूसरा नियम: सामने वाले के शब्दों से ज़्यादा उसकी eye movement और body posture को notice करें।",
                "caption": "Doosra niyam: saamne wale ke shabdon se zyaada uski eye movement aur body posture ko notice karein.",
                "kicker": "STEP 02", "headline": "Body Language Read",
                "metric_big": "3X", "metric_label": "FASTER CLARITY",
                "left_label": "Sirf Baatein", "right_label": "Micro Signals", "pct": 92
            },
            {
                "tts_voice": "तीसरा नियम: अपनी energy को फालतू distractions से हटाकर सिर्फ top 2 priorities पर lock कर दें।",
                "caption": "Teesra niyam: apni energy ko faaltu distractions se hata kar sirf top 2 priorities par lock kar dein.",
                "kicker": "STEP 03", "headline": "Top-2 Focus Lock",
                "metric_big": "80/20", "metric_label": "HIGH OUTPUT RULE",
                "left_label": "Multitasking", "right_label": "Laser Focus", "pct": 95
            },
            {
                "tts_voice": "सिर्फ 7 दिन इस pattern को follow करने से आपका self-control और respect दोनों double हो जाएंगे।",
                "caption": "Sirf 7 din iss pattern ko follow karne se aapka self-control aur respect dono double ho jayenge.",
                "kicker": "7-DAY RESULT", "headline": "Double Self-Control",
                "metric_big": "2X", "metric_label": "CONFIDENCE BOOST",
                "left_label": "Old Habit", "right_label": "New Identity", "pct": 97
            },
            {
                "tts_voice": "अगर यह formula काम का लगा हो, तो इस reel को अभी save करके दोस्त को share करें!",
                "caption": "Agar yeh formula kaam ka laga ho, toh iss reel ko abhi save karke dost ko share karein!",
                "kicker": "SAVE & SHARE", "headline": "Abhi Save Karein",
                "metric_big": "SAVE", "metric_label": "DAILY REMINDER",
                "left_label": "Scroll Past", "right_label": "Apply Today", "pct": 99
            }
        ]
    }

def generate_white_grid_canvases(scenes_list):
    os.makedirs("bg_assets", exist_ok=True)
    pal = edit_dna["palette"]
    bg_c = tuple(pal["bg"])
    grid_c = tuple(pal["grid"])
    ac = tuple(pal["accent"])
    sc_c = tuple(pal["secondary"])

    for idx in range(len(scenes_list)):
        out_img = f"bg_assets/bg_{idx}.jpg"
        base = Image.new("RGB", (1080, 1920), bg_c)
        gd = ImageDraw.Draw(base)

        orb1 = tuple(int(bg_c[i] * 0.86 + ac[i] * 0.14) for i in range(3))
        orb2 = tuple(int(bg_c[i] * 0.88 + sc_c[i] * 0.12) for i in range(3))
        gd.ellipse([rng.randint(-150, 250), rng.randint(-100, 300), rng.randint(650, 1050), rng.randint(650, 1050)], fill=orb1)
        gd.ellipse([rng.randint(150, 450), rng.randint(950, 1300), rng.randint(850, 1200), rng.randint(1650, 2000)], fill=orb2)
        im = base.filter(ImageFilter.GaussianBlur(130))
        dr = ImageDraw.Draw(im)

        step = 60
        for gx in range(0, 1080, step):
            w_line = 2 if gx % (step * 4) == 0 else 1
            dr.line([(gx, 0), (gx, 1920)], fill=grid_c, width=w_line)
        for gy in range(0, 1920, step):
            w_line = 2 if gy % (step * 4) == 0 else 1
            dr.line([(0, gy), (1080, gy)], fill=grid_c, width=w_line)

        plus_c = tuple(int(grid_c[i] * 0.82 + ac[i] * 0.18) for i in range(3))
        for gx in range(step * 4, 1080, step * 4):
            for gy in range(step * 4, 1920, step * 4):
                dr.line([(gx - 10, gy), (gx + 10, gy)], fill=plus_c, width=2)
                dr.line([(gx, gy - 10), (gx, gy + 10)], fill=plus_c, width=2)

        im.save(out_img, quality=95)
    print("Generated 6 Crisp White Architectural Grid Canvases!")

script_obj = generate_ai_script(topic)
scenes_data = script_obj["scenes"]
generate_white_grid_canvases(scenes_data)

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
        print("ELEVENLABS_API_KEY not found in secrets!")
        return False

    voice_id = "cgSgspJ2msm6clMCkdW9" if voice_style == "cute_viral" else "TX3LPaxmHKxFdv7VOQHJ"
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
            "stability": 0.38,
            "similarity_boost": 0.82,
            "style": 0.52,
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
                print(f"ElevenLabs API issue (HTTP {r.status_code}): {r.text[:220]}")
                if r.status_code in (401, 402, 429):
                    break
        except Exception as e:
            print(f"ElevenLabs retry {attempt+1}/3:", e)
        time.sleep(1.5)
    return False

def run_edge_tts_fallback(text, out_file):
    voice_name = "hi-IN-SwaraNeural" if voice_style == "cute_viral" else "hi-IN-MadhurNeural"
    rate = "+12%"
    pitch = "+2Hz" if voice_style == "cute_viral" else "-1Hz"
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

print("Voice Mode:", "ElevenLabs Liam Bunny-Punch Human Voice" if voice_style != "cute_viral" else "ElevenLabs Jessica Viral Female")

for idx, sc in enumerate(scenes_data):
    v_file = f"voice_{idx}.mp3"
    raw_v = f"raw_voice_{idx}.mp3"
    tts_text = sc.get("tts_voice", sc.get("caption", ""))
    cap_text = sc.get("caption", tts_text)

    ok = generate_elevenlabs_tts(tts_text, raw_v)
    if ok:
        print(f"SUCCESS! ElevenLabs Human Voice generated for Scene {idx+1}/6")
        af_str = "atempo=1.08,highpass=f=85,equalizer=f=190:width_type=h:width=120:g=2.5,equalizer=f=3600:width_type=h:width=1600:g=3.2,acompressor=threshold=-16dB:ratio=2.8:attack=5:release=50"
    else:
        print(f"Scene {idx+1}/6 using Edge-TTS fallback")
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

print(f"V14 White-Grid + ElevenLabs Studio Ready! ({round(current_time, 2)}s)")
