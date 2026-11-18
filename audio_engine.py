import sys
import subprocess
import json
import os
import time
import re
import random
import requests

raw_topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "cute_viral"

rng = random.SystemRandom()

TRENDING_VIRAL_TOPICS = [
    "Dark Psychology: Kisi Ka Bhi Mind Kaise Padhein",
    "Middle Class Se Crorepati Banne Ka 3-Bucket Money Formula",
    "Subah 5 Baje Uthne Ka Secret Dopamine Hack",
    "Overthinking Ko 60 Second Mein Rokne Ki Navy SEAL Trick",
    "Phone Ki 3 Secret Settings Jo Battery 2X Kar Dengi",
    "Interview Ya Meeting Mein Instant Respect Pane Ki Body Language",
    "Procrastination Khatam Karne Ka 5-Minute Rule",
    "Paise Bachane Ke 3 Silent Rules Jo Ameer Log Follow Karte Hain",
    "Communication Skill: Log Aapki Baat Dhyan Se Kaise Sunenge",
    "Brain Memory 3X Fast Karne Ki Japanese Technique",
    "Social Media Addiction Todne Ka 7-Day Reset Plan",
    "Confidence Boost Karne Ki 3 Psychological Tricks"
]

topic = raw_topic if raw_topic else rng.choice(TRENDING_VIRAL_TOPICS)
print(f"Selected Viral Topic: {topic}")

PALETTE_POOL = [
    {"name": "obsidian_crimson", "primary": [244, 63, 94], "secondary": [251, 191, 36], "dark": [248, 250, 252], "soft": [30, 27, 38], "tint": [24, 24, 34], "bg": [11, 11, 16], "grid": [32, 32, 46], "is_dark": True},
    {"name": "electric_cobalt", "primary": [59, 130, 246], "secondary": [16, 185, 129], "dark": [248, 250, 252], "soft": [23, 37, 64], "tint": [20, 32, 56], "bg": [9, 14, 26], "grid": [26, 38, 66], "is_dark": True},
    {"name": "royal_gold_dark", "primary": [245, 158, 11], "secondary": [239, 68, 68], "dark": [250, 250, 249], "soft": [38, 33, 24], "tint": [32, 28, 22], "bg": [13, 12, 10], "grid": [38, 35, 28], "is_dark": True},
    {"name": "neon_emerald_dark", "primary": [16, 185, 129], "secondary": [56, 189, 248], "dark": [240, 253, 244], "soft": [17, 42, 36], "tint": [15, 36, 31], "bg": [8, 18, 16], "grid": [22, 48, 42], "is_dark": True},
    {"name": "clean_editorial_blue", "primary": [37, 99, 235], "secondary": [225, 29, 72], "dark": [15, 23, 42], "soft": [219, 234, 254], "tint": [239, 246, 255], "bg": [248, 250, 252], "grid": [224, 232, 242], "is_dark": False},
    {"name": "clean_editorial_red", "primary": [220, 38, 38], "secondary": [217, 119, 6], "dark": [17, 24, 39], "soft": [254, 226, 226], "tint": [254, 242, 242], "bg": [250, 248, 248], "grid": [238, 224, 224], "is_dark": False}
]

BG_PATTERNS = ["grid", "dots", "diagonal", "concentric"]
TRANSITIONS = ["shutter_v", "curtain_h", "iris_zoom"]

SCENE_WIDGET_CHOICES = {
    "scene1": ["big_stat_hook", "alert_card", "split_question"],
    "scene2": ["myth_stamp", "versus_clash"],
    "scene3": ["three_stack", "timeline_nodes"],
    "scene4": ["comparison_bars", "radial_gauge"],
    "scene5": ["checklist_cards", "live_feed_pulse"],
    "scene6": ["cta_comment_box"]
}

visual_dna = {
    "palette": rng.choice(PALETTE_POOL),
    "bg_pattern": rng.choice(BG_PATTERNS),
    "transition": rng.choice(TRANSITIONS),
    "widgets": {k: rng.choice(v) for k, v in SCENE_WIDGET_CHOICES.items()}
}

