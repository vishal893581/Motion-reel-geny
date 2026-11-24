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
theme_mode = sys.argv[3].strip() if len(sys.argv) > 3 else "random"

rng = random.SystemRandom()
HISTORY_FILE = "used_topics.txt"

ALLOWED_WIDGETS = [
    "rupee_counter_shock",
    "phone_upi_alert",
    "scam_warning_stamp",
    "vs_clash_cards",
    "stock_line_graph",
    "animated_bar_chart",
    "floating_checklist",
    "circular_gauge",
    "typing_terminal_hud",
    "split_duel_banner",
    "step_pyramid_stack",
    "spotlight_stat_pill"
]


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


# High-converting Desi Money & Habit Fallback Packs (if Gemini API hits rate limit)
TOPIC_PACKS = [
    {
        "caption_topic": "Roz Ki ₹20 Wali Chai Aapke ₹2.5 Lakh Kaise Kha Jaati Hai",
        "thumbnail_hook": "₹20 KI CHAI = ₹2.5 LAKH LOSS?!",
        "thumbnail_badge": "MIDDLE CLASS TRAP",
        "scenes": [
            {"tts_voice": "रोज़ की सिर्फ बीस रुपये वाली चाय आपके ढाई लाख रुपये कैसे खा जाती है?", "caption": "Roz ki sirf ₹20 wali chai aapke ₹2.5 lakh kaise kha jaati hai?", "widget": "rupee_counter_shock", "kicker": "POCKET LEAK", "headline": "₹20 Chai Ka Asli Hisab", "metric_big": "₹2.5L", "metric_label": "10 SAAL KA LOSS", "left_label": "Roz ₹20 Kharch", "right_label": "₹2.5 Lakh Gayab", "pct": 94},
            {"tts_voice": "दिन में दो बार चाय और स्नैक्स मतलब महीने के बारह सौ रुपये सीधे गायब।", "caption": "Din mein 2 baar chai aur snacks matlab mahine ke ₹1,200 seedhe gayab.", "widget": "phone_upi_alert", "kicker": "UPI DEBIT ALERT", "headline": "Mahine Ka Chhupa Bill", "metric_big": "₹1,200", "metric_label": "MONTHLY UPI LEAK", "left_label": "Chhota Payment", "right_label": "Bada Nuksan", "pct": 88},
            {"tts_voice": "साल के चौदह हज़ार चार सौ रुपये बिना किसी हिसाब के उड़ जाते हैं।", "caption": "Saal ke ₹14,400 bina kisi hisab ke hawa mein ud jaate hain.", "widget": "stock_line_graph", "kicker": "SILENT DRAIN", "headline": "Saal Bhar Ka Nuksan", "metric_big": "₹14,400", "metric_label": "YEARLY WASTE", "left_label": "Zero Savings", "right_label": "100% Kharcha", "pct": 91},
            {"tts_voice": "अगर यही बारह सौ रुपये बारह परसेंट एसआईपी में जाएं तो दस साल में दो लाख अस्सी हज़ार बनते हैं!", "caption": "Agar yahi ₹1,200 12% SIP mein jaayein toh 10 saal mein ₹2.80 Lakh bante hain!", "widget": "vs_clash_cards", "kicker": "WEALTH SHIFT", "headline": "Chai Vs Smart SIP", "metric_big": "₹2.80L", "metric_label": "10-YEAR WEALTH", "left_label": "Roz ₹40 Kharch", "right_label": "₹1,200 Monthly SIP", "pct": 96},
            {"tts_voice": "अमीर लोग छोटे खर्चों को ट्रैक करते हैं और गरीब इन्हें सिर्फ चिल्लर समझते हैं।", "caption": "Ameer log chhote kharchon ko track karte hain, gareeb inhe chillar samajhte hain.", "widget": "scam_warning_stamp", "kicker": "MINDSET TRAP", "headline": "Chillar Soch Band Karo", "metric_big": "TRAP", "metric_label": "ZERO TRACKING", "left_label": "Andha Kharcha", "right_label": "Smart Tracking", "pct": 93},
            {"tts_voice": "अपने उस दोस्त को टैग करो जो रोज़ चाय पिलाता है और रील सेव करो!", "caption": "Apne us dost ko share karo jo roz chai peeta hai aur reel save karo!", "widget": "floating_checklist", "kicker": "ACTION RULE", "headline": "Aaj Se Hisab Shuru", "metric_big": "SAVE", "metric_label": "MONEY RULE", "left_label": "Kharcha Likho", "right_label": "Auto SIP Lagao", "pct": 98}
        ]
    },
    {
        "caption_topic": "Zero Cost EMI Ka Asli Jaal Jo Middle Class Ko Gareeb Rakhta Hai",
        "thumbnail_hook": "ZERO COST EMI KA ASLI SCAM!",
        "thumbnail_badge": "BANKING TRAP",
        "scenes": [
            {"tts_voice": "ज़िरो कॉस्ट ईएमआई के नाम पर कंपनियां आपकी जेब से एक्स्ट्रा पैसे कैसे निकालती हैं?", "caption": "Zero Cost EMI ke naam par companies aapki jeb se extra paise kaise nikaalti hain?", "widget": "scam_warning_stamp", "kicker": "EMI SCAM", "headline": "Zero Cost EMI Ka Sach", "metric_big": "SCAM", "metric_label": "HIDDEN CHARGES", "left_label": "0% Dikhaawa", "right_label": "16% Asli Byaj", "pct": 95},
            {"tts_voice": "पहला झटका: ईएमआई चुनते ही कैश डिस्काउंट खत्म हो जाता है जो सीधे आपका ब्याज है।", "caption": "Pehla jhatka: EMI chunte hi cash discount khatam, jo seedha aapka interest hai.", "widget": "vs_clash_cards", "kicker": "TRICK 01", "headline": "Discount Gayab Khel", "metric_big": "₹4,500", "metric_label": "LOST DISCOUNT", "left_label": "EMI Price Full", "right_label": "Cash ₹4,500 Sasta", "pct": 90},
            {"tts_voice": "दूसरा झटका: प्रोसेसिंग फीस और उस पर अठारह परसेंट जीएसटी अलग से कटता है।", "caption": "Doosra jhatka: processing fee aur us par 18% GST alag se kat-ta hai.", "widget": "phone_upi_alert", "kicker": "BANK FEE ALERT", "headline": "Processing Fee + 18% GST", "metric_big": "+18%", "metric_label": "EXTRA GST TAX", "left_label": "Free EMI Claim", "right_label": "Hidden Bank Fee", "pct": 89},
            {"tts_voice": "तीसरा झटका: एक किश्त लेट होते ही बैंक भारी पेनल्टी और सिबिल स्कोर खराब करता है।", "caption": "Teesra jhatka: ek kist late hote hi bank bhaari penalty aur CIBIL kharab karta hai.", "widget": "rupee_counter_shock", "kicker": "PENALTY TRAP", "headline": "Late Fee + CIBIL Crash", "metric_big": "₹1,180", "metric_label": "PER LATE BOUNCE", "left_label": "Safe CIBIL 780", "right_label": "Bounce Penalty", "pct": 94},
            {"tts_voice": "असली नियम: जो चीज़ कैश में नहीं खरीद सकते, उसे ईएमआई पर कभी मत लो।", "caption": "Asli niyam: jo cheez cash mein nahi khareed sakte, use EMI par kabhi mat lo.", "widget": "split_duel_banner", "kicker": "GOLDEN RULE", "headline": "Cash Rule Apnao", "metric_big": "100%", "metric_label": "DEBT FREE LIFE", "left_label": "Show-Off EMI", "right_label": "100% Cash Buy", "pct": 97},
            {"tts_voice": "ईएमआई पर फोन लेने वाले दोस्त को ये रील अभी शेयर करो!", "caption": "EMI par phone lene wale dost ko yeh reel abhi share karo!", "widget": "floating_checklist", "kicker": "SHARE NOW", "headline": "EMI Jaal Se Bacho", "metric_big": "SAVE", "metric_label": "SMART BUYER", "left_label": "No Impulse EMI", "right_label": "Save First Buy", "pct": 99}
        ]
    },
    {
        "caption_topic": "Subah Uthne Ke Pehle 15 Minute Aapka Poora Din Barbaad Kaise Karte Hain",
        "thumbnail_hook": "SUBAH KE 15 MIN = DIN BARBAAD!",
        "thumbnail_badge": "BRAIN TRAP",
        "scenes": [
            {"tts_voice": "सुबह उठते ही पहले पंद्रह मिनट में की गई ये एक गलती आपका पूरा दिन बर्बाद कर देती है!", "caption": "Subah uthte hi pehle 15 minute mein ki gayi yeh galti poora din barbaad karti hai!", "widget": "scam_warning_stamp", "kicker": "MORNING TRAP", "headline": "Subah Ki Sabse Badi Galti", "metric_big": "15 MIN", "metric_label": "FOCUS DESTROYED", "left_label": "Fresh Dimag", "right_label": "Instant Stress", "pct": 95},
            {"tts_voice": "आंख खुलते ही रील्स और नोटिफिकेशन देखने से दिमाग में फेक डोपामिन का धमाका होता है।", "caption": "Aankh khulte hi reels aur notification dekhne se dimag mein fake dopamine phat-ta hai.", "widget": "phone_upi_alert", "kicker": "DOPAMINE SPIKE", "headline": "Bed Par Phone Check", "metric_big": "400%", "metric_label": "DOPAMINE CRASH", "left_label": "Calm Morning", "right_label": "27 Notifications", "pct": 92},
            {"tts_voice": "इसके बाद पढ़ाई या काम जैसा ज़रूरी काम दिमाग को बेहद बोरिंग लगने लगता है।", "caption": "Iske baad padhai ya kaam jaisa zaroori kaam dimag ko behad boring lagne lagta hai.", "widget": "stock_line_graph", "kicker": "ENERGY DROP", "headline": "Kaam Mein Mann Nahi", "metric_big": "-65%", "metric_label": "FOCUS DROP", "left_label": "High Willpower", "right_label": "Brain Fog", "pct": 89},
            {"tts_voice": "सिर्फ सात दिन तक उठने के तीस मिनट बाद तक फोन को हाथ मत लगाओ।", "caption": "Sirf 7 din tak uthne ke 30 minute baad tak phone ko haath mat lagao.", "widget": "vs_clash_cards", "kicker": "7-DAY CHALLENGE", "headline": "30-Min No Phone Rule", "metric_big": "3X", "metric_label": "SHARP FOCUS", "left_label": "Bed Scrolling", "right_label": "30 Min Detox", "pct": 96},
            {"tts_voice": "पहले दिन से ही आपका दिमाग शांत रहेगा और काम दोगुनी स्पीड से खत्म होगा।", "caption": "Pehle din se hi aapka dimag shaant rahega aur kaam dugni speed se khatam hoga.", "widget": "circular_gauge", "kicker": "RESULT", "headline": "2X Kaam Ki Speed", "metric_big": "94%", "metric_label": "PEAK CLARITY", "left_label": "Lazy Din", "right_label": "Super Active", "pct": 94},
            {"tts_voice": "कल सुबह ये रूल ट्राई करो और रील सेव करके दोस्त को भेजो!", "caption": "Kal subah yeh rule try karo aur reel save karke dost ko bhejo!", "widget": "floating_checklist", "kicker": "TRY TOMORROW", "headline": "Morning Rule Lock Karo", "metric_big": "SAVE", "metric_label": "HABIT SHIFT", "left_label": "Phone Door Rakho", "right_label": "Paani & Stretch", "pct": 98}
        ]
    }
]

