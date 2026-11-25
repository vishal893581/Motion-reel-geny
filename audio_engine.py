import sys
import subprocess
import json
import os
import time
import re
import random
import requests

raw_topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "wise_human"
theme_mode = sys.argv[3].strip() if len(sys.argv) > 3 else "kinetic_cream"

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


# High-retention 45-60s practical educational teaching packs (matching video_1 & video_2 exact structure)
EDUCATIONAL_PACKS = [
    {
        "topic_title": "Kal Exam Hai Aur Syllabus Bacha Hai: Topper 3-Hour Crash Plan",
        "thumb_hero": "EXAM",
        "thumb_sub": "3-Hour Topper Crash Plan",
        "thumb_badge": "23:28:13",
        "ig_caption": "Kal exam hai aur syllabus bacha hai? Yeh 3-Hour Crash Plan follow karo!\n\nSave karo aaj raat ke liye aur apne dost ko share karo.\nComment mein batao kal kis subject ka exam hai!\n\n#exam #studytips #students #boardexam #sochbadlo",
        "beats": [
            {"tts": "कल एग्जाम है... और सिलेबस अभी भी बचा है?", "hero": "EXAM", "hero_color": "maroon", "sub": "kal exam hai aur syllabus bacha hai?", "pill": "syllabus", "bg": "cream", "card": "timer", "card_title": "EXAM KAL", "card_val": "23:28:13", "card_sub": "time kam hai"},
            {"tts": "टेंशन मत ले... टॉपर भी यही करता है!", "hero": "TENSION", "hero_color": "maroon", "strike": True, "sub": "mat le, topper bhi yahi karta hai!", "pill": "topper", "bg": "cream", "card": "none"},
            {"tts": "तीन घंटे का क्रैश प्लान याद रखो।", "hero": "3-HOUR", "hero_color": "orange", "sub": "crash plan yaad rakho.", "pill": "crash", "bg": "cream", "card": "badge", "card_title": "CRASH PLAN", "card_val": "3 HOURS", "card_sub": "step by step"},
            {"tts": "पहला घंटा... पी वाई क्यू निकालो। पिछले दो साल के पेपर में जो सवाल दो बार आया है, वही पहले पढ़ो!", "hero": "2 BAAR", "hero_color": "orange", "sub": "aaya question pehle padho!", "pill": "PYQ", "bg": "cream", "card": "compare", "card_title": "HOUR 1", "card_val": "PAPER 1 vs 2", "card_sub": "2x repeated"},
            {"tts": "प्रोफेसर भी वही रिपीट करता है।", "hero": "REPEAT", "hero_color": "maroon", "sub": "professor bhi wahi poochta hai!", "pill": "professor", "bg": "cream", "card": "checklist", "card_title": "MUST DO", "card_val": "2024 Paper|2025 Paper|Repeated Qs", "card_sub": "high weightage"},
            {"tts": "दूसरा घंटा... इम्पॉर्टेंट टॉपिक्स के आंसर रिवाइज़ करो। हर आंसर को डेफिनिशन, की-पॉइंट्स और डायग्राम में बांटो।", "hero": "REVISE", "hero_color": "orange", "sub": "important topics ke answers karo.", "pill": "HOUR 2", "bg": "cream", "card": "checklist", "card_title": "HOUR 2", "card_val": "Definition|Key Points|Diagram", "card_sub": "smart notes"},
            {"tts": "सिर्फ रीड मत करो... बुक बंद करके खुद रिकॉल भी करो।", "hero": "RECALL", "hero_color": "maroon", "sub": "book band karke khud yaad karo!", "pill": "band", "bg": "cream", "card": "none"},
            {"tts": "पूरी बुक मत खोलो! बुक खोली तो रात खत्म।", "hero": "MAT KHOLO", "hero_color": "cream", "sub": "poori book kholi toh raat khatam!", "pill": "POORI BOOK", "bg": "maroon", "card": "cross", "card_title": "WARNING", "card_val": "POORI BOOK", "card_sub": "time waste"},
            {"tts": "तीसरा घंटा... एक पेज पर सारे फॉर्मूलाज़, डेफिनिशन और डायग्राम बना लो।", "hero": "EK PAGE", "hero_color": "maroon", "sub": "pe saare formulas aur diagrams bana lo.", "pill": "HOUR 3", "bg": "cream", "card": "sheet", "card_title": "CHEAT SHEET", "card_val": "F = m x a|v = u + at", "card_sub": "1 page summary"},
            {"tts": "यही पेज कल सुबह एग्जाम से पहले पढ़ना है।", "hero": "KAL SUBAH", "hero_color": "orange", "sub": "pehle exam se yahi padhna hai.", "pill": "exam", "bg": "cream", "card": "clock", "card_title": "MORNING", "card_val": "07:30 AM", "card_sub": "quick revision"},
            {"tts": "और हाँ... रात को दो बजे तक रील्स देख के कल सुबह पढूँगा मत बोलना! कल सुबह कुछ नहीं होता।", "hero": "2 BAJE", "hero_color": "maroon", "sub": "raat ko reels dekhna band karo!", "pill": "raat", "bg": "cream", "card": "phone", "card_title": "2:00 AM", "card_val": "REELS TRAP", "card_sub": "0% padhai"},
            {"tts": "इस प्लान को सेव करो... आज रात को ही चाहिए होगा!", "hero": "SAVE", "hero_color": "orange", "sub": "karo aaj raat ke liye!", "pill": "raat", "bg": "cream", "card": "save", "card_title": "3-HOUR PLAN", "card_val": "SAVED", "card_sub": "@sochbadlo.hq"},
            {"tts": "शेयर करो उस दोस्त को जो अभी भी बोल रहा है कल सुबह पढूँगा।", "hero": "SHARE", "hero_color": "maroon", "sub": "karo us dost ko abhi!", "pill": "dost", "bg": "cream", "card": "share", "card_title": "SEND TO", "card_val": "Best Friend", "card_sub": "kal subah padhunga"},
            {"tts": "और कमेंट में बताओ... तुम्हारा कल किस सब्जेक्ट का एग्जाम है?", "hero": "COMMENT", "hero_color": "orange", "sub": "me batao kal kaunsa subject hai?", "pill": "batao", "bg": "cream", "card": "comment", "card_title": "COMMENT", "card_val": "Kal mera exam...", "card_sub": "reply below"}
        ]
    },
    {
        "topic_title": "Age 18 Se 26: 3 High-Income Skills Jo 3 Mahine Mein Seekh Sakte Ho",
        "thumb_hero": "AGE 18-26",
        "thumb_sub": "3 High-Income Skills (2026)",
        "thumb_badge": "90 DAYS PLAN",
        "ig_caption": "Agar tumhari age 18 se 26 ke beech hai, toh 2026 khatam hone se pehle in 3 mein se 1 skill zaroor seekh lo!\n\nSave karo aur comment mein apni age likho.\n\n#skills #career #earning #youthindia #sochbadlo",
        "beats": [
            {"tts": "अगर तुम्हारी एज अठारह से छब्बीस साल के बीच में है... तो दो हज़ार छब्बीस खत्म होने से पहले ये तीन स्किल्स सीख लो!", "hero": "AGE 18-26", "hero_color": "maroon", "sub": "2026 khatam hone se pehle seekho!", "pill": "2026", "bg": "cream", "card": "badge", "card_title": "CAREER ALERT", "card_val": "3 SKILLS", "card_sub": "in 90 days"},
            {"tts": "जिन्हें तुम सिर्फ तीन महीने में ईज़िली सीख जाओगे... वरना तुम इस साल को भी बर्बाद कर दोगे।", "hero": "3 MAHINE", "hero_color": "orange", "sub": "mein seekh jaoge, warna saal barbaad!", "pill": "barbaad", "bg": "cream", "card": "timer", "card_title": "TIME LEFT", "card_val": "90 DAYS", "card_sub": "start today"},
            {"tts": "स्किल नंबर वन... मेटा ऐड्स। आज जितनी भी कंपनीज़ हैं वो अपने प्रोडक्ट बेचने के लिए मेटा ऐड्स चलाती हैं।", "hero": "META ADS", "hero_color": "cream", "sub": "companies lakho pay karne ko ready hain!", "pill": "SKILL 01", "bg": "maroon", "card": "badge", "card_title": "SKILL NO. 1", "card_val": "META ADS", "card_sub": "high demand"},
            {"tts": "और एक अच्छा ऐड्स मैनेजर घर बैठे पचास हज़ार से एक लाख महीना चार्ज करता है।", "hero": "₹50K - ₹1L", "hero_color": "orange", "sub": "mahina ghar baithe kama sakte ho.", "pill": "earning", "bg": "cream", "card": "compare", "card_title": "INCOME", "card_val": "JOB vs SKILL", "card_sub": "3x faster growth"},
            {"tts": "स्किल नंबर टू... सेल्स ऑटोमेशन और एआई बॉट्स। इस स्किल को सीखने के बाद तुम किसी भी बिज़नेस के लिए लीड्स ला सकते हो।", "hero": "AI AUTOMATION", "hero_color": "cream", "sub": "har business ko aaj iski zaroorat hai!", "pill": "SKILL 02", "bg": "maroon", "card": "checklist", "card_title": "SKILL NO. 2", "card_val": "WhatsApp Bot|Lead Funnel|CRM Auto", "card_sub": "zero coding"},
            {"tts": "अगर ये स्किल तुमने एक बार सीख ली... तो ज़िंदगी भर अपॉर्चुनिटीज़ की कमी नहीं होगी।", "hero": "NO LIMITS", "hero_color": "maroon", "sub": "zindagi bhar kaam ki kami nahi hogi.", "pill": "opportunities", "bg": "cream", "card": "none"},
            {"tts": "स्किल नंबर थ्री... वेबसाइट और लैंडिंग पेज डेवलपमेंट। इंडिया के अंदर सत्तर से अस्सी परसेंट बिज़नेस ओनर्स की वेबसाइट नहीं है।", "hero": "70% - 80%", "hero_color": "orange", "sub": "Indian businesses ke paas website nahi hai!", "pill": "SKILL 03", "bg": "cream", "card": "sheet", "card_title": "MARKET GAP", "card_val": "75% No Site|High Clients", "card_sub": "huge opportunity"},
            {"tts": "सिर्फ नो-कोड टूल्स सीख कर तुम एक वेबसाइट के पंद्रह से तीस हज़ार रुपये चार्ज कर सकते हो।", "hero": "₹25,000", "hero_color": "maroon", "sub": "ek website ka aasani se charge karo.", "pill": "no-code", "bg": "cream", "card": "checklist", "card_title": "ROADMAP", "card_val": "Month 1: Basics|Month 2: Portfolio|Month 3: Clients", "card_sub": "90-day plan"},
            {"tts": "सिर्फ डिग्री के भरोसे मत बैठो... आज मार्केट डिग्री नहीं, तुम्हारी स्किल देखता है।", "hero": "DEGREE", "hero_color": "maroon", "strike": True, "sub": "nahi, market aaj sirf skill dekhta hai!", "pill": "skill", "bg": "cream", "card": "cross", "card_title": "OLD RULE", "card_val": "SIRF DEGREE", "card_sub": "not enough"},
            {"tts": "इस रील को सेव कर लो... ताकि कल से ही पहली स्किल शुरू कर सको!", "hero": "SAVE", "hero_color": "orange", "sub": "karo aur kal se hi start karo!", "pill": "start", "bg": "cream", "card": "save", "card_title": "3 SKILLS 2026", "card_val": "SAVED", "card_sub": "@sochbadlo.hq"},
            {"tts": "शेयर करो अपने उस दोस्त को जो अभी भी नौकरी के लिए भटक रहा है।", "hero": "SHARE", "hero_color": "maroon", "sub": "karo apne dost ko abhi!", "pill": "dost", "bg": "cream", "card": "share", "card_title": "SEND TO", "card_val": "College Friend", "card_sub": "help him grow"},
            {"tts": "कमेंट में अपनी एज और कौनसी स्किल सीखोगे... ज़रूर लिखना!", "hero": "COMMENT", "hero_color": "orange", "sub": "me likho kaunsi skill seekhoge?", "pill": "likho", "bg": "cream", "card": "comment", "card_title": "COMMENT", "card_val": "Skill #1 start...", "card_sub": "reply below"}
        ]
    },
    {
        "topic_title": "Salary Aate Hi 10 Tareekh Ko Khatam: 50-30-20 Smart Money Rule",
        "thumb_hero": "SALARY",
        "thumb_sub": "50-30-20 Smart Money Rule",
        "thumb_badge": "MONEY RULE",
        "ig_caption": "Salary aate hi 10 tareekh ko khatam ho jaati hai? Yeh 50-30-20 Money Rule aaj se lagao!\n\nSave karo aur apne dost ko bhejo.\n\n#personalfinance #salary #savingtips #moneyrules #sochbadlo",
        "beats": [
            {"tts": "सैलरी एक तारीख को आती है... और दस तारीख तक अकाउंट फिर से खाली हो जाता है?", "hero": "SALARY", "hero_color": "maroon", "sub": "10 tareekh ko hi khatam ho jaati hai?", "pill": "khaali", "bg": "cream", "card": "timer", "card_title": "BANK BALANCE", "card_val": "₹420.00", "card_sub": "10th of month"},
            {"tts": "क्योंकि तुम खर्च करने के बाद बचाते हो... जबकि अमीर लोग बचाने के बाद खर्च करते हैं!", "hero": "ULTE RULE", "hero_color": "orange", "sub": "se chaloge toh kabhi nahi bachega!", "pill": "rule", "bg": "cream", "card": "compare", "card_title": "MINDSET", "card_val": "AAM vs SMART", "card_sub": "save first"},
            {"tts": "आज से पचास-तीस-बीस का ये सिंपल रूल अपनी सैलरी पर लगाओ।", "hero": "50-30-20", "hero_color": "cream", "sub": "ka simple formula aaj se lagao!", "pill": "FORMULA", "bg": "maroon", "card": "badge", "card_title": "MONEY RULE", "card_val": "50 : 30 : 20", "card_sub": "100% control"},
            {"tts": "पहला हिस्सा पचास परसेंट... सिर्फ ज़रूरी खर्चों के लिए। रेंट, राशन, बिजली और घर की ईएमआई।", "hero": "50% NEEDS", "hero_color": "maroon", "sub": "sirf zaroori kharchon ke liye rakho.", "pill": "PART 01", "bg": "cream", "card": "checklist", "card_title": "50% NEEDS", "card_val": "Rent & Bills|Ration & Food|Basic EMI", "card_sub": "fixed limit"},
            {"tts": "दूसरा हिस्सा तीस परसेंट... तुम्हारे शौक और लाइफस्टाइल के लिए। बाहर खाना, शॉपिंग और घूमना।", "hero": "30% WANTS", "hero_color": "orange", "sub": "shauk aur lifestyle ke liye rakho.", "pill": "PART 02", "bg": "cream", "card": "checklist", "card_title": "30% WANTS", "card_val": "Dining Out|Shopping|Weekend Trip", "card_sub": "guilt free"},
            {"tts": "तीसरा हिस्सा बीस परसेंट... सैलरी आते ही सबसे पहले अलग अकाउंट में इन्वेस्ट कर दो!", "hero": "20% INVEST", "hero_color": "maroon", "sub": "salary aate hi pehle alag karo!", "pill": "PART 03", "bg": "cream", "card": "sheet", "card_title": "AUTO SAVE", "card_val": "1st Date SIP|Emergency Fund", "card_sub": "pay yourself first"},
            {"tts": "बिना सोचे ईएमआई पर नया फोन लेना बंद करो... वरना पूरी जवानी किश्तों में निकल जाएगी!", "hero": "EMI TRAP", "hero_color": "cream", "sub": "mein mat phanso, dikhawa band karo!", "pill": "WARNING", "bg": "maroon", "card": "cross", "card_title": "AVOID THIS", "card_val": "0% EMI PHONE", "card_sub": "wealth killer"},
            {"tts": "अगर तुम हर महीने सिर्फ पाँच हज़ार भी बचाते हो... तो दस साल में वो बारह लाख से ऊपर बन जाता है।", "hero": "₹12 LAKH+", "hero_color": "orange", "sub": "sirf ₹5,000 mahina bachane se banta hai!", "pill": "compounding", "bg": "cream", "card": "clock", "card_title": "10 YEARS", "card_val": "₹12,40,000", "card_sub": "power of habit"},
            {"tts": "इस रूल को अभी सेव करो... अगली सैलरी पर यही फॉलो करना है!", "hero": "SAVE", "hero_color": "orange", "sub": "karo agli salary ke liye!", "pill": "salary", "bg": "cream", "card": "save", "card_title": "50-30-20 RULE", "card_val": "SAVED", "card_sub": "@sochbadlo.hq"},
            {"tts": "शेयर करो अपने उस दोस्त को जिसकी सैलरी भी दस तारीख को गायब हो जाती है!", "hero": "SHARE", "hero_color": "maroon", "sub": "karo apne kharchile dost ko!", "pill": "dost", "bg": "cream", "card": "share", "card_title": "SEND TO", "card_val": "Salary Friend", "card_sub": "tag him now"},
            {"tts": "कमेंट में बताओ... तुम्हारी सैलरी किस तारीख तक चलती है?", "hero": "COMMENT", "hero_color": "orange", "sub": "me batao kitne din chalti hai salary?", "pill": "batao", "bg": "cream", "card": "comment", "card_title": "COMMENT", "card_val": "Meri salary toh...", "card_sub": "reply below"}
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
    "Communication, Confidence & Daily Productivity Frameworks (3-Step Practical Rules)",
    "Consumer Rights, Banking Rules & Everyday Smart Life Hacks Every Indian Must Know"
]
chosen_category = rng.choice(TEACHING_CATEGORIES)
print(f"V21 Kinetic Explainer Engine | Category: {chosen_category} | Past Topics: {len(used_history)}")


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
        f'Create an educational, step-by-step Hinglish Reel specifically on: "{explicit_topic}"'
        if explicit_topic
        else f'Invent ONE brand-new, ultra-practical, high-save Indian educational/teaching Reel topic in "{category_hint}" that teaches viewers a concrete 3-step method, crash plan, skill roadmap, or smart rule! Never repeat any topic in the list above.'
    )

    return f"""You are a viral Indian educational motion-graphics Reel creator (like @sochbadlo.hq / Vox / crisp kinetic explainer Reels).
{topic_instruction}
{avoid_block}

Write a fast-paced, high-retention 11 to 13 beat Hinglish educational script (42 to 55 seconds total -> 8 to 13 spoken words per beat) that genuinely TEACHES something actionable step-by-step and ends with a strong SAVE + SHARE + COMMENT call-to-action!

For EACH beat in "beats" array, return:
- "tts": Natural Devanagari Hindi with English terms written phonetically in Devanagari (e.g., 'एग्जाम', 'सिलेबस', 'स्किल', 'सैलरी') and natural pauses (`...`) so the voiceover sounds like an energetic, wise Indian mentor teaching clearly.
- "hero": 1 to 2 BIG UPPERCASE PUNCH WORDS in Hinglish/English (MAX 13 chars, e.g. "EXAM", "3-HOUR", "2 BAAR", "REVISE", "MAT KHOLO", "EK PAGE", "SAVE", "SHARE", "COMMENT") that appear in giant 3D extruded typography!
- "hero_color": "maroon" or "orange" (when bg is "cream"), or "cream" (when bg is "maroon").
- "strike": boolean (true ONLY when crossing out a bad habit like "TENSION" or "DEGREE", otherwise false).
- "sub": Short clean Roman Hinglish continuation phrase (MAX 36 chars, e.g. "kal exam hai aur syllabus bacha hai?").
- "pill": Single keyword from "sub" (MAX 14 chars) to highlight inside a maroon rounded pill badge.
- "bg": "cream" (warm textured paper, use for ~80% of beats) or "maroon" (deep crimson warning/step header, use for 2-3 dramatic beats).
- "card": Visual vector diagram on screen — choose from ["timer", "badge", "compare", "checklist", "sheet", "clock", "phone", "cross", "save", "share", "comment", "none"].
- "card_title": Short uppercase card header (MAX 14 chars, e.g. "HOUR 1", "SKILL NO. 1", "CHEAT SHEET").
- "card_val": Main card value (MAX 28 chars; for "checklist" use pipe-separated items like "Step 1|Step 2|Step 3"; for "compare" use "A vs B").
- "card_sub": Tiny bottom note on card (MAX 18 chars).

Return ONLY valid JSON:
{{
  "topic_title": "Short unique Roman Hinglish title (6-10 words)",
  "thumb_hero": "1-2 word big cover title (MAX 12 chars)",
  "thumb_sub": "4-5 word cover subtitle (MAX 32 chars)",
  "thumb_badge": "Short cover badge value (MAX 12 chars)",
  "ig_caption": "Engaging 3-line Hinglish caption with Save/Share/Comment prompt + 5 hashtags",
  "beats": [ ... 11 to 13 beat objects ... ]
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
                    print(f"SUCCESS! Gemini generated {len(data['beats'])}-beat kinetic teaching script via {model_name}!")
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
    print(f"Using built-in educational crash-plan pack: {title}")
    return chosen_pack


script_data = generate_script()
beats = script_data["beats"]


def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())


def generate_sfx_bank():
    # Crisp motion-graphics whoosh, UI pop, and subtle tick SFX (exact video_2 feel)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.16:c=pink:a=0.30", "-af", "bandpass=f=950:width_type=h:w=700,afade=t=in:ss=0:d=0.03,afade=t=out:st=0.05:d=0.11", "sfx_whoosh.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=680:d=0.07", "-af", "afade=t=out:st=0.01:d=0.06,volume=0.38", "sfx_pop.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1150:d=0.045", "-af", "afade=t=out:st=0.01:d=0.035,volume=0.25", "sfx_tick.wav"], check=True)


def generate_elevenlabs_tts(text, out_file):
    el_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not el_key:
        return False
    voice_id = "nPczCjzI2devNBz1zQrb"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": el_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.44, "similarity_boost": 0.82, "style": 0.48, "use_speaker_boost": True}
    }
    for _ in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(out_file, "wb") as f:
                    f.write(r.content)
                return True
            if r.status_code in (401, 402, 429):
                break
        except Exception:
            pass
        time.sleep(1.2)
    return False


def run_edge_tts_fallback(text, out_file):
    for _ in range(5):
        res = subprocess.run([
            "edge-tts", "--voice", "hi-IN-MadhurNeural",
            "--rate", "+11%", "--pitch", "-2Hz",
            "--text", text, "--write-media", out_file
        ])
        if res.returncode == 0 and os.path.exists(out_file) and os.path.getsize(out_file) > 500:
            return
        time.sleep(1.5)
    raise RuntimeError(f"Failed TTS for {out_file}")


generate_sfx_bank()

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
        af_str = "atempo=1.06,highpass=f=85,equalizer=f=165:width_type=h:width=110:g=2.5,equalizer=f=3200:width_type=h:width=1400:g=2.4,acompressor=threshold=-16dB:ratio=2.4:attack=6:release=60"
    else:
        run_edge_tts_fallback(tts_text, raw_v)
        af_str = "highpass=f=85,equalizer=f=175:width_type=h:width=110:g=2.8,acompressor=threshold=-16dB:ratio=2.5:attack=6:release=60"

    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)
    dur = get_duration(v_file) + 0.14
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "index": idx,
        "start": round(current_time, 3),
        "duration": round(dur, 3),
        "hero": str(b.get("hero", "STEP")).upper()[:14],
        "hero_color": str(b.get("hero_color", "maroon")).lower(),
        "strike": bool(b.get("strike", False)),
        "sub": str(b.get("sub", ""))[:42],
        "pill": str(b.get("pill", ""))[:16],
        "bg": str(b.get("bg", "cream")).lower(),
        "card": str(b.get("card", "none")).lower(),
        "card_title": str(b.get("card_title", ""))[:16],
        "card_val": str(b.get("card_val", ""))[:36],
        "card_sub": str(b.get("card_sub", ""))[:20]
    })

    # Whoosh on beat start + pop when vector card appears
    ms1 = int((current_time + 0.02) * 1000)
    sfx_inputs.extend(["-i", "sfx_whoosh.wav"])
    sfx_counter += 1
    filter_complex.append(f"[{sfx_counter}:a]adelay={ms1}|{ms1}[s{sfx_counter}]")

    if b.get("card", "none") != "none":
        ms2 = int((current_time + min(0.28, dur * 0.35)) * 1000)
        sfx_inputs.extend(["-i", "sfx_pop.wav"])
        sfx_counter += 1
        filter_complex.append(f"[{sfx_counter}:a]adelay={ms2}|{ms2}[s{sfx_counter}]")

    current_time += dur

with open("vlist.txt", "w") as f:
    for vf in voice_files:
        f.write(f"file '{vf}'\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "vlist.txt", "full_voice.wav"], check=True)

# Subtle clean background pulse
subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi",
    "-i", f"aevalsrc=0.018*sin(2*PI*65*t)+0.010*sin(2*PI*130*t):d={current_time+1}",
    "-af", "lowpass=f=240,afade=t=in:ss=0:d=0.5,afade=t=out:st=" + str(max(0.5, current_time - 0.5)) + ":d=0.5",
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
        "thumb_hero": str(script_data.get("thumb_hero", "STUDY PLAN")).upper()[:13],
        "thumb_sub": str(script_data.get("thumb_sub", "3-Step Smart Formula"))[:34],
        "thumb_badge": str(script_data.get("thumb_badge", "3 STEPS"))[:13],
        "beats": timeline
    }, f, indent=2)

print(f"V21 Kinetic Explainer Engine Ready! ({round(current_time, 2)}s, {len(timeline)} beats)")