def build_prompt(topic_str):
    return f"""You are a top viral Indian Instagram Reel scriptwriter & motion-graphics director.
Topic: "{topic_str}"

Create a 100% original, ultra-engaging 6-scene Hinglish Reel script (strictly 32 to 38 seconds total when spoken fast -> ~12-14 words per scene, ~80 words total).
CRITICAL RULES:
1. Every word, number, headline, and card MUST be 100% specific to "{topic_str}".
2. Write Hindi words phonetically for natural Indian TTS pronunciation (use "isse" instead of "ise", "hee" instead of "hi", "hazaaron" instead of "hazaron", "logon" instead of "logo").
3. Keep visual text super crisp (2 to 4 words per line).
4. Return ONLY valid JSON matching this exact schema:
{{
  "scene1": {{
    "voice": "Hook narration (12-14 words)",
    "h_top": "2-3 words",
    "h_highlight": "1-2 words",
    "h_pill": "3-4 words badge",
    "big_number": "99%",
    "card_title": "Short header (max 22 chars)",
    "point1": "First punchy line (max 25 chars)",
    "point2": "Second punchy line (max 25 chars)"
  }},
  "scene2": {{
    "voice": "Myth/mistake narration (12-14 words)",
    "sub": "99% log yeh galti karte hain...",
    "myth": "2-WORD MYTH?",
    "truth_big": "3 SECRETS",
    "truth_sub": "REAL TRUTH"
  }},
  "scene3": {{
    "voice": "3 actionable steps/secrets narration (12-14 words)",
    "badge": "01 • 3 CORE SECRETS",
    "h_top": "2 words",
    "h_pill": "2 words",
    "h_bottom": "2-3 words",
    "item1": "01 • Secret 1 (max 23 chars)",
    "tag1": "#1",
    "item2": "02 • Secret 2 (max 23 chars)",
    "tag2": "#2",
    "item3": "03 • Secret 3 (max 23 chars)",
    "tag3": "#3"
  }},
  "scene4": {{
    "voice": "Before vs After impact narration (12-14 words)",
    "badge": "02 • MASSIVE SHIFT",
    "h_top": "2-3 words",
    "h_pill": "2 words",
    "h_tail": "1-2 words",
    "before_label": "Old Habit: 15% Result",
    "after_label": "New Formula: 10X Result",
    "percent_val": 94,
    "footer": "Short takeaway line (max 30 chars)"
  }},
  "scene5": {{
    "voice": "Real-life proof/benefits narration (12-14 words)",
    "badge": "03 • PROVEN PROOF",
    "h_top": "2 words",
    "h_highlight": "2 words",
    "h_bottom": "2-3 words",
    "metric_title": "SUCCESS RATE",
    "metric_val": "98.7%",
    "row1_left": "Benefit 1 (max 22 chars)",
    "row1_right": "Active",
    "row2_left": "Benefit 2 (max 22 chars)",
    "row2_right": "Proven",
    "row3_left": "Benefit 3 (max 22 chars)",
    "row3_right": "100%"
  }},
  "scene6": {{
    "voice": "Strong CTA ending with comment keyword (12-14 words)",
    "h_top": "2-3 words",
    "h_pill": "2 words",
    "h_tail": "1-2 words",
    "stat_title": "FINAL RESULT",
    "stat_big": "10X FAST",
    "stat_pill": "Save & Share This Reel",
    "keyword": "ONEWORD",
    "cta_text": "Comment karo  [ ONEWORD ]"
  }}
}}"""

def generate_ai_script(topic_str):
    prompt = build_prompt(topic_str)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=25)
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data = json.loads(raw)
            print("Script generated via Gemini API!")
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
                timeout=25
            )
            raw = resp.json()["choices"][0]["message"]["content"]
            raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data = json.loads(raw)
            print("Script generated via OpenAI API!")
            return data
        except Exception as e:
            print("OpenAI API skip:", e)

    for model_name in ["openai", "mistral"]:
        try:
            resp = requests.post(
                "https://text.pollinations.ai/",
                json={
                    "messages": [
                        {"role": "system", "content": "Return strictly valid JSON only. No markdown fences."},
                        {"role": "user", "content": prompt}
                    ],
                    "model": model_name,
                    "seed": rng.randint(1, 999999)
                },
                timeout=30
            )
            if resp.status_code == 200 and resp.text.strip():
                match = re.search(r"\{[\s\S]*\}", resp.text.strip())
                if match:
                    data = json.loads(match.group(0))
                    if "scene1" in data and "scene6" in data:
                        print(f"Script generated via Free AI ({model_name})!")
                        return data
        except Exception as e:
            print(f"Free AI ({model_name}) retry:", e)

    short_t = topic_str[:22]
    kw = re.sub(r"[^A-Za-z0-9]", "", topic_str.split()[0]).upper()[:8] or "SECRET"
    return {
        "scene1": {
            "voice": f"Kya aap jaante hain {topic_str} ka woh secret jo 99 percent log ignore karte hain?",
            "h_top": "99% Log",
            "h_highlight": "Nahi Jaante",
            "h_pill": short_t,
            "big_number": "99%",
            "card_title": "HIDDEN TRUTH",
            "point1": "Aaj hee yeh trick samjho",
            "point2": f"{short_t} ka real formula"
        },
        "scene2": {
            "voice": "Zyaadatar log purane tareeke follow karte hain, lekin asli result sirf 3 smart steps se aata hai.",
            "sub": "Purana tareeka chhodo...",
            "myth": "SLOW WAY?",
            "truth_big": "3 STEPS",
            "truth_sub": "GAME CHANGER"
        },
        "scene3": {
            "voice": "Pehla step: Sahi mindset banao. Doosra: Daily micro-action lo. Teersa: Consistency lock karo.",
            "badge": "01 • 3 CORE STEPS",
            "h_top": "Bas yeh",
            "h_pill": "3 steps",
            "h_bottom": "follow karke dekho",
            "item1": "01 • Laser Focus Setup",
            "tag1": "#1",
            "item2": "02 • Smart Daily Action",
            "tag2": "#2",
            "item3": "03 • 10X Growth Loop",
            "tag3": "#3"
        },
        "scene4": {
            "voice": "Normal tareeke mein mahine lagte hain, lekin yeh smart system pehle week se fark dikhata hai.",
            "badge": "02 • REAL IMPACT",
            "h_top": "Purana nahi,",
            "h_pill": "Smart System",
            "h_tail": "lagao",
            "before_label": "Normal Tareeka: 15% Result",
            "after_label": "Smart Formula: 10X Result",
            "percent_val": 94,
            "footer": "Turant result dikhna shuru hota hai"
        },
        "scene5": {
            "voice": "Isse aapka time bachta hai, confidence badhta hai, aur har kaam autopilot par fast hota hai.",
            "badge": "03 • PROVEN PROOF",
            "h_top": "Har jagah",
            "h_highlight": "instant growth",
            "h_bottom": "aur clarity milegi",
            "metric_title": "SUCCESS SCORE",
            "metric_val": "98.6%",
            "row1_left": "High Speed Focus",
            "row1_right": "Active",
            "row2_left": "Zero Overthinking",
            "row2_right": "Proven",
            "row3_left": "Daily Momentum",
            "row3_right": "100%"
        },
        "scene6": {
            "voice": f"Aaj hee isse try karo. Full guide aur Part 2 chahiye toh comment karo {kw}!",
            "h_top": "Aapko bhi chahiye",
            "h_pill": "Full Guide",
            "h_tail": "aur Part 2?",
            "stat_title": "DAILY RESULT",
            "stat_big": "10X BETTER",
            "stat_pill": "Save & Share This Reel",
            "keyword": kw,
            "cta_text": f"Comment karo  [ {kw} ]"
        }
    }

