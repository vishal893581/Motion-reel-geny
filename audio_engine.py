import sys
import subprocess
import json
import os
import time
import re
import random
import requests

raw_topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "liam_ref"
theme_mode = sys.argv[3].strip() if len(sys.argv) > 3 else "kinetic_16x9"

rng = random.SystemRandom()
HISTORY_FILE = "used_topics.txt"


def load_used_topics():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def save_used_topic(topic_title):
    clean_t = topic_title.strip()
    if not clean_t:
        return
    used = load_used_topics()
    if clean_t.lower() not in [u.lower() for u in used]:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(clean_t + "\n")


EDUCATIONAL_PACKS = [
    {
        "topic_title": "Salary Aate Hi 10 Tareekh Ko Khatam: 50-30-20 Smart Money Rule",
        "thumb_hero": "SALARY",
        "thumb_sub": "50-30-20 Smart Money Rule",
        "thumb_badge": "₹420 LEFT",
        "ig_caption": "Salary aate hi 10 tareekh ko khatam ho jaati hai? Yeh 50-30-20 Money Rule aaj se lagao!\n\nSave karo aur apne dost ko bhejo.\n\n#personalfinance #salary #savingtips #moneyrules #sochbadlo",
        "beats": [
            {"tts": "सैलरी एक तारीख को आती है... और दस तारीख तक अकाउंट फिर से खाली हो जाता है?", "hero": "SALARY", "hero_color": "maroon", "sub": "10 tareekh ko hi khatam ho jaati hai?", "pill": "khaali", "bg": "cream", "wipe": False, "visual": "wallet_empty", "v_title": "10TH OF MONTH", "v_data": "₹32,000|₹420", "v_sub": "account drained"},
            {"tts": "क्योंकि तुम खर्च करने के बाद बचाते हो... जबकि अमीर लोग बचाने के बाद खर्च करते हैं!", "hero": "ULTE RULE", "hero_color": "orange", "sub": "se chaloge toh kabhi nahi bachega!", "pill": "rule", "bg": "cream", "wipe": True, "visual": "compare_bars", "v_title": "SAVING HABIT", "v_data": "Aam: Spend First|Smart: Save First", "v_sub": "flip the order"},
            {"tts": "आज से पचास-तीस-बीस का ये सिंपल रूल अपनी सैलरी पर लगाओ।", "hero": "50-30-20", "hero_color": "cream", "sub": "ka simple formula aaj se lagao!", "pill": "FORMULA", "bg": "maroon", "wipe": True, "visual": "donut_split", "v_title": "SALARY SPLIT", "v_data": "50% Needs|30% Wants|20% Invest", "v_sub": "100% control"},
            {"tts": "पहला हिस्सा पचास परसेंट... सिर्फ ज़रूरी खर्चों के लिए। रेंट, राशन, बिजली और घर की ईएमआई।", "hero": "50% NEEDS", "hero_color": "maroon", "sub": "sirf zaroori kharchon ke liye rakho.", "pill": "PART 01", "bg": "cream", "wipe": False, "visual": "checklist", "v_title": "50% NEEDS", "v_data": "House Rent|Ration & Bills|Essential EMI", "v_sub": "fixed limit"},
            {"tts": "दूसरा हिस्सा तीस परसेंट... तुम्हारे शौक और लाइफस्टाइल के लिए। बाहर खाना, शॉपिंग और घूमना।", "hero": "30% WANTS", "hero_color": "orange", "sub": "shauk aur lifestyle ke liye rakho.", "pill": "PART 02", "bg": "cream", "wipe": True, "visual": "grid4", "v_title": "30% LIFESTYLE", "v_data": "Dining Out|Shopping|Movies|Weekend Trip", "v_sub": "guilt-free fun"},
            {"tts": "तीसरा हिस्सा बीस परसेंट... सैलरी आते ही सबसे पहले अलग अकाउंट में इन्वेस्ट कर दो!", "hero": "20% INVEST", "hero_color": "maroon", "sub": "salary aate hi pehle alag karo!", "pill": "PART 03", "bg": "cream", "wipe": False, "visual": "growth_chart", "v_title": "AUTO INVEST", "v_data": "Yr 1: ₹60K|Yr 5: ₹4.1L|Yr 10: ₹11.6L", "v_sub": "pay yourself first"},
            {"tts": "बिना सोचे ईएमआई पर नया फोन लेना बंद करो... वरना पूरी जवानी किश्तों में निकल जाएगी!", "hero": "EMI TRAP", "hero_color": "cream", "sub": "mein mat phanso, dikhawa band karo!", "pill": "WARNING", "bg": "maroon", "wipe": True, "visual": "trap_cross", "v_title": "DEBT TRAP", "v_data": "0% EMI Phone", "v_sub": "wealth killer"},
            {"tts": "अगर तुम हर महीने सिर्फ पाँच हज़ार भी बचाते हो... तो दस साल में वो बारह लाख से ऊपर बन जाता है।", "hero": "₹12 LAKH+", "hero_color": "orange", "sub": "sirf ₹5,000 mahina bachane se banta hai!", "pill": "compounding", "bg": "cream", "wipe": False, "visual": "coin_stack", "v_title": "₹5,000 / MONTH", "v_data": "Invested: ₹6L|Value: ₹12.4L", "v_sub": "compounding magic"},
            {"tts": "इस रूल को अभी सेव करो... अगली सैलरी पर यही फॉलो करना है!", "hero": "SAVE", "hero_color": "orange", "sub": "karo agli salary ke liye!", "pill": "salary", "bg": "cream", "wipe": False, "visual": "save", "v_title": "50-30-20 RULE", "v_data": "SAVED", "v_sub": "@sochbadlo.hq"},
            {"tts": "शेयर करो अपने उस दोस्त को जिसकी सैलरी भी दस तारीख को गायब हो जाती है!", "hero": "SHARE", "hero_color": "maroon", "sub": "karo apne kharchile dost ko!", "pill": "dost", "bg": "cream", "wipe": True, "visual": "share", "v_title": "SEND TO", "v_data": "Salary Friend", "v_sub": "tag him now"},
            {"tts": "कमेंट में बताओ... तुम्हारी सैलरी किस तारीख तक चलती है?", "hero": "COMMENT", "hero_color": "orange", "sub": "me batao kitne din chalti hai salary?", "pill": "batao", "bg": "cream", "wipe": False, "visual": "comment", "v_title": "COMMENT", "v_data": "Meri salary toh...", "v_sub": "reply below"}
        ]
    },
    {
        "topic_title": "Public Speaking Fear: Stage Par Bina Dare Bolne Ka 3-Step Formula",
        "thumb_hero": "STAGE FEAR",
        "thumb_sub": "Bina Dare Bolne Ka Formula",
        "thumb_badge": "3 STEPS",
        "ig_caption": "Logon ke saamne bolte waqt haath kaampte hain? Yeh 3-Step Formula try karo!\n\nSave karo aur apne shy dost ko bhejo.\n\n#publicspeaking #confidence #communication #personality #sochbadlo",
        "beats": [
            {"tts": "दस लोगों के सामने माइक पकड़ते ही... गला सूखने लगता है और आवाज़ काँपने लगती है?", "hero": "STAGE FEAR", "hero_color": "maroon", "sub": "mic pakadte hi awaaz kaampne lagti hai?", "pill": "kaampne", "bg": "cream", "wipe": False, "visual": "mic_wave", "v_title": "STAGE PANIC", "v_data": "Heart: 135 BPM", "v_sub": "nervous voice"},
            {"tts": "याद रखो... ऑडियंस तुम्हारी गलतियाँ गिनने नहीं बैठी, वो बस कुछ नया सुनने आई है!", "hero": "DARO MAT", "hero_color": "maroon", "strike": True, "sub": "audience tumhari dushman nahi hai!", "pill": "audience", "bg": "cream", "wipe": True, "visual": "bubble", "v_title": "MINDSET SHIFT", "v_data": "They want you to win!", "v_sub": "relax shoulders"},
            {"tts": "आज से स्पीकिंग का पी-एस-ई रूल अपनाओ।", "hero": "P-S-E RULE", "hero_color": "cream", "sub": "se koi bhi speech easy ban jaati hai!", "pill": "FORMULA", "bg": "maroon", "wipe": True, "visual": "grid4", "v_title": "P-S-E METHOD", "v_data": "P: Point|S: Story|E: Example|Action", "v_sub": "zero blank mind"},
            {"tts": "पहला कदम... शुरुआत में तीन सेकंड का पॉज़ लो और सामने तीन लोगों से आई कॉन्टैक्ट बनाओ।", "hero": "3-SEC PAUSE", "hero_color": "orange", "sub": "lekar pehle eye contact banao!", "pill": "STEP 01", "bg": "cream", "wipe": False, "visual": "eye_triangle", "v_title": "EYE TRIANGLE", "v_data": "Left|Center|Right", "v_sub": "instant confidence"},
            {"tts": "दूसरा कदम... रट्टा मार के मत बोलो, सिर्फ तीन बुलेट पॉइंट्स याद रखो।", "hero": "NO RATTA", "hero_color": "cream", "sub": "sirf 3 bullet points yaad rakho!", "pill": "STEP 02", "bg": "maroon", "wipe": True, "visual": "trap_cross", "v_title": "AVOID THIS", "v_data": "Word-by-Word Script", "v_sub": "causes forgetting"},
            {"tts": "तीसरा कदम... अपनी हर बात के बाद एक छोटा सा रियल लाइफ एग्ज़ाम्पल जोड़ दो।", "hero": "EXAMPLE DO", "hero_color": "maroon", "sub": "jodne se log tumhe dhyan se sunenge!", "pill": "STEP 03", "bg": "cream", "wipe": False, "visual": "checklist", "v_title": "SPEECH FLOW", "v_data": "Clear Hook|Real Story|Strong Ending", "v_sub": "high engagement"},
            {"tts": "तेज़ बोलने की जल्दी मत करो... स्लो और क्लियर बोलने वाले लोग ज़्यादा कॉन्फिडेंट लगते हैं।", "hero": "SLOW PACE", "hero_color": "orange", "sub": "aur clear bolne se authority dikhti hai!", "pill": "clear", "bg": "cream", "wipe": True, "visual": "compare_bars", "v_title": "SPEAKING SPEED", "v_data": "Fast: Nervous|Calm: Leader", "v_sub": "control pace"},
            {"tts": "इस फॉर्मूले को सेव करो... अगली प्रेज़ेंटेशन या इंटरव्यू से पहले काम आएगा!", "hero": "SAVE", "hero_color": "orange", "sub": "karo agli presentation ke liye!", "pill": "interview", "bg": "cream", "wipe": False, "visual": "save", "v_title": "P-S-E FORMULA", "v_data": "SAVED", "v_sub": "@sochbadlo.hq"},
            {"tts": "शेयर करो अपने उस दोस्त को जो क्लास या मीटिंग में सबसे पीछे छुपता है!", "hero": "SHARE", "hero_color": "maroon", "sub": "karo apne shy dost ko abhi!", "pill": "dost", "bg": "cream", "wipe": True, "visual": "share", "v_title": "SEND TO", "v_data": "Shy Friend", "v_sub": "boost his confidence"},
            {"tts": "कमेंट में बताओ... तुम्हें किस चीज़ से सबसे ज़्यादा डर लगता है?", "hero": "COMMENT", "hero_color": "orange", "sub": "me batao apna sabse bada fear!", "pill": "batao", "bg": "cream", "wipe": False, "visual": "comment", "v_title": "COMMENT", "v_data": "Mujhe dar lagta hai...", "v_sub": "reply below"}
        ]
    }
]

