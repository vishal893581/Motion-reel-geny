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
    "Daily small-spend leaks (chai, Swiggy/Zomato, UPI, subscriptions) and what they cost over 10 years",
    "Salary rules for Indian 20-30 year olds (50/30/20, emergency fund, first salary mistakes, lifestyle inflation)",
    "Middle-class money traps in India (EMI, credit card minimum due, BNPL, festive sale psychology)",
    "Rich vs middle-class money habits (assets vs liabilities, paying yourself first, compounding with small SIP numbers)",
    "Everyday banking/UPI/tax facts every Indian salaried person should know (education only, no stock tips)"
]
chosen_category = rng.choice(TEACHING_CATEGORIES)
print(f"V24 Liam Voice + Trending BGM + Word-Sync Highlight Engine | Category: {chosen_category} | Past Topics: {len(used_history)}")


SERIES_NAME = os.environ.get("SERIES_NAME", "").strip() or "PAISA REALITY"
SERIES_FILE = "series_day.txt"


def read_series_day():
    try:
        return int(open(SERIES_FILE).read().strip())
    except Exception:
        return 0


NEXT_DAY = read_series_day() + 1


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
        else f'Invent ONE brand-new, scroll-stopping Indian personal-finance topic (with a surprising number in the hook) in "{category_hint}" that teaches viewers one concrete rule they can use today! Never repeat any topic in the list above.'
    )

    return f"""You are a viral Indian educational motion-graphics creator (like @sochbadlo.hq).
{topic_instruction}
{avoid_block}

Write a fast-paced, high-retention 8 to 10 beat Hinglish money-education script (32 to 42 seconds total -> 7 to 11 spoken words per beat).

HOOK RULES (most important - viewers decide in 2 seconds):
- Beat 1 MUST open with a shocking, specific NUMBER or loss in <= 8 spoken words (e.g. "Roz ka 300 rupaye Swiggy... 10 saal mein 11 lakh ka nuksaan"). No greetings, no "aaj hum seekhenge", no intro.
- Beat 2 must deepen the curiosity or show the maths. Never reveal the full answer before the last third.
- Use real, checkable maths (state the assumed return, e.g. 12% p.a. compounding, in the card). Never invent fake statistics.
- Last 2 beats: one practical rule they can do today, then ONE call-to-action built around SHARE/SEND ("Yeh us dost ko bhejo jo roz ... karta hai") + save.
- EDUCATION ONLY: never recommend a specific stock, mutual fund, broker or app, and never promise returns (SEBI rules).

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
- "cap": The SAME sentence as "tts" written in Roman Hinglish, SAME words in the SAME order, ONE Roman word per spoken Hindi word (no extra words, no ellipsis, no punctuation inside words). This is shown as live captions, so keep it clean.
- "hero": 1 to 2 BIG UPPERCASE PUNCH WORDS in Hinglish/English (MAX 11 chars).
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
  "next_teaser": "5-7 word Roman Hinglish teaser for tomorrow's part of the series",
  "ig_caption": "3-line Hinglish caption. Line 1 starts with \"{SERIES_NAME} - Day {NEXT_DAY}\". Last line before hashtags: \"Kal Day {NEXT_DAY+1}: <next_teaser>\". Include a Share/Send prompt + 5 hashtags",
  "beats": [ ... 10 to 12 beat objects ... ]
}}"""


def discover_gemini_models(gemini_key):
    """Ask Google which models THIS key can use (names change often -> never hardcode only)."""
    try:
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/models",
                         params={"key": gemini_key, "pageSize": 200}, timeout=30)
        if r.status_code != 200:
            print(f"Gemini ListModels HTTP {r.status_code}: {r.text[:200]}")
            return []
        found = []
        for m in r.json().get("models", []):
            name = m.get("name", "").replace("models/", "")
            methods = m.get("supportedGenerationMethods", [])
            if "generateContent" not in methods or "flash" not in name:
                continue
            if any(x in name for x in ("image", "tts", "live", "audio", "embedding", "robotics", "computer", "gemma", "exp")):
                continue
            nums = [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)", name)[:1]] or [0.0]
            found.append((-nums[0], 1 if "lite" in name else 0, name))
        found.sort()   # newest version first, full flash before lite
        names = [n for _, _, n in found]
        print("Gemini models available for this key:", names[:10])
        return names
    except Exception as e:
        print("Gemini ListModels error:", e)
        return []