WHITE_PALETTES = [
    {"name": "apple_white_cobalt", "is_light": True, "bg": [248, 250, 253], "grid": [222, 232, 246], "card": [255, 255, 255], "card_border": [206, 220, 242], "text_main": [15, 23, 42], "text_muted": [92, 110, 136], "accent": [37, 99, 235], "secondary": [245, 158, 11], "positive": [16, 185, 129], "negative": [239, 68, 68]},
    {"name": "pure_paper_emerald", "is_light": True, "bg": [247, 252, 250], "grid": [216, 238, 230], "card": [255, 255, 255], "card_border": [198, 230, 218], "text_main": [14, 30, 26], "text_muted": [84, 115, 106], "accent": [5, 150, 105], "secondary": [217, 119, 6], "positive": [16, 185, 129], "negative": [225, 29, 72]}
]

DARK_PALETTES = [
    {"name": "midnight_cyan_neon", "is_light": False, "bg": [7, 11, 22], "grid": [20, 32, 58], "card": [14, 22, 40], "card_border": [46, 78, 136], "text_main": [248, 250, 252], "text_muted": [148, 163, 184], "accent": [56, 189, 248], "secondary": [250, 204, 21], "positive": [52, 211, 153], "negative": [248, 113, 113]},
    {"name": "obsidian_amber_gold", "is_light": False, "bg": [11, 10, 16], "grid": [32, 28, 44], "card": [20, 18, 29], "card_border": [74, 62, 96], "text_main": [250, 250, 250], "text_muted": [161, 161, 170], "accent": [245, 158, 11], "secondary": [56, 189, 248], "positive": [52, 211, 153], "negative": [244, 63, 94]},
    {"name": "cyber_emerald_dark", "is_light": False, "bg": [6, 15, 14], "grid": [17, 42, 38], "card": [12, 26, 24], "card_border": [36, 84, 75], "text_main": [240, 253, 250], "text_muted": [140, 175, 168], "accent": [16, 185, 129], "secondary": [250, 204, 21], "positive": [52, 211, 153], "negative": [248, 113, 113]},
    {"name": "crimson_noir_pro", "is_light": False, "bg": [14, 8, 12], "grid": [40, 20, 32], "card": [24, 14, 20], "card_border": [88, 36, 62], "text_main": [255, 248, 250], "text_muted": [175, 145, 158], "accent": [244, 63, 94], "secondary": [250, 204, 21], "positive": [52, 211, 153], "negative": [251, 113, 133]}
]

