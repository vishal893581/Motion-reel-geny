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
    "Dimaag Ki Memory Aur Focus Tez Karne Ki Japanese Kaizen Aadat",
    "Interview Ya Meeting Mein Pehle 7 Second Mein Impression Kaise Jamayein"
]

topic = raw_topic if raw_topic else rng.choice(TRENDING_VIRAL_TOPICS)
print(f"Selected Viral Topic: {topic}")

EDIT_PROFILES = [
    {
        "style_id": "cinematic_story",
        "name": "Dark Cinema Storytelling",
        "accent": [244, 63, 94],
        "highlight": [250, 204, 21],
        "bg_tint": [10, 12, 20],
        "layout_mode": "center_cinema",
        "caption_style": "neon_stroke",
        "transition": "flash_cut"
    },
    {
        "style_id": "apple_keynote",
        "name": "Clean Editorial & Glass Cards",
        "accent": [37, 99, 235],
        "highlight": [16, 185, 129],
        "bg_tint": [15, 23, 42],
        "layout_mode": "glass_editorial",
        "caption_style": "glass_pill",
        "transition": "slide_up"
    },
    {
        "style_id": "luxury_gold",
        "name": "Billionaire Noir & Gold",
        "accent": [217, 119, 6],
        "highlight": [253, 224, 71],
        "bg_tint": [14, 12, 10],
        "layout_mode": "editorial_frame",
        "caption_style": "underline_glow",
        "transition": "curtain_wipe"
    },
    {
        "style_id": "cyber_tech",
        "name": "Modern Tech & Neon Cyan",
        "accent": [6, 182, 212],
        "highlight": [168, 85, 247],
        "bg_tint": [8, 15, 28],
        "layout_mode": "split_hud",
        "caption_style": "glass_pill",
        "transition": "iris_zoom"
    },
    {
        "style_id": "sunset_creator",
        "name": "Warm Sunset Viral Creator",
        "accent": [234, 88, 12],
        "highlight": [255, 255, 255],
        "bg_tint": [24, 14, 12],
        "layout_mode": "center_cinema",
        "caption_style": "bold_box",
        "transition": "slide_up"
    },
    {
        "style_id": "emerald_wealth",
        "name": "Emerald Wealth & Growth",
        "accent": [5, 150, 105],
        "highlight": [250, 204, 21],
        "bg_tint": [8, 22, 18],
        "layout_mode": "glass_editorial",
        "caption_style": "neon_stroke",
        "transition": "flash_cut"
    }
]

edit_dna = rng.choice(EDIT_PROFILES)
print(f"Chosen Visual Style: {edit_dna['name']} ({edit_dna['layout_mode']})")