def _parse_json_loose(raw):
    """Gemini sometimes returns almost-JSON (trailing commas, fences, text around it). Repair, then parse."""
    raw = re.sub(r"^```(?:json)?\s*|```\s*$", "", raw.strip(), flags=re.MULTILINE).strip()
    i, j = raw.find("{"), raw.rfind("}")
    if i != -1 and j != -1:
        raw = raw[i:j + 1]
    for candidate in (raw, re.sub(r",\s*([}\]])", r"\1", raw)):
        try:
            return json.loads(candidate)
        except Exception:
            pass
    raise ValueError("unparseable JSON from model")


def call_gemini_reliable(gemini_key, prompt):
    discovered = discover_gemini_models(gemini_key)
    models, seen = [], set()
    for m in [os.environ.get("GEMINI_MODEL", "").strip()] + discovered[:4] + ["gemini-flash-latest", "gemini-2.5-flash"]:
        if m and m not in seen:
            seen.add(m)
            models.append(m)

    for round_no in range(3):                       # whole list again if Google is overloaded
        for model_name in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            hdrs = {"Content-Type": "application/json", "x-goog-api-key": gemini_key}
            for attempt in range(3):
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json",
                                         "temperature": 0.9 if attempt == 0 else 0.6,
                                         "maxOutputTokens": 8192}
                }
                try:
                    resp = requests.post(url, headers=hdrs, json=payload, timeout=60)
                    if resp.status_code == 404:
                        print(f"Gemini {model_name}: 404 (model not available) -> next model")
                        break
                    if resp.status_code in (429, 500, 503):      # overloaded / quota burst -> wait, retry
                        wait = 4 * (attempt + 1) + round_no * 6
                        print(f"Gemini {model_name} HTTP {resp.status_code} (busy). retry in {wait}s")
                        time.sleep(wait)
                        continue
                    if resp.status_code != 200:
                        print(f"Gemini {model_name} HTTP {resp.status_code}: {resp.text[:200]}")
                        break
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = _parse_json_loose(raw)
                    if isinstance(data, dict) and "beats" in data and len(data["beats"]) >= 8:
                        print(f"SUCCESS! Gemini generated {len(data['beats'])}-beat script via {model_name}!")
                        return data
                    print(f"Gemini {model_name}: JSON ok but too few beats, retrying")
                except Exception as e:
                    print(f"Gemini {model_name} retry ({e})")
        time.sleep(5)
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

    if os.environ.get("ALLOW_FALLBACK_PACKS") != "1":
        # old built-in packs are off-niche (study/speaking) -> better to skip a post than publish junk
        raise RuntimeError("Gemini script generation failed - skipping this run (set ALLOW_FALLBACK_PACKS=1 to allow built-in packs).")
    title = chosen_pack["topic_title"]
    save_used_topic(title)
    with open("caption.txt", "w", encoding="utf-8") as cf:
        cf.write(chosen_pack["ig_caption"])
    print(f"Using built-in educational pack: {title}")
    return chosen_pack


script_data = generate_script()
beats = script_data["beats"]
SERIES_DAY = NEXT_DAY
with open(SERIES_FILE, "w") as _sf:
    _sf.write(str(SERIES_DAY))


def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())