# 75% Dark Pro Neon weightage for maximum thumb-stop contrast on Instagram feed
if theme_mode == "white_grid":
    chosen_palette = rng.choice(WHITE_PALETTES)
elif theme_mode == "dark_pro":
    chosen_palette = rng.choice(DARK_PALETTES)
else:
    chosen_palette = rng.choice(DARK_PALETTES * 3 + WHITE_PALETTES)

used_history = load_used_topics()
unused_packs = [p for p in TOPIC_PACKS if p["caption_topic"].lower() not in [u.lower() for u in used_history]]
chosen_pack = rng.choice(unused_packs if unused_packs else TOPIC_PACKS)

CATEGORIES = [
    "Indian Middle-Class Money Traps, UPI Leaks & Hidden Bank/EMI Scams",
    "Salary Management, SIP Compounding & Everyday Chhote Kharche Reality Check",
    "Mobile Addiction, Dopamine Traps & Focus Hacks for Indian Youth",
    "Relatable Relationship, Respect & Dosti Psychology (When People Use You)",
    "Smart Career, Salary Negotiation & Office Politics Survival Secrets",
    "Consumer Marketing Tricks (Malls, Food Apps, Subscriptions) Fooling Indians"
]
chosen_category = rng.choice(CATEGORIES)

print(f"Theme: {chosen_palette['name']} | Category: {chosen_category} | Past Topics: {len(used_history)}")


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
        f'Write the script specifically on this topic: "{explicit_topic}"'
        if explicit_topic
        else f'Invent ONE brand-new, ultra-viral, hyper-relatable Indian Hinglish Reel topic in the category "{category_hint}" that has NEVER been covered in the avoid list above. Use concrete Indian numbers (₹, %, minutes, days) that make viewers DM-share the Reel to friends!'
    )

    return f"""You are India's #1 viral Instagram Reel scriptwriter & Premiere Pro motion graphics director for @sochbadlo.hq.
{topic_instruction}
{avoid_block}

Write an ultra-fast, addictive, high-retention 6-scene Hinglish Reel script (strictly 17 to 21 seconds total -> 7 to 9 punchy words per scene).

CRITICAL CONTENT, LANGUAGE & VISUAL DIRECTOR RULES:
1. NO BORING BOOKISH LECTURES: Never write generic English self-help titles like "Power of Silence" or "2-Minute Rule". Every headline and hook MUST be punchy Hinglish spoken by real Indians!
2. Scene 1 MUST be a shocking scroll-stopping hook with a concrete number or relatable trap. Scene 6 MUST be a share-trigger CTA ("Apne us dost ko bhejo...").
3. For EACH scene, return TWO spoken/caption fields:
   - 'tts_voice': Pure natural Devanagari Hindi script with English buzzwords written phonetically in Devanagari (e.g. write 'रूल' instead of 'rule', 'सेकंड' instead of 'second', 'यूपीआई' instead of 'UPI', 'ईएमआई' instead of 'EMI', 'मेन' NEVER for 'में') so TTS pronounces every word crisply!
   - 'caption': The exact same spoken sentence in clean Roman Hinglish (with ₹ symbols and numbers like ₹10, 90%, 15 min) for kinetic on-screen captions!
4. SCENE-MATCHED VISUAL DIRECTOR ('widget'): For EACH scene, choose the EXACT widget from this list that visually illustrates what is being spoken in THAT specific scene (do NOT use the same widget twice in a row):
   - "rupee_counter_shock": Best when mentioning a rupee loss, savings amount, price, or compounding figure (e.g. ₹10, ₹1,09,500)
   - "phone_upi_alert": Best when mentioning UPI payment, bank alert, mobile notification, app, or screen time
   - "scam_warning_stamp": Best when exposing a trap, scam, mistake, or danger
   - "vs_clash_cards": Best when comparing 2 choices (e.g. Gareeb vs Ameer mindset, Cash vs EMI, Bad vs Good habit)
   - "stock_line_graph": Best when showing growth, compounding, or steep drop over time
   - "animated_bar_chart": Best when comparing 3-5 levels, months, or years
   - "floating_checklist": Best for step-by-step rules or final action summary
   - "circular_gauge": Best for percentages (e.g. 90% log, 75% salary)
   - "typing_terminal_hud": Best for psychological facts, brain hacks, or system rules
   - "split_duel_banner": Best for old mistake vs winning shift
   - "step_pyramid_stack": Best for 3-level hierarchy or progression
   - "spotlight_stat_pill": Best for one giant shocking stat or time limit
5. Compact UI fields per scene (MUST be crisp Hinglish/numbers, MAX lengths strictly respected):
   - 'kicker': 2-word uppercase badge (MAX 16 chars, e.g. 'UPI POCKET LEAK', 'SALARY TRAP')
   - 'headline': 3-4 word punchy Hinglish title (MAX 26 chars, e.g. '₹10 Ki Chai Ka Scam', 'Salary Ka 40% Gayab')
   - 'metric_big': Punchy 2-6 char hero stat matching the spoken line (e.g. '₹1.09L', '18% GST', '90%', 'TRAP', 'SAVE')
   - 'metric_label': 2-word uppercase subtitle (MAX 16 chars, e.g. '10 SAAL KA LOSS', 'HIDDEN BANK FEE')
   - 'left_label': Short point A in Hinglish (MAX 16 chars)
   - 'right_label': Short point B in Hinglish (MAX 16 chars)
   - 'pct': Integer between 76 and 98

Return ONLY valid JSON with:
- "topic_title": Short unique Roman Hinglish title of this Reel (5-9 words)
- "thumbnail_hook": Ultra-catchy 4-6 word uppercase Hinglish cover headline for Frame 0 thumbnail (MAX 34 chars, e.g. "₹10 KI CHAI = ₹1.09 LAKH LOSS?!")
- "thumbnail_badge": 2-word red/gold cover stamp (MAX 16 chars, e.g. "99% INDIANS FAIL", "POCKET LEAK")
- "ig_caption": Engaging 3-line Hinglish Instagram caption with DM-share trigger + CTA to follow @sochbadlo.hq + 5 targeted hashtags
- "scenes": Array of 6 scene objects."""