used_history = load_used_topics()
unused_packs = [p for p in EDUCATIONAL_PACKS if p["topic_title"].lower() not in [u.lower() for u in used_history]]
chosen_pack = rng.choice(unused_packs if unused_packs else EDUCATIONAL_PACKS)

TEACHING_CATEGORIES = [
    "Practical Study & Exam Hacks for Indian Students (Step-by-Step Crash Plans)",
    "High-Income Skills & Career Roadmaps for 18-28 Indian Youth (Actionable Steps)",
    "Smart Personal Finance, Salary Rules & Avoiding Debt Traps in India",
    "Communication, Public Speaking & Daily Productivity Frameworks (3-Step Practical Rules)",
    "Consumer Rights, Banking Rules & Everyday Smart Life Hacks Every Indian Must Know"
]
chosen_category = rng.choice(TEACHING_CATEGORIES)
print(f"V24.1 Liam Voice + Trending BGM + Word-Sync Highlight Engine | Category: {chosen_category} | Past Topics: {len(used_history)}")


def build_prompt(explicit_topic, past_topics, category_hint):
    avoid_block = ""
    if past_topics:
        recent_list = "\n".join(f"- {t}" for t in past_topics[-65:])
        avoid_block = f"""
STRICT ANTI-DUPLICATE RULE:
You MUST NOT repeat or closely resemble ANY of these previously used topics:
{recent_list}
"""

    topic_instruction = (
        f'Create an educational, step-by-step Hinglish video specifically on: "{explicit_topic}"'
        if explicit_topic
        else f'Invent ONE brand-new, ultra-practical, high-save Indian educational/teaching topic in "{category_hint}" that teaches viewers a concrete 3-step method, crash plan, skill roadmap, or smart rule! Never repeat any topic in the list above.'
    )

    return f"""You are a viral Indian educational motion-graphics creator (like @sochbadlo.hq).
{topic_instruction}
{avoid_block}

Write a fast-paced, high-retention 10 to 12 beat Hinglish educational script (45 to 58 seconds total -> 8 to 13 spoken words per beat) that genuinely TEACHES something actionable step-by-step and ends with a strong SAVE + SHARE + COMMENT call-to-action!

CRITICAL RULE FOR VISUAL DIVERSITY (NO REPEATED BOXES):
Every single beat MUST choose a DIFFERENT, topic-matched visual diagram from the 15 specialized vector visual types below so consecutive beats NEVER look the same:
1. "wallet_empty" -> Money/salary drain bar (`v_data`: "₹32,000|₹420")
2. "donut_split" -> Proportional percentage breakdown ring (`v_data`: "50% Needs|30% Wants|20% Invest")
3. "growth_chart" -> Upward compounding/career/skill growth bars (`v_data`: "Yr 1: ₹60K|Yr 5: ₹4.1L|Yr 10: ₹11.6L")
4. "coin_stack" -> Savings/wealth stack comparison (`v_data`: "Invested: ₹6L|Value: ₹12.4L")
5. "mic_wave" -> Audio waveform & heart-rate/stress meter (`v_data`: "Heart: 135 BPM")
6. "eye_triangle" -> 3-point focus / triangle diagram (`v_data`: "Left|Center|Right")
7. "timer" -> Digital countdown / deadline clock (`v_data`: "23:28:13" or "90 DAYS")
8. "clock" -> Analog clock face (`v_data`: "07:30 AM")
9. "compare_bars" -> Side-by-side A vs B comparison (`v_data`: "Bad Habit: Slow|Smart Rule: 3x")
10. "grid4" -> 4-quadrant breakdown box (`v_data`: "Item 1|Item 2|Item 3|Item 4")
11. "checklist" -> 3-step animated checkmark list (`v_data`: "Step 1|Step 2|Step 3")
12. "bubble" -> Character avatar with speech bubble quote (`v_data`: "Short spoken quote")
13. "phone" -> Smartphone screen illustration (`v_data`: "REELS TRAP")
14. "trap_cross" -> Red-orange crossed-out warning card (`v_data`: "Mistake to avoid")
15. "none" -> Pure giant 3D kinetic typography without any side card (use on 1-2 punch beats!)
And for the final 3 CTA beats ONLY, use: "save", "share", "comment".

For EACH beat in "beats" array, return:
- "tts": Natural Devanagari Hindi with English terms written phonetically in Devanagari (e.g., 'एग्जाम', 'सिलेबस', 'स्किल', 'सैलरी') and natural pauses (`...`).
- "hero": 1 to 2 BIG UPPERCASE PUNCH WORDS in Hinglish/English (MAX 13 chars).
- "hero_color": "maroon" or "orange" (when bg is "cream"), or "cream" (when bg is "maroon").
- "strike": boolean (true ONLY when crossing out a bad habit, otherwise false).
- "sub": Short clean Roman Hinglish continuation phrase (MAX 38 chars).
- "pill": Single keyword from "sub" (MAX 14 chars) to highlight inside a maroon pill badge.
- "bg": "cream" (~80% of beats) or "maroon" (2-3 dramatic warning/step header beats).
- "wipe": boolean (true on ~45% of beats for diagonal maroon-gold wipe transitions).
- "visual": Exact visual type name chosen from the list above (NEVER repeat the same visual in two back-to-back beats!).
- "v_title": Short uppercase header matching that beat's topic (MAX 15 chars).
- "v_data": Specific numbers, labels, or pipe-separated items directly reflecting what is spoken in THAT beat (MAX 42 chars).
- "v_sub": Tiny bottom caption matching that beat (MAX 20 chars).

Return ONLY valid JSON:
{{
  "topic_title": "Short unique Roman Hinglish title (6-10 words)",
  "thumb_hero": "1-2 word big cover title (MAX 12 chars)",
  "thumb_sub": "4-5 word cover subtitle (MAX 32 chars)",
  "thumb_badge": "Short cover badge value (MAX 12 chars)",
  "ig_caption": "Engaging 3-line Hinglish caption with Save/Share/Comment prompt + 5 hashtags",
  "beats": [ ... 10 to 12 beat objects ... ]
}}"""