def generate_sfx_and_trending_bgm(total_sec):
    """Generates crisp transition whooshes, UI pops, and a punchy, melodic trending lo-fi/marimba background beat (matching reference video)."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.18:c=pink:a=0.36",
        "-af", "bandpass=f=880:width_type=h:w=750,afade=t=in:ss=0:d=0.03,afade=t=out:st=0.06:d=0.12",
        "sfx_whoosh.wav"
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=760:d=0.065",
        "-af", "afade=t=out:st=0.01:d=0.055,volume=0.28",
        "sfx_pop.wav"
    ], check=True)

    # Melodic pluck groove + rhythmic soft hi-hat pulse + warm sub-bass (audible, energetic, non-intrusive)
    dur = total_sec + 1.5
    pluck_expr = (
        "0.048*exp(-5.5*mod(t,0.5))*(sin(2*PI*220*t)+0.45*sin(2*PI*440*t))*lt(mod(t,2.0),0.5)+"
        "0.048*exp(-5.5*mod(t,0.5))*(sin(2*PI*261.63*t)+0.45*sin(2*PI*523.25*t))*between(mod(t,2.0),0.5,1.0)+"
        "0.048*exp(-5.5*mod(t,0.5))*(sin(2*PI*329.63*t)+0.45*sin(2*PI*659.25*t))*between(mod(t,2.0),1.0,1.5)+"
        "0.048*exp(-5.5*mod(t,0.5))*(sin(2*PI*293.66*t)+0.45*sin(2*PI*587.33*t))*gte(mod(t,2.0),1.5)+"
        "0.038*exp(-7.0*mod(t,0.5))*sin(2*PI*110*t)+"
        "0.022*exp(-28.0*mod(t+0.25,0.5))*sin(2*PI*3800*t)"
    )
    res = subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"aevalsrc={pluck_expr}:s=44100:d={dur}",
        "-af", f"lowpass=f=4500,volume=1.35,afade=t=in:ss=0:d=0.4,afade=t=out:st={max(0.5, total_sec - 0.5)}:d=0.5",
        "bgm.wav"
    ])
    if res.returncode != 0:   # never let background music crash a publish
        print("Synth BGM failed -> using silent bed")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(dur), "bgm.wav"], check=True)


def _env_float(name, default):
    try:
        return float(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


_AUTO_VOICE = None


def resolve_auto_voice(el_key):
    """No voice chosen? Pick the most-used Hindi voice in the ElevenLabs library (proven for narration),
    add it to this account once (named SB_auto_...) and reuse it. Set ELEVENLABS_VOICE_ID to override."""
    global _AUTO_VOICE
    if _AUTO_VOICE is not None:
        return _AUTO_VOICE or None
    _AUTO_VOICE = ""
    base = "https://api.elevenlabs.io"
    hdr = {"xi-api-key": el_key}
    gender = (os.environ.get("EL_VOICE_GENDER", "").strip().lower() or "male")
    try:
        r = requests.get(f"{base}/v1/voices", headers=hdr, timeout=30)
        if r.status_code == 200:
            for v in r.json().get("voices", []):
                if str(v.get("name", "")).startswith("SB_auto_"):
                    _AUTO_VOICE = v["voice_id"]
                    print(f"AUTO VOICE (already added): {v.get('name')} -> {_AUTO_VOICE}")
                    return _AUTO_VOICE
        r = requests.get(f"{base}/v1/shared-voices", headers=hdr, timeout=30,
                         params={"language": "hi", "gender": gender, "sort": "usage_character_count_1y", "page_size": 30})
        if r.status_code != 200:
            print(f"AUTO VOICE: library HTTP {r.status_code}: {r.text[:160]}")
            return None
        voices = r.json().get("voices", [])
        nice = {"social_media", "narrative_story", "advertisement", "informative_educational"}
        voices = sorted(voices, key=lambda v: (0 if v.get("free_users_allowed") else 1,
                                               0 if v.get("use_case") in nice else 1))
        for v in voices[:3]:
            vid, owner = v.get("voice_id"), v.get("public_owner_id")
            if not vid or not owner:
                continue
            a = requests.post(f"{base}/v1/voices/add/{owner}/{vid}", timeout=30,
                              headers={**hdr, "Content-Type": "application/json"},
                              json={"new_name": ("SB_auto_" + str(v.get("name", "voice")))[:40]})
            if a.status_code == 200:
                _AUTO_VOICE = a.json().get("voice_id", vid)
                print(f"AUTO VOICE picked: {v.get('name')} ({v.get('accent')}, {v.get('use_case')}) -> {_AUTO_VOICE}")
                return _AUTO_VOICE
            print(f"AUTO VOICE add failed HTTP {a.status_code}: {a.text[:140]}")
    except Exception as e:
        print("AUTO VOICE error:", e)
    return None


def generate_elevenlabs_tts(text, out_file, prev_text="", next_text=""):
    """Returns None on failure, else the alignment dict (character timings) from ElevenLabs.
    Voice is chosen with env ELEVENLABS_VOICE_ID (pick a native Hindi voice from the Voice Library)."""
    import base64
    el_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not el_key:
        print("WARNING: ELEVENLABS_API_KEY not found in secrets!")
        return None

    model_id = os.environ.get("ELEVENLABS_MODEL", "").strip() or "eleven_multilingual_v2"
    primary = os.environ.get("ELEVENLABS_VOICE_ID", "").strip() or resolve_auto_voice(el_key)
    voice_ids = [v for v in [primary, "TX3LPaxmHKxFdv7VOQHJ"] if v]
    headers = {"xi-api-key": el_key, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": _env_float("EL_STABILITY", 0.5),
            "similarity_boost": _env_float("EL_SIMILARITY", 0.8),
            "style": _env_float("EL_STYLE", 0.15),
            "speed": _env_float("EL_SPEED", 1.05),
            "use_speaker_boost": True
        }
    }
    # request-stitching context keeps tone/pace continuous across beats (not supported by v3)
    if not model_id.startswith("eleven_v3"):
        if prev_text:
            payload["previous_text"] = prev_text
        if next_text:
            payload["next_text"] = next_text

    for vid in voice_ids:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_128"
        for attempt in range(3):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=60)
                if r.status_code == 200:
                    j = r.json()
                    audio = base64.b64decode(j.get("audio_base64", ""))
                    if len(audio) > 1000:
                        with open(out_file, "wb") as f:
                            f.write(audio)
                        return j.get("alignment") or j.get("normalized_alignment") or {}
                print(f"ElevenLabs {vid} HTTP {r.status_code}: {r.text[:160]}")
                if r.status_code in (401, 402):
                    return None
                if r.status_code in (400, 404, 422):
                    break  # bad voice id / bad params -> try next voice id
            except Exception as e:
                print("ElevenLabs retry:", e)
            time.sleep(1.2)
    return None


def spoken_word_spans(alignment):
    """[(start, end), ...] per spoken word from ElevenLabs character alignment."""
    try:
        chars = alignment["characters"]
        st = alignment["character_start_times_seconds"]
        en = alignment["character_end_times_seconds"]
    except (KeyError, TypeError):
        return []
    words, cur = [], None
    for c, t0, t1 in zip(chars, st, en):
        if c.isspace():
            if cur:
                words.append(tuple(cur))
                cur = None
        elif cur is None:
            cur = [t0, t1]
        else:
            cur[1] = t1
    if cur:
        words.append(tuple(cur))
    return words


def caption_word_times(spans, cap_text, has_cap):
    """One start time per caption word, following the real voice."""
    n = len(cap_text.split())
    m = len(spans)
    if n == 0 or m == 0:
        return None
    if has_cap:   # cap is word-for-word with the speech -> map by position
        return [round(spans[min(m - 1, int(j * m / n))][0], 3) for j in range(n)]
    t0, t1 = spans[0][0], spans[-1][1]   # short 'sub' phrase -> spread over actual speech
    return [round(t0 + (t1 - t0) * j / n, 3) for j in range(n)]


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

    prev_t = beats[idx - 1].get("tts", "") if idx > 0 else ""
    next_t = beats[idx + 1].get("tts", "") if idx + 1 < len(beats) else ""
    alignment = generate_elevenlabs_tts(tts_text, raw_v, prev_t, next_t)
    word_spans = []
    if alignment is not None:
        word_spans = spoken_word_spans(alignment)
        # natural voice: gentle clean-up only (no speed hack, no harsh presence boost)
        af_str = "highpass=f=80,equalizer=f=180:width_type=h:width=120:g=1.5,equalizer=f=3200:width_type=h:width=1500:g=1.2,acompressor=threshold=-18dB:ratio=2.0:attack=8:release=80"
    else:
        print(f"Beat {idx}: using edge-tts FALLBACK voice (check ElevenLabs key/credits!)")
        run_edge_tts_fallback(tts_text, raw_v)
        af_str = "highpass=f=85,equalizer=f=175:width_type=h:width=110:g=2.6,equalizer=f=3400:width_type=h:width=1400:g=2.8,acompressor=threshold=-16dB:ratio=2.5:attack=5:release=55"

    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)
    dur = get_duration(v_file) + 0.08
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    cap_raw = str(b.get("cap", "")).strip()
    cap_text = cap_raw if cap_raw else str(b.get("sub", ""))
    wtimes = caption_word_times(word_spans, cap_text, bool(cap_raw)) if word_spans else None

    vis = str(b.get("visual") or b.get("card") or "none").lower()
    timeline.append({
        "index": idx,
        "start": round(current_time, 3),
        "duration": round(dur, 3),
        "hero": str(b.get("hero", "STEP")).upper()[:14],
        "hero_color": str(b.get("hero_color", "maroon")).lower(),
        "strike": bool(b.get("strike", False)),
        "sub": str(b.get("sub", ""))[:44],
        "cap": cap_raw[:120],
        "word_times": wtimes,
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
import glob as _glob
for _kind in ("whoosh", "pop"):
    _fl = sorted(_glob.glob(f"sfx/{_kind}*.wav") + _glob.glob(f"sfx/{_kind}*.mp3"))
    if _fl:
        _pick = rng.choice(_fl)
        print(f"SFX {_kind}: real file -> {_pick}")
        subprocess.run(["ffmpeg", "-y", "-i", _pick, "-af", "atrim=0:1.2,afade=t=out:st=0.9:d=0.3,volume=0.8", f"sfx_{_kind}.wav"], check=True)

with open("vlist.txt", "w") as f:
    for vf in voice_files:
        f.write(f"file '{vf}'\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "vlist.txt", "full_voice.wav"], check=True)

import glob
music_files = sorted(glob.glob("music/*.mp3") + glob.glob("music/*.wav") + glob.glob("music/*.m4a"))
music_file = rng.choice(music_files) if music_files else None
if music_file:
    print(f"BGM: real track -> {music_file}")
    sfx_inputs.extend(["-stream_loop", "-1", "-i", music_file])
    bgm_vol = 0.30
else:
    print("BGM: synth fallback (add royalty-free tracks to /music for a pro sound)")
    sfx_inputs.extend(["-i", "bgm.wav"])
    bgm_vol = 0.55

bgm_idx = sfx_counter + 1
sfx_labels = "".join([f"[s{i}]" for i in range(1, sfx_counter + 1)])
filter_str = ";".join(filter_complex) + (
    f";[0:a]asplit=2[vo][vsc]"
    f";[{bgm_idx}:a]volume={bgm_vol},atrim=0:{round(current_time + 1, 2)}[bg0]"
    f";[bg0][vsc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=450:makeup=1[bgd]"
    f";[vo]{sfx_labels}[bgd]amix=inputs={sfx_counter + 2}:duration=first:normalize=0,"
    f"loudnorm=I=-14:TP=-1.5:LRA=11[out]"
)

subprocess.run([
    "ffmpeg", "-y", "-i", "full_voice.wav", *sfx_inputs,
    "-filter_complex", filter_str, "-map", "[out]", "-c:a", "aac", "-b:a", "192k", "final_audio.m4a"
], check=True)

with open("timeline.json", "w") as f:
    json.dump({
        "total_duration": round(current_time, 3),
        "thumb_hero": str(script_data.get("thumb_hero", "STUDY PLAN")).upper()[:13],
        "thumb_sub": str(script_data.get("thumb_sub", "3-Step Smart Formula"))[:34],
        "thumb_badge": str(script_data.get("thumb_badge", "3 STEPS"))[:13],
        "day": SERIES_DAY,
        "series": SERIES_NAME,
        "next_teaser": str(script_data.get("next_teaser", ""))[:60],
        "beats": timeline
    }, f, indent=2)

print(f"V25 voice + real word-sync + ducked BGM ready! ({round(current_time, 2)}s)")