def call_gemini_reliable(gemini_key, prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.95}
    }
    models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.0-flash", "gemini-flash-latest"]
    for model_name in models:
        endpoints = [
            (f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}", {"Content-Type": "application/json"}),
            (f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent", {"Content-Type": "application/json", "x-goog-api-key": gemini_key})
        ]
        for url, hdrs in endpoints:
            try:
                resp = requests.post(url, headers=hdrs, json=payload, timeout=30)
                if resp.status_code != 200:
                    print(f"Gemini {model_name} HTTP {resp.status_code}: {resp.text[:240]}")
                    continue
                r_json = resp.json()
                raw = r_json["candidates"][0]["content"]["parts"][0]["text"]
                raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
                data = json.loads(raw)
                if isinstance(data, list) and len(data) == 6:
                    data = {"scenes": data}
                if isinstance(data, dict) and "scenes" in data and len(data["scenes"]) == 6:
                    print(f"SUCCESS! Gemini API generated script-matched visual plan via {model_name}!")
                    return data
            except Exception as e:
                print(f"Gemini {model_name} retry:", e)
    return None


def generate_ai_script():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        prompt = build_prompt(raw_topic, used_history, chosen_category)
        data = call_gemini_reliable(gemini_key, prompt)
        if data:
            final_title = data.get("topic_title") or raw_topic or f"{chosen_category} #{len(used_history)+1}"
            save_used_topic(final_title)
            ig_cap = data.get("ig_caption", "").strip()
            if ig_cap:
                with open("caption.txt", "w", encoding="utf-8") as cf:
                    cf.write(ig_cap)
            print(f"Generated Unique Topic: {final_title}")
            return data

    fallback_title = chosen_pack["caption_topic"]
    save_used_topic(fallback_title)
    print(f"Using unused viral fallback pack: {fallback_title}")
    return {
        "topic_title": fallback_title,
        "thumbnail_hook": chosen_pack.get("thumbnail_hook", fallback_title.upper()[:34]),
        "thumbnail_badge": chosen_pack.get("thumbnail_badge", "VIRAL TRUTH"),
        "scenes": chosen_pack["scenes"]
    }


def generate_grid_canvases(scenes_list):
    os.makedirs("bg_assets", exist_ok=True)
    pal = chosen_palette
    is_light = pal.get("is_light", True)
    bg_c = tuple(pal["bg"])
    grid_c = tuple(pal["grid"])
    ac = tuple(pal["accent"])
    sc_c = tuple(pal["secondary"])

    for idx in range(len(scenes_list)):
        out_img = f"bg_assets/bg_{idx}.jpg"
        base = Image.new("RGB", (1080, 1920), bg_c)
        gd = ImageDraw.Draw(base)

        w_bg = 0.86 if is_light else 0.70
        w_ac = 1.0 - w_bg
        orb1 = tuple(int(bg_c[i] * w_bg + ac[i] * w_ac) for i in range(3))
        orb2 = tuple(int(bg_c[i] * w_bg + sc_c[i] * w_ac) for i in range(3))
        gd.ellipse([rng.randint(-150, 250), rng.randint(-100, 300), rng.randint(650, 1050), rng.randint(650, 1050)], fill=orb1)
        gd.ellipse([rng.randint(150, 450), rng.randint(950, 1300), rng.randint(850, 1200), rng.randint(1650, 2000)], fill=orb2)
        im = base.filter(ImageFilter.GaussianBlur(135))
        dr = ImageDraw.Draw(im)

        step = 60
        for gx in range(0, 1080, step):
            w_line = 2 if gx % (step * 4) == 0 else 1
            dr.line([(gx, 0), (gx, 1920)], fill=grid_c, width=w_line)
        for gy in range(0, 1920, step):
            w_line = 2 if gy % (step * 4) == 0 else 1
            dr.line([(0, gy), (1080, gy)], fill=grid_c, width=w_line)

        plus_c = tuple(int(grid_c[i] * 0.75 + ac[i] * 0.25) for i in range(3))
        for gx in range(step * 4, 1080, step * 4):
            for gy in range(step * 4, 1920, step * 4):
                dr.line([(gx - 10, gy), (gx + 10, gy)], fill=plus_c, width=2)
                dr.line([(gx, gy - 10), (gx, gy + 10)], fill=plus_c, width=2)

        im.save(out_img, quality=95)
    print("Generated 6 High-Contrast Studio Canvases!")


script_obj = generate_ai_script()
scenes_data = script_obj["scenes"]

resolved_widgets = []
last_w = ""
for i, sc in enumerate(scenes_data):
    w_req = str(sc.get("widget", "")).strip()
    if w_req not in ALLOWED_WIDGETS or w_req == last_w:
        choices = [w for w in ALLOWED_WIDGETS if w != last_w]
        w_req = rng.choice(choices)
    resolved_widgets.append(w_req)
    last_w = w_req

edit_dna = {
    "palette": chosen_palette,
    "widgets": resolved_widgets,
    "transition": rng.choice(["flash_zoom", "iris_reveal", "prism_wipe", "shutter_bars"]),
    "thumbnail_hook": str(script_obj.get("thumbnail_hook") or script_obj.get("topic_title") or scenes_data[0].get("headline", "SACH JAAN LO")).upper()[:38],
    "thumbnail_badge": str(script_obj.get("thumbnail_badge") or scenes_data[0].get("kicker", "REALITY CHECK")).upper()[:18]
}

generate_grid_canvases(scenes_data)

sfx_bank_plan = [
    [{"type": "sub_boom", "offset": 0.02}, {"type": "rise", "offset": 0.08}, {"type": "pop", "offset": 0.55}, {"type": "whoosh", "offset": 2.1}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "impact", "offset": 0.50}, {"type": "pop", "offset": 1.15}, {"type": "ping", "offset": 1.95}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "ping", "offset": 0.60}, {"type": "pop", "offset": 1.40}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "impact", "offset": 0.65}, {"type": "ping", "offset": 1.75}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "pop", "offset": 0.45}, {"type": "ping", "offset": 1.10}, {"type": "pop", "offset": 1.80}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "sub_boom", "offset": 0.80}, {"type": "ping", "offset": 1.90}]
]


