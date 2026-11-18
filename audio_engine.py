import sys
import subprocess
import json
import os
import time
import requests

provider = sys.argv[1] if len(sys.argv) > 1 else "edge"

scenes = [
    {
        "id": "scene1",
        "text": "Ek client ka message aaya... Humein apna khud ka AI customer support app chahiye, jo 24 ghante reply kare.",
        "sfx": [
            {"type": "type", "offset": 0.1},
            {"type": "pop", "offset": 1.8},
            {"type": "whoosh", "offset": 3.4}
        ]
    },
    {
        "id": "scene2",
        "text": "Pehli baar suno toh lagta hai... Mushkil? Lekin yeh 100 percent possible hai. Bas sahi system chahiye.",
        "sfx": [
            {"type": "whoosh", "offset": 0.2},
            {"type": "stamp", "offset": 2.4}
        ]
    },
    {
        "id": "scene3",
        "text": "Hum ise 3 smart layers mein banate hain. Pehli layer: WhatsApp aur Instagram API, jisse har message turant aata hai.",
        "sfx": [
            {"type": "whoosh", "offset": 0.1},
            {"type": "pop", "offset": 2.5},
            {"type": "pop", "offset": 3.8}
        ]
    },
    {
        "id": "scene4",
        "text": "Doosri layer: AI Brain aur Knowledge Base. Yeh aapke business ka data padhkar sirf 1 second mein exact jawab deta hai.",
        "sfx": [
            {"type": "whoosh", "offset": 0.1},
            {"type": "ping", "offset": 2.8}
        ]
    },
    {
        "id": "scene5",
        "text": "Teesri layer: Auto-Booking aur Payment. Customer chat ke andar hi order book aur pay kar deta hai, bina kisi staff ke.",
        "sfx": [
            {"type": "whoosh", "offset": 0.1},
            {"type": "ping", "offset": 2.2},
            {"type": "ping", "offset": 3.2}
        ]
    },
    {
        "id": "scene6",
        "text": "Result? Zero missed leads, aur mahine ke hazaron ghante bachte hain. Aapko bhi aisa system chahiye? Toh comment karo AI!",
        "sfx": [
            {"type": "whoosh", "offset": 0.1},
            {"type": "type", "offset": 3.8},
            {"type": "pop", "offset": 5.0}
        ]
    }
]

def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())

def generate_sfx_bank():
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.40:c=pink:a=0.40",
        "-af", "bandpass=f=750:width_type=h:w=1100,afade=t=in:ss=0:d=0.12,afade=t=out:st=0.18:d=0.22",
        "sfx_whoosh.wav"
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=720:d=0.11",
        "-af", "asetrate=44100*0.62,aresample=44100,afade=t=out:st=0.03:d=0.08,volume=0.55",
        "sfx_pop.wav"
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=95:d=0.30",
        "-af", "afade=t=out:st=0.04:d=0.26,volume=0.95",
        "sfx_stamp.wav"
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1046:d=0.22",
        "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.06:d=0.16,volume=0.45",
        "sfx_ping.wav"
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.06:c=white:a=0.35",
        "-af", "highpass=f=1800,afade=t=out:st=0.01:d=0.05",
        "sfx_type.wav"
    ], check=True)

def run_edge_tts_with_retry(text, out_file):
    for attempt in range(5):
        res = subprocess.run([
            "edge-tts", "--voice", "hi-IN-MadhurNeural",
            "--rate=+16%", "--pitch=-2Hz",
            "--text", text, "--write-media", out_file
        ])
        if res.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 500:
            return
        print(f"TTS retry {attempt + 1}/5 for {out_file}...")
        time.sleep(2.5)
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
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")

    if provider == "elevenlabs" and api_key:
        url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        data = {
            "text": sc["text"],
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.42, "similarity_boost": 0.82, "style": 0.45}
        }
        r = requests.post(url, json=data, headers=headers)
        with open(v_file, "wb") as f:
            f.write(r.content)
    else:
        raw_v = f"raw_voice_{idx}.mp3"
        run_edge_tts_with_retry(sc["text"], raw_v)
        time.sleep(1.5)
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_v,
            "-af", "equalizer=f=140:width_type=h:width=100:g=4,equalizer=f=3500:width_type=h:width=1500:g=3,acompressor=threshold=-18dB:ratio=3:attack=5:release=50",
            v_file
        ], check=True)

    dur = get_duration(v_file) + 0.30
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

    for s in sc["sfx"]:
        sfx_time_ms = int((current_time + s["offset"]) * 1000)
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
    "-af", "lowpass=f=280,afade=t=in:ss=0:d=0.8,afade=t=out:st=" + str(max(0.5, current_time - 0.8)) + ":d=0.8",
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

print("Studio Voice + SFX + BGM generated!")