def call_gemini_reliable(gemini_key, prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.90}
    }
    models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.0-flash", "gemini-flash-latest"]
    for model_name in models:
        endpoints = [
            (f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}", {"Content-Type": "application/json"}),
            (f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent", {"Content-Type": "application/json", "x-goog-api-key": gemini_key})
        ]
        for url, hdrs in endpoints:
            try:
                resp = requests.post(url, headers=hdrs, json=payload, timeout=35)
                if resp.status_code != 200:
                    print(f"Gemini {model_name} HTTP {resp.status_code}: {resp.text[:200]}")
                    continue
                r_json = resp.json()
                raw = r_json["candidates"][0]["content"]["parts"][0]["text"]
                raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
                data = json.loads(raw)
                if isinstance(data, dict) and "beats" in data and len(data["beats"]) >= 8:
                    print(f"SUCCESS! Gemini generated {len(data['beats'])}-beat script via {model_name}!")
                    return data
            except Exception as e:
                print(f"Gemini {model_name} retry:", e)
    return None


def generate_script():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        prompt = build_prompt(raw_topic, used_history, chosen_category)
        data = call_gemini_reliable(gemini_key, prompt)
        if data:
            title = data.get("topic_title") or raw_topic or f"Smart Lesson #{len(used_history)+1}"
            save_used_topic(title)
            if data.get("ig_caption"):
                with open("caption.txt", "w", encoding="utf-8") as cf:
                    cf.write(data["ig_caption"].strip())
            return data

    title = chosen_pack["topic_title"]
    save_used_topic(title)
    with open("caption.txt", "w", encoding="utf-8") as cf:
        cf.write(chosen_pack["ig_caption"])
    print(f"Using built-in educational pack: {title}")
    return chosen_pack


script_data = generate_script()
beats = script_data["beats"]


def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())