def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())


def generate_sfx_bank():
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.38:c=pink:a=0.55", "-af", "bandpass=f=900:width_type=h:w=1300,afade=t=in:ss=0:d=0.07,afade=t=out:st=0.14:d=0.24", "sfx_whoosh.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=840:d=0.11", "-af", "asetrate=44100*0.74,aresample=44100,afade=t=out:st=0.02:d=0.09,volume=0.68", "sfx_pop.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=80:d=0.40", "-af", "afade=t=out:st=0.04:d=0.36,volume=1.05", "sfx_impact.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=50:d=0.55", "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.08:d=0.47,volume=1.15", "sfx_sub_boom.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1340:d=0.24", "-af", "afade=t=in:ss=0:d=0.015,afade=t=out:st=0.04:d=0.20,volume=0.58", "sfx_ping.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.48:c=pink:a=0.36", "-af", "highpass=f=650,afade=t=in:ss=0:d=0.36,afade=t=out:st=0.36:d=0.12", "sfx_rise.wav"], check=True)


def generate_elevenlabs_tts(text, out_file):
    el_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not el_key:
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
            "stability": 0.46,
            "similarity_boost": 0.78,
            "style": 0.38,
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
    rate = "+16%"
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

for idx, sc in enumerate(scenes_data):
    v_file = f"voice_{idx}.mp3"
    raw_v = f"raw_voice_{idx}.mp3"
    tts_text = sc.get("tts_voice", sc.get("caption", ""))
    cap_text = sc.get("caption", tts_text)

    ok = generate_elevenlabs_tts(tts_text, raw_v)
    if ok:
        print(f"SUCCESS! ElevenLabs Human Voice generated for Scene {idx+1}/6 [{resolved_widgets[idx]}]")
        af_str = "atempo=1.13,highpass=f=85,equalizer=f=190:width_type=h:width=120:g=2.5,equalizer=f=3600:width_type=h:width=1600:g=3.2,acompressor=threshold=-16dB:ratio=2.8:attack=5:release=50"
    else:
        print(f"Scene {idx+1}/6 using Edge-TTS fallback [{resolved_widgets[idx]}]")
        run_edge_tts_fallback(tts_text, raw_v)
        af_str = "highpass=f=90,equalizer=f=220:width_type=h:width=120:g=3,equalizer=f=3400:width_type=h:width=1600:g=3.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50"

    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)

    dur = get_duration(v_file) + 0.09
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "index": idx,
        "start": round(current_time, 3),
        "duration": round(dur, 3),
        "voice": cap_text,
        "kicker": str(sc.get("kicker", "INSIGHT"))[:18],
        "headline": str(sc.get("headline", ""))[:28],
        "metric_big": str(sc.get("metric_big", "95%"))[:8],
        "metric_label": str(sc.get("metric_label", "PROVEN IMPACT"))[:18],
        "left_label": str(sc.get("left_label", "Purana Tareeka"))[:18],
        "right_label": str(sc.get("right_label", "Smart Move"))[:18],
        "pct": int(sc.get("pct", 92)),
        "widget": resolved_widgets[idx],
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

print(f"V18 Premiere-Pro Dynamic Visual Director + Custom Thumbnail Engine Ready! ({round(current_time, 2)}s)")
