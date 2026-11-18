import sys
import subprocess
import json
import os
import time
import re
import requests

topic = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() else "AI Customer Support App for Business"
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "bunny"

def generate_ai_script(topic_str):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        prompt = f"""You are a viral Instagram Reel scriptwriter & motion graphics director for Indian creators.
Topic: "{topic_str}"

Create a crisp, high-retention 6-scene Hinglish Reel script that lasts strictly 35 to 42 seconds when spoken fast (around 90 to 105 words TOTAL across all 6 scenes — ~15-17 words per scene).
Rules:
1. Write Hindi words phonetically so Indian TTS pronounces them clearly (e.g., use "isse" instead of "ise", "hee" instead of "hi", "hazaaron" instead of "hazaron").
2. Keep every visual headline/label super short so it fits cleanly on 1080x1920 mobile cards.
3. Return ONLY valid JSON (no markdown, no explanation) matching this exact schema:
{{
  "scene1": {{
    "voice": "Hook narration (14-17 words)",
    "h_top": "2-3 words",
    "h_highlight": "1-2 words",
    "h_pill": "3-4 words badge",
    "sender": "Client / User",
    "msg1": "Short message 1 (max 24 chars)",
    "msg2_line1": "Short message 2a (max 24 chars)",
    "msg2_line2": "Short message 2b (max 24 chars)"
  }},
  "scene2": {{
    "voice": "Myth-buster narration (14-17 words)",
    "sub": "Pehli baar lagta hai...",
    "myth": "MUSHKIL?",
    "truth_big": "100%",
    "truth_sub": "POSSIBLE"
  }},
  "scene3": {{
    "voice": "3-step overview narration (14-17 words)",
    "badge": "01 • 3 SMART STEPS",
    "h_top": "2 words",
    "h_pill": "2 words",
    "h_bottom": "2-3 words",
    "layer1": "01 • Step One Title (max 24 chars)",
    "tag1": "LIVE",
    "layer2": "02 • Step Two Title (max 24 chars)",
    "tag2": "24/7",
    "layer3": "03 • Step Three Title (max 24 chars)",
    "tag3": "100%"
  }},
  "scene4": {{
    "voice": "Speed/advantage comparison narration (14-17 words)",
    "badge": "02 • CORE ENGINE",
    "h_top": "2-3 words",
    "h_pill": "2 words",
    "h_tail": "1-2 words",
    "slow_label": "Purana Tareeka: 45 min",
    "fast_label": "Smart System: 0.8 sec",
    "footer": "100% accurate aur fast result"
  }},
  "scene5": {{
    "voice": "Live proof/results narration (14-17 words)",
    "badge": "03 • LIVE RESULTS",
    "h_top": "2 words",
    "h_highlight": "2 words",
    "h_bottom": "3 words",
    "metric_title": "LIVE GROWTH",
    "metric_val": "+340%",
    "row1_left": "Result #1 • Fast",
    "row1_right": "Active",
    "row2_left": "Result #2 • Auto",
    "row2_right": "Verified",
    "row3_left": "Result #3 • Scale",
    "row3_right": "24/7 Live"
  }},
  "scene6": {{
    "voice": "Strong CTA narration ending with comment keyword (14-17 words)",
    "h_top": "Aapko bhi chahiye",
    "h_pill": "2 words",
    "h_tail": "setup?",
    "stat_title": "TIME & COST SAVED",
    "stat_big": "10X FAST",
    "stat_pill": "Zero Tension • Full Automation",
    "keyword": "START",
    "cta_text": "Comment karo  [ START ]"
  }}
}}"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=25)
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
            data = json.loads(raw)
            print("Gemini AI generated custom script for topic:", topic_str)
            return data
        except Exception as e:
            print("Gemini API fallback used:", e)

    # Smart dynamic fallback if GEMINI_API_KEY is not set
    short_topic = topic_str[:22]
    kw = re.sub(r"[^A-Za-z0-9]", "", topic_str.split()[0]).upper()[:8] or "AI"
    return {
        "scene1": {
            "voice": f"Ek client ka message aaya... Humein apna khud ka {topic_str} chahiye, jo bina ruke kaam kare.",
            "h_top": "Ek naya",
            "h_highlight": "project",
            "h_pill": short_topic,
            "sender": "Client  • Online",
            "msg1": "Hi! Urgent kaam hai",
            "msg2_line1": f"{short_topic} ka",
            "msg2_line2": "best system chahiye!"
        },
        "scene2": {
            "voice": "Pehli baar suno toh lagta hai... Mushkil? Lekin yeh 100 percent possible hai. Bas sahi system chahiye.",
            "sub": "Pehli baar lagta hai...",
            "myth": "MUSHKIL?",
            "truth_big": "100%",
            "truth_sub": "POSSIBLE"
        },
        "scene3": {
            "voice": "Hum isse 3 smart layers mein banate hain. Pehli layer: Fast Setup, jisse har kaam turant shuru hota hai.",
            "badge": "01 • 3 SMART LAYERS",
            "h_top": "Hum isse",
            "h_pill": "3 layers",
            "h_bottom": "mein banate hain",
            "layer1": "01 • Fast Smart Setup",
            "tag1": "LIVE",
            "layer2": "02 • Custom AI Engine",
            "tag2": "24/7",
            "layer3": "03 • Auto Growth System",
            "tag3": "100%"
        },
        "scene4": {
            "voice": "Doosri layer: Smart Automation. Yeh purane manual tareeke ke mukable sirf 1 second mein exact result deta hai.",
            "badge": "02 • LAYER 02 • SPEED",
            "h_top": "Manual kaam nahi,",
            "h_pill": "Smart Tech",
            "h_tail": "se turant",
            "slow_label": "Purana Tareeka:  45 min",
            "fast_label": "Smart System:  0.8 sec FAST",
            "footer": "100% accurate aur fast result"
        },
        "scene5": {
            "voice": "Teesri layer: Auto Scaling. Har task aur order khud hee complete hota hai, bina kisi extra team ke.",
            "badge": "03 • LAYER 03 • AUTO SCALE",
            "h_top": "Har kaam",
            "h_highlight": "auto mode",
            "h_bottom": "mein khud hota hai",
            "metric_title": "LIVE PERFORMANCE",
            "metric_val": "+340%",
            "row1_left": "Task #101 • Instant",
            "row1_right": "Done",
            "row2_left": "Task #102 • Verified",
            "row2_right": "Active",
            "row3_left": "Task #103 • Scaled",
            "row3_right": "24/7"
        },
        "scene6": {
            "voice": f"Result? Zero tension aur 10X fast growth. Aapko bhi aisa system chahiye? Toh comment karo {kw}!",
            "h_top": "Aapko bhi aisa",
            "h_pill": short_topic[:14],
            "h_tail": "chahiye?",
            "stat_title": "TIME & COST SAVED",
            "stat_big": "10X FAST",
            "stat_pill": "24/7 Uptime • Zero Missed Leads",
            "keyword": kw,
            "cta_text": f"Comment karo  [ {kw} ]"
        }
    }

script_data = generate_ai_script(topic)
with open("script_data.json", "w") as f:
    json.dump(script_data, f, indent=2)

scenes = [
    {"id": "scene1", "text": script_data["scene1"]["voice"], "sfx": [{"type": "type", "offset": 0.1}, {"type": "pop", "offset": 1.5}, {"type": "whoosh", "offset": 2.8}]},
    {"id": "scene2", "text": script_data["scene2"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.2}, {"type": "stamp", "offset": 2.0}]},
    {"id": "scene3", "text": script_data["scene3"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "pop", "offset": 2.0}, {"type": "pop", "offset": 3.1}]},
    {"id": "scene4", "text": script_data["scene4"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 2.2}]},
    {"id": "scene5", "text": script_data["scene5"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "ping", "offset": 1.8}, {"type": "ping", "offset": 2.6}]},
    {"id": "scene6", "text": script_data["scene6"]["voice"], "sfx": [{"type": "whoosh", "offset": 0.1}, {"type": "type", "offset": 3.0}, {"type": "pop", "offset": 3.9}]}
]

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())

def generate_sfx_bank():
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.40:c=pink:a=0.40", "-af", "bandpass=f=750:width_type=h:w=1100,afade=t=in:ss=0:d=0.12,afade=t=out:st=0.18:d=0.22", "sfx_whoosh.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=720:d=0.11", "-af", "asetrate=44100*0.62,aresample=44100,afade=t=out:st=0.03:d=0.08,volume=0.55", "sfx_pop.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=95:d=0.30", "-af", "afade=t=out:st=0.04:d=0.26,volume=0.95", "sfx_stamp.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1046:d=0.22", "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.06:d=0.16,volume=0.45", "sfx_ping.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.06:c=white:a=0.35", "-af", "highpass=f=1800,afade=t=out:st=0.01:d=0.05", "sfx_type.wav"], check=True)

def run_edge_tts_with_retry(text, out_file):
    voice_name = "hi-IN-SwaraNeural" if voice_style == "bunny" else "hi-IN-MadhurNeural"
    rate = "+22%" if voice_style == "bunny" else "+20%"
    pitch = "+36Hz" if voice_style == "bunny" else "-2Hz"
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
    time.sleep(1.2)

    if voice_style == "bunny":
        af_str = "asetrate=24000*1.12,aresample=24000,atempo=0.94,highpass=f=120,equalizer=f=3200:width_type=h:width=1500:g=4,acompressor=threshold=-16dB:ratio=3:attack=5:release=50"
    else:
        af_str = "equalizer=f=140:width_type=h:width=100:g=4,equalizer=f=3500:width_type=h:width=1500:g=3,acompressor=threshold=-18dB:ratio=3:attack=5:release=50"

    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)

    # Tight 0.18s pause between scenes so total video stays crisp (32-45s)
    dur = get_duration(v_file) + 0.18
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "id": sc["id"],
        "start": round(current_time, 3),
        "duration": round(dur, 3)
    })

    for s in sc["sfx"]:
        offset = min(s["offset"], max(0.1, dur - 0.25))
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
    "-i", f"aevalsrc=0.04*sin(2*PI*55*t)*(0.5+0.5*sin(2*PI*2.2*t))+0.02*sin(2*PI*110*t):d={current_time+1}",
    "-af", "lowpass=f=280,afade=t=in:ss=0:d=0.6,afade=t=out:st=" + str(max(0.5, current_time - 0.6)) + ":d=0.6",
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

print(f"Audio + Script Ready! Total video length: {round(current_time, 2)}s")