def generate_sfx_and_trending_bgm(total_sec):
    """100% compatible FFmpeg command building a crisp 2-second melodic pluck + beat loop and repeating it cleanly."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.18:c=pink:a=0.36",
        "-af", "bandpass=f=880:width_type=h:w=750,afade=t=in:ss=0:d=0.03,afade=t=out:st=0.06:d=0.12",
        "sfx_whoosh.wav"
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=760:d=0.065",
        "-af", "afade=t=out:st=0.01:d=0.055,volume=0.38",
        "sfx_pop.wav"
    ], check=True)

    # Build 4 melodic marimba/pluck notes + soft kick/hat pulse in a 2.0s bar, then loop for full video
    notes = [(220.0, 0), (261.63, 500), (329.63, 1000), (293.66, 1500)]
    for i, (freq, _) in enumerate(notes):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=f={freq}:d=0.38",
            "-af", "afade=t=in:ss=0:d=0.015,afade=t=out:st=0.08:d=0.30,volume=0.065",
            f"note_{i}.wav"
        ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=95:d=0.22",
        "-af", "afade=t=out:st=0.02:d=0.20,volume=0.075",
        "kick.wav"
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.06:c=white:a=0.035",
        "-af", "highpass=f=4000,afade=t=out:st=0.01:d=0.05",
        "hat.wav"
    ], check=True)

    bar_fc = (
        "[0:a]apad=whole_dur=2.0[n0];"
        "[1:a]adelay=500|500,apad=whole_dur=2.0[n1];"
        "[2:a]adelay=1000|1000,apad=whole_dur=2.0[n2];"
        "[3:a]adelay=1500|1500,apad=whole_dur=2.0[n3];"
        "[4:a]apad=whole_dur=2.0[k0];"
        "[4:a]adelay=1000|1000,apad=whole_dur=2.0[k1];"
        "[5:a]adelay=250|250,apad=whole_dur=2.0[h0];"
        "[5:a]adelay=750|750,apad=whole_dur=2.0[h1];"
        "[5:a]adelay=1250|1250,apad=whole_dur=2.0[h2];"
        "[5:a]adelay=1750|1750,apad=whole_dur=2.0[h3];"
        "[n0][n1][n2][n3][k0][k1][h0][h1][h2][h3]amix=inputs=10:duration=first:normalize=0[bar]"
    )
    subprocess.run([
        "ffmpeg", "-y",
        "-i", "note_0.wav", "-i", "note_1.wav", "-i", "note_2.wav", "-i", "note_3.wav",
        "-i", "kick.wav", "-i", "hat.wav",
        "-filter_complex", bar_fc, "-map", "[bar]", "bgm_bar.wav"
    ], check=True)

    dur = round(total_sec + 1.0, 2)
    fade_out_st = round(max(0.5, total_sec - 0.5), 2)
    subprocess.run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", "bgm_bar.wav",
        "-t", str(dur),
        "-af", f"afade=t=in:ss=0:d=0.4,afade=t=out:st={fade_out_st}:d=0.5",
        "bgm.wav"
    ], check=True)


def generate_elevenlabs_tts(text, out_file):
    el_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not el_key:
        print("WARNING: ELEVENLABS_API_KEY not found in secrets!")
        return False

    # ElevenLabs "Liam" (TX3LPaxmHKxFdv7VOQHJ) -> fallback "Antoni" (ErXwobaYiN019PkySvjV)
    voice_ids = ["TX3LPaxmHKxFdv7VOQHJ", "ErXwobaYiN019PkySvjV"]
    headers = {"xi-api-key": el_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.38,
            "similarity_boost": 0.86,
            "style": 0.58,
            "use_speaker_boost": True
        }
    }
    for vid in voice_ids:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
        for attempt in range(3):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=30)
                if r.status_code == 200 and len(r.content) > 1000:
                    with open(out_file, "wb") as f:
                        f.write(r.content)
                    return True
                print(f"ElevenLabs {vid} HTTP {r.status_code}: {r.text[:160]}")
                if r.status_code in (401, 402):
                    return False
            except Exception as e:
                print("ElevenLabs retry:", e)
            time.sleep(1.2)
    return False


def run_edge_tts_fallback(text, out_file):
    for _ in range(5):
        res = subprocess.run([
            "edge-tts", "--voice", "hi-IN-MadhurNeural",
            "--rate", "+14%", "--pitch", "+1Hz",
            "--text", text, "--write-media", out_file
        ])
        if res.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 500:
            return
        time.sleep(1.5)
    raise RuntimeError(f"Failed TTS for {out_file}")


timeline = []
current_time = 0.0
voice_files = []
sfx_inputs = []
filter_complex = []
sfx_counter = 0

for idx, b in enumerate(beats):
    v_file = f"voice_{idx}.mp3"
    raw_v = f"raw_voice_{idx}.mp3"
    tts_text = b.get("tts", b.get("sub", ""))

    if generate_elevenlabs_tts(tts_text, raw_v):
        af_str = "atempo=1.11,highpass=f=85,equalizer=f=160:width_type=h:width=110:g=2.4,equalizer=f=3500:width_type=h:width=1400:g=3.0,acompressor=threshold=-16dB:ratio=2.4:attack=5:release=55"
    else:
        run_edge_tts_fallback(tts_text, raw_v)
        af_str = "highpass=f=85,equalizer=f=175:width_type=h:width=110:g=2.6,equalizer=f=3400:width_type=h:width=1400:g=2.8,acompressor=threshold=-16dB:ratio=2.5:attack=5:release=55"

    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)
    dur = get_duration(v_file) + 0.12
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    vis = str(b.get("visual") or b.get("card") or "none").lower()
    timeline.append({
        "index": idx,
        "start": round(current_time, 3),
        "duration": round(dur, 3),
        "hero": str(b.get("hero", "STEP")).upper()[:14],
        "hero_color": str(b.get("hero_color", "maroon")).lower(),
        "strike": bool(b.get("strike", False)),
        "sub": str(b.get("sub", ""))[:44],
        "pill": str(b.get("pill", ""))[:16],
        "bg": str(b.get("bg", "cream")).lower(),
        "wipe": bool(b.get("wipe", idx % 2 == 1)),
        "visual": vis,
        "v_title": str(b.get("v_title") or b.get("card_title") or "")[:16],
        "v_data": str(b.get("v_data") or b.get("card_val") or "")[:44],
        "v_sub": str(b.get("v_sub") or b.get("card_sub") or "")[:22]
    })

    ms1 = int((current_time + 0.02) * 1000)
    sfx_inputs.extend(["-i", "sfx_whoosh.wav"])
    sfx_counter += 1
    filter_complex.append(f"[{sfx_counter}:a]adelay={ms1}|{ms1}[s{sfx_counter}]")

    if vis != "none":
        ms2 = int((current_time + min(0.24, dur * 0.32)) * 1000)
        sfx_inputs.extend(["-i", "sfx_pop.wav"])
        sfx_counter += 1
        filter_complex.append(f"[{sfx_counter}:a]adelay={ms2}|{ms2}[s{sfx_counter}]")

    current_time += dur

generate_sfx_and_trending_bgm(current_time)

with open("vlist.txt", "w") as f:
    for vf in voice_files:
        f.write(f"file '{vf}'\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "vlist.txt", "full_voice.wav"], check=True)

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
        "thumb_hero": str(script_data.get("thumb_hero", "STUDY PLAN")).upper()[:13],
        "thumb_sub": str(script_data.get("thumb_sub", "3-Step Smart Formula"))[:34],
        "thumb_badge": str(script_data.get("thumb_badge", "3 STEPS"))[:13],
        "beats": timeline
    }, f, indent=2)

print(f"V24.1 Liam Voice + Trending BGM + Dynamic Word-Sync Ready! ({round(current_time, 2)}s)")