script_data = generate_ai_script(topic)
script_data["_visual_dna"] = visual_dna
with open("script_data.json", "w") as f:
    json.dump(script_data, f, indent=2)

scenes = [
    {"id": "scene1", "text": script_data["scene1"]["voice"], "sfx": [{"type": "rise", "offset": 0.05}, {"type": "pop", "offset": 1.2}, {"type": "whoosh", "offset": 2.4}]},
    {"id": "scene2", "text": script_data["scene2"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "impact", "offset": 1.6}]},
    {"id": "scene3", "text": script_data["scene3"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "pop", "offset": 1.4}, {"type": "pop", "offset": 2.3}]},
    {"id": "scene4", "text": script_data["scene4"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 1.7}]},
    {"id": "scene5", "text": script_data["scene5"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 1.4}, {"type": "ping", "offset": 2.1}]},
    {"id": "scene6", "text": script_data["scene6"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "type", "offset": 2.2}, {"type": "impact", "offset": 3.0}]}
]

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())

def generate_sfx_bank():
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.35:c=pink:a=0.45", "-af", "bandpass=f=850:width_type=h:w=1200,afade=t=in:ss=0:d=0.08,afade=t=out:st=0.14:d=0.21", "sfx_whoosh.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=780:d=0.10", "-af", "asetrate=44100*0.68,aresample=44100,afade=t=out:st=0.02:d=0.08,volume=0.60", "sfx_pop.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=75:d=0.38", "-af", "afade=t=out:st=0.04:d=0.34,volume=1.0", "sfx_impact.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1174:d=0.22", "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.05:d=0.17,volume=0.50", "sfx_ping.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.05:c=white:a=0.38", "-af", "highpass=f=2000,afade=t=out:st=0.01:d=0.04", "sfx_type.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.30", "-af", "highpass=f=600,afade=t=in:ss=0:d=0.35,afade=t=out:st=0.35:d=0.10", "sfx_rise.wav"], check=True)

def run_edge_tts_with_retry(text, out_file):
    voice_name = "hi-IN-SwaraNeural" if voice_style == "cute_viral" else "hi-IN-MadhurNeural"
    rate = "+18%"
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

for idx, sc in enumerate(scenes):
    v_file = f"voice_{idx}.mp3"
    raw_v = f"raw_voice_{idx}.mp3"
    run_edge_tts_with_retry(sc["text"], raw_v)
    time.sleep(1.0)

    af_str = "highpass=f=90,equalizer=f=220:width_type=h:width=120:g=3,equalizer=f=3400:width_type=h:width=1600:g=3.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50"
    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)

    dur = get_duration(v_file) + 0.14
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "id": sc["id"],
        "start": round(current_time, 3),
        "duration": round(dur, 3)
    })

    for s in sc["sfx"]:
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

subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi",
    "-i", f"aevalsrc=0.055*sin(2*PI*55*t)*exp(-4*mod(t,0.5))+0.025*sin(2*PI*220*t)*(0.5+0.5*sin(2*PI*2*t))+0.015*sin(2*PI*330*t)*(0.5+0.5*cos(2*PI*2*t)):d={current_time+1}",
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
    json.dump({"total_duration": round(current_time, 3), "scenes": timeline}, f, indent=2)

print(f"Natural Viral Voice + Beat + SFX Ready! Total length: {round(current_time, 2)}s")