def build_prompt(topic_str):
    lines = [
        "You are India's #1 viral Instagram Reel scriptwriter & creative director (known for millions of views on psychology, finance, stories, and life-hacks).",
        f'Topic: "{topic_str}"',
        "",
        "Write an addictive, high-retention 6-scene Hinglish Reel script (strictly 32 to 38 seconds total -> 11 to 14 words per scene, ~75 words total).",
        "",
        "CRITICAL CONTENT RULES:",
        "1. Hook (Scene 1) MUST stop the scroll immediately with a shocking question, relatable pain point, or curiosity gap. NEVER use generic intros like Hello friends or Aaj hum baat karenge.",
        "2. Every single scene must reveal a genuinely useful, concrete insight, real-world example, or psychological/financial truth about the topic. No fluff!",
        "3. Write 100% NATURAL, EASY, GRAMMATICALLY CLEAN spoken Hinglish that Indian creators use (NO gibberish, NO broken English words).",
        "4. Spell Hindi words phonetically so Indian TTS speaks smoothly (use 'isse' instead of 'ise', 'hee' instead of 'hi', 'logon' instead of 'logo', 'kyunki' instead of 'kyuki', 'samajhiye' instead of 'samjhiye').",
        "5. For each scene provide kicker (2-3 word top tag), headline (3-5 word bold screen title), stat_badge (1-2 word visual callout), and image_prompt (vivid vertical 9:16 photorealistic cinematic visual description in English, dramatic lighting, 8k, no text in image).",
        "",
        "Return ONLY valid JSON with key 'scenes' containing 6 objects, each having keys: voice, kicker, headline, stat_badge, image_prompt."
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
                print("Generated fresh viral script via Gemini 2.5 Flash!")
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
                print("Generated fresh viral script via OpenAI API!")
                return data
        except Exception as e:
            print("OpenAI API skip:", e)

    return {
        "scenes": [
            {"voice": f"Kya aap jaante hain {topic_str} ke peeche ka asli raaz kya hai?", "kicker": "SHOCKING TRUTH", "headline": "Asli Raaz Kya Hai?", "stat_badge": "TRUTH", "image_prompt": f"Dramatic cinematic portrait in moody neon lighting, {topic_str}, photorealistic, 8k, no text"},
            {"voice": "Zyaadatar log bina soche samjhe wahi purani galti baar-baar dohrate rehte hain.", "kicker": "COMMON TRAP", "headline": "Yeh Galti Mat Karo", "stat_badge": "TRAP", "image_prompt": "Close up of dark luxury chessboard with dramatic golden rim light, 8k, no text"},
            {"voice": "Lekin jo log sahi psychology samajhte hain, woh har jagah apni alag pehchan banate hain.", "kicker": "MINDSET SHIFT", "headline": "Smart Logon Ki Soch", "stat_badge": "MINDSET", "image_prompt": "Modern minimalist penthouse overlooking rainy city lights at night, cinematic moody, 8k, no text"},
            {"voice": "Jab aap sahi waqt par sahi kadam uthate hain, toh sab kuch aapke haq mein hota hai.", "kicker": "POWER MOVE", "headline": "Sahi Waqt Aur Faisla", "stat_badge": "POWER", "image_prompt": "Silhouette standing before glowing golden sunset over mountains, volumetric rays, 8k, no text"},
            {"voice": "Isse aapka confidence badhta hai aur log aapki baaton ko gambhirta se sunte hain.", "kicker": "REAL RESULT", "headline": "Confidence Aur Respect", "stat_badge": "RESULT", "image_prompt": "Glowing golden hourglass on dark obsidian table with bokeh sparks, 8k, no text"},
            {"voice": "Agar yeh baat kaam ki lagi ho, toh iss reel ko abhi save zaroor karein!", "kicker": "SAVE & SHARE", "headline": "Abhi Save Karein", "stat_badge": "SAVE", "image_prompt": "Futuristic glowing compass pointing north in dark studio atmosphere, 8k, no text"}
        ]
    }

def generate_scene_visuals(scenes_list):
    os.makedirs("bg_assets", exist_ok=True)
    pexels_key = os.environ.get("PEXELS_API_KEY", "").strip()

    for idx, sc in enumerate(scenes_list):
        out_img = f"bg_assets/bg_{idx}.jpg"
        prompt = sc.get("image_prompt", "dramatic cinematic lighting 8k")
        saved = False

        try:
            encoded = urllib.parse.quote(prompt + ", vertical 9:16 composition, rich cinematic color grading, sharp focus, no text, no watermark")
            seed = rng.randint(1, 999999)
            img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&seed={seed}&nologo=true&model=flux"
            r = requests.get(img_url, timeout=35)
            if r.status_code == 200 and len(r.content) > 15000:
                with open(out_img, "wb") as f:
                    f.write(r.content)
                saved = True
                print(f"Generated custom AI scene art {idx+1}/6")
        except Exception as e:
            print(f"AI art retry {idx+1}:", e)

        if not saved and pexels_key:
            try:
                q = urllib.parse.quote(" ".join(prompt.split()[:4]))
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
                    print(f"Downloaded Pexels stock photo {idx+1}/6")
            except Exception as e:
                print("Pexels skip:", e)

        if not saved:
            from PIL import Image, ImageDraw, ImageFilter
            im = Image.new("RGB", (768, 1344), tuple(edit_dna["bg_tint"]))
            dr = ImageDraw.Draw(im)
            c1 = tuple(edit_dna["accent"])
            c2 = tuple(edit_dna["highlight"])
            dr.ellipse([rng.randint(-150, 250), rng.randint(-100, 400), rng.randint(450, 900), rng.randint(550, 1100)], fill=c1)
            dr.ellipse([rng.randint(50, 450), rng.randint(600, 950), rng.randint(550, 950), rng.randint(1150, 1550)], fill=c2)
            im = im.filter(ImageFilter.GaussianBlur(135))
            im.save(out_img, quality=92)
            print(f"Generated rich color mesh {idx+1}/6")

script_obj = generate_ai_script(topic)
scenes_data = script_obj["scenes"]
generate_scene_visuals(scenes_data)

sfx_bank_plan = [
    [{"type": "rise", "offset": 0.05}, {"type": "whoosh", "offset": 2.2}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "impact", "offset": 1.5}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 1.6}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "pop", "offset": 1.5}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 1.4}],
    [{"type": "whoosh", "offset": 0.1}, {"type": "impact", "offset": 2.2}]
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
        "stat_badge": sc.get("stat_badge", "VIRAL"),
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

print(f"V9 Ready! Style: {edit_dna['name']} | Duration: {round(current_time, 2)}s")
