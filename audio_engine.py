import sys
import subprocess
import json
import os
import requests

provider = sys.argv[1] if len(sys.argv) > 1 else "edge"

# Scene-wise script (Exact reference video pacing)
scenes = [
    {"id": "scene1", "text": "Developer aapko ye kabhi nahi batayega.", "sfx": "whoosh", "sfx_offset": 0.1},
    {"id": "scene2", "text": "Aapki website already ek app hai, bas convert karna hai.", "sfx": "pop", "sfx_offset": 0.4},
    {"id": "scene3", "text": "Iske liye ek se dedh lakh ka naya app banane ki zaroorat nahi.", "sfx": "stamp", "sfx_offset": 2.4},
    {"id": "scene4", "text": "Step 1: Capacitor naam ka open source framework aapki website ko real app mein wrap karta hai.", "sfx": "whoosh", "sfx_offset": 0.2},
    {"id": "scene5", "text": "Step 2: Notifications, camera aur location jaise native features add karo, bilkul real app jaisa feel.", "sfx": "pop", "sfx_offset": 0.2},
    {"id": "scene6", "text": "Step 3: Play Store aur App Store par publish karo. Video save karo aur share karo!", "sfx": "whoosh", "sfx_offset": 0.2}
]

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())

def generate_sfx():
    # 1. Whoosh SFX (Filtered pink noise sweep)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.35",
        "-af", "bandpass=f=800:width_type=h:w=1200,afade=t=in:ss=0:d=0.15,afade=t=out:st=0.2:d=0.25",
        "sfx_whoosh.wav"
    ], check=True)
    # 2. Pop SFX (Pitch drop sine wave)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=650:d=0.12",
        "-af", "asetrate=44100*0.65,aresample=44100,afade=t=out:st=0.04:d=0.08,volume=0.5",
        "sfx_pop.wav"
    ], check=True)
    # 3. Heavy Stamp Impact SFX
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=110:d=0.28",
        "-af", "afade=t=out:st=0.05:d=0.23,volume=0.85",
        "sfx_stamp.wav"
    ], check=True)

generate_sfx()

timeline = []
current_time = 0.0
voice_files = []
sfx_inputs = []
filter_complex = []

for idx, sc in enumerate(scenes):
    v_file = f"voice_{idx}.mp3"
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")

    if provider == "elevenlabs" and api_key:
        # Ultra-realistic multilingual voice (Adam / Brian)
        url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        data = {
            "text": sc["text"],
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.80, "style": 0.35}
        }
        r = requests.post(url, json=data, headers=headers)
        with open(v_file, "wb") as f:
            f.write(r.content)
    else:
        # Free fallback with faster rate & natural pitch
        subprocess.run([
            "edge-tts", "--voice", "hi-IN-MadhurNeural",
            "--rate=+12%", "--pitch=+2Hz",
            "--text", sc["text"], "--write-media", v_file
        ], check=True)

    dur = get_duration(v_file) + 0.35  # 0.35s breathing gap between scenes
    padded_v = f"padded_{idx}.wav"
    subprocess.run([
        "ffmpeg", "-y", "-i", v_file,
        "-af", f"apad=whole_dur={dur}", padded_v
    ], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "id": sc["id"],
        "start": round(current_time, 3),
        "duration": round(dur, 3)
    })

    # Schedule SFX
    sfx_time_ms = int((current_time + sc["sfx_offset"]) * 1000)
    sfx_inputs.extend(["-i", f"sfx_{sc['sfx']}.wav"])
    sfx_idx = len(sfx_inputs) // 2
    filter_complex.append(f"[{sfx_idx}:a]adelay={sfx_time_ms}|{sfx_time_ms}[s{idx}]")

    current_time += dur

# Concatenate all voice segments
with open("vlist.txt", "w") as f:
    for vf in voice_files:
        f.write(f"file '{vf}'\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "vlist.txt", "full_voice.wav"], check=True)

# Mix full voice + all timed SFX
mix_inputs = "".join([f"[s{i}]" for i in range(len(scenes))])
filter_str = ";".join(filter_complex) + f";[0:a]{mix_inputs}amix=inputs={len(scenes)+1}:duration=first:normalize=0[out]"

subprocess.run([
    "ffmpeg", "-y", "-i", "full_voice.wav", *sfx_inputs,
    "-filter_complex", filter_str, "-map", "[out]", "final_audio.m4a"
], check=True)

with open("timeline.json", "w") as f:
    json.dump({"total_duration": round(current_time, 3), "scenes": timeline}, f, indent=2)

print("Audio & Timeline generated successfully!")
