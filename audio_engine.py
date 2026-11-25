import sys
import subprocess
import json
import os
import time
import re
import random
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageEnhance

raw_topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "wise_human"
theme_mode = sys.argv[3].strip() if len(sys.argv) > 3 else "random"

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


TOPIC_PACKS = [
    {
        "caption_topic": "Medical Store Par ₹450 Ki Dawai Jan Aushadhi Mein Sirf ₹45 Ki Kaise Milti Hai",
        "style": "theme_1",
        "thumbnail_hook": "SAME DAWAI ₹450 VS ₹45?!",
        "thumbnail_badge": "BILL EVIDENCE",
        "scenes": [
            {"tts_voice": "अरे भाई... मेडिकल स्टोर पर जो दवाई चार सौ पचास रुपये की मिलती है ना, वही सरकारी दुकान पर सिर्फ पैंतालीस रुपये की है!", "caption": "Are bhai... medical store par jo dawai ₹450 ki milti hai na, wahi sarkari dukaan par sirf ₹45 ki hai!", "highlight": "₹450 VS ₹45", "doc_tag": "DOC. #0412", "emotion": "shocked", "photo_prompt": "candid realistic photo of an Indian pharmacy medicine strip and printed paper bill on a wooden counter, natural lighting, 35mm documentary photography", "effect": "highlighter_circle"},
            {"tts_voice": "हँसी आती है ये सोच कर... कि फर्क सिर्फ कंपनी के महंगे नाम और कमीशन का है, अंदर का सॉल्ट सौ परसेंट सेम है!", "caption": "Hansi aati hai yeh soch kar... ki farq sirf company ke mehenge naam ka hai, andar ka salt 100% same hai!", "highlight": "100% SAME SALT", "doc_tag": "SALT FORMULA", "emotion": "chuckle", "photo_prompt": "close up candid photo of generic medicine tablets blister pack next to branded medicine box on table, natural daylight, realistic photo", "effect": "yellow_highlight"},
            {"tts_voice": "बस दवाई के पत्ते के पीछे लिखा जेनेरिक सॉल्ट नाम ध्यान से पढ़ो... और गूगल पर चेक करो।", "caption": "Bas dawai ke patte ke peeche likha generic salt naam dhyan se padho... aur Google par check karo.", "highlight": "SALT CHECK KARO", "doc_tag": "BACK LABEL", "emotion": "wise", "photo_prompt": "candid photo of Indian hands holding a medicine strip reading the back label in natural sunlight, 35mm realistic photography", "effect": "red_circle"},
            {"tts_voice": "इसके बाद अपने नज़दीकी प्रधानमंत्री जन औषधि केंद्र पर जाकर... सीधे वही सॉल्ट मांगो।", "caption": "Iske baad apne nazdeeki Jan Aushadhi Kendra par jaakar... seedhe wahi salt maango.", "highlight": "JAN AUSHADHI", "doc_tag": "GOVT STORE", "emotion": "wise", "photo_prompt": "realistic street level candid photo of an Indian medical pharmacy storefront during daytime, natural colors, 35mm lens", "effect": "yellow_highlight"},
            {"tts_voice": "यकीन मानो, हर महीने घर की दवाई का बिल अस्सी परसेंट तक कम हो जाएगा।", "caption": "Yakeen mano, har mahine ghar ki dawai ka bill 80% tak kam ho jayega.", "highlight": "80% BACHAT", "doc_tag": "MONTHLY SAVE", "emotion": "warm", "photo_prompt": "candid realistic photo of Indian rupee notes and a small pharmacy receipt kept inside a middle class wallet, natural light", "effect": "highlighter_circle"},
            {"tts_voice": "ये बात हर घर को पता होनी चाहिए... अभी अपने परिवार के व्हाट्सएप ग्रुप में शेयर करो!", "caption": "Yeh baat har ghar ko pata honi chahiye... abhi apne parivar ke WhatsApp group mein share karo!", "highlight": "SHARE NOW", "doc_tag": "FAMILY ALERT", "emotion": "urgent", "photo_prompt": "candid warm photo of an Indian son showing his smartphone screen to his parents at home living room, natural lighting, 35mm film", "effect": "yellow_highlight"}
        ]
    },
    {
        "caption_topic": "Jo Dost Har Baat Par Bole Mazak Tha Woh Asal Mein Tumse Jalta Hai",
        "style": "theme_3",
        "thumbnail_hook": "JO DOST BOLE 'MAZAK THA'...",
        "thumbnail_badge": "Dusk, 6:14 PM",
        "scenes": [
            {"tts_voice": "जो दोस्त सबके सामने तुम्हारी बेइज़्ज़ती करके... हँसते हुए बोलता है, अरे मैं तो मज़ाक कर रहा था...", "caption": "Jo dost sabke saamne tumhari beizzati karke... hanste hue bolta hai, are main toh mazak kar raha tha...", "highlight": "MAZAK THA", "doc_tag": "Sign 01", "emotion": "chuckle", "photo_prompt": "candid realistic photo of two Indian friends at a college canteen table, one looking slightly hurt while other laughs, natural daylight, 35mm", "effect": "red_underline"},
            {"tts_voice": "सच कहूँ दोस्त... वो मज़ाक नहीं कर रहा होता, बल्कि अपने दिल की जलन को हँसी के पीछे छुपा रहा होता है।", "caption": "Sach kahoon dost... woh mazak nahi kar raha hota, balki apne dil ki jalan ko hansi ke peeche chhupa raha hota hai.", "highlight": "JALAN", "doc_tag": "Deep Truth", "emotion": "wise", "photo_prompt": "candid close up portrait of a thoughtful young Indian man looking away at an evening cafe, moody natural lighting, 35mm film", "effect": "red_underline"},
            {"tts_voice": "क्योंकि असली दोस्त तुम्हारी कमियों को अकेले में बताता है... भरी महफ़िल में तमाशा नहीं बनाता।", "caption": "Kyunki asli dost tumhari kamiyon ko akele mein batata hai... bhari mehfil mein tamasha nahi banata.", "highlight": "ASLI DOST", "doc_tag": "Golden Rule", "emotion": "wise", "photo_prompt": "candid photo of two Indian friends walking together on a quiet tree-lined street having a serious honest conversation, natural light", "effect": "yellow_highlight"},
            {"tts_voice": "याद रखना... तुम्हारी जीत पर जिसकी मुस्कान फीकी पड़ जाए, उससे दूरी बना लेना ही बेहतर है।", "caption": "Yaad rakhna... tumhari jeet par jiski muskaan feeki pad jaaye, usse doori bana lena hi behtar hai.", "highlight": "DOORI BANA LENA", "doc_tag": "Warning", "emotion": "serious", "photo_prompt": "candid photo of a young Indian man standing alone near a rainy window looking outside, calm contemplative mood, 35mm photography", "effect": "red_underline"},
            {"tts_voice": "कम दोस्त रखो... लेकिन ऐसे रखो जो तुम्हारी पीठ पीछे भी तुम्हारी इज़्ज़त करें।", "caption": "Kam dost rakho... lekin aise rakho jo tumhari peeth peeche bhi tumhari izzat karein.", "highlight": "IZZAT", "doc_tag": "Wisdom", "emotion": "warm", "photo_prompt": "candid warm photograph of two loyal Indian friends sharing cutting chai at a roadside tapri during golden hour sunset, 35mm", "effect": "yellow_highlight"},
            {"tts_voice": "अपने उस एक सच्चे दोस्त को यह रील भेज कर... आज शुक्रिया ज़रूर कहना।", "caption": "Apne us ek sachche dost ko yeh reel bhej kar... aaj shukriya zaroor kehna.", "highlight": "SHUKRIYA", "doc_tag": "Send Now", "emotion": "warm", "photo_prompt": "candid photo of two Indian friends smiling and fist bumping at an evening street market, natural warm light, 35mm film", "effect": "yellow_highlight"}
        ]
    },
    {
        "caption_topic": "25 Ki Umar Ke Baad Jab Salary 10 Tareekh Ko Khatam Ho Jaati Hai",
        "style": "theme_5",
        "thumbnail_hook": "25 KE BAAD SALARY 10 TAREEKH KO KHATAM...",
        "thumbnail_badge": "MIDDLE CLASS REALITY",
        "scenes": [
            {"tts_voice": "पच्चीस की उम्र के बाद जब सैलरी दस तारीख को ही खत्म हो जाती है ना... तब असली ज़िंदगी समझ आती है।", "caption": "25 ki umar ke baad jab salary 10 tareekh ko hi khatam ho jaati hai na... tab asli zindagi samajh aati hai.", "highlight": "10 TAREEKH", "doc_tag": "REALITY", "emotion": "emotional", "photo_prompt": "cinematic moody 35mm film still of a tired young Indian man in his late 20s standing on a rainy Delhi metro platform at night, warm street lamps, realistic", "effect": "none"},
            {"tts_voice": "रेंट, ईएमआई, घर के खर्च... और दोस्तों के सामने मुस्कुराने की एक्टिंग सब एक साथ चलती है, हाहा!", "caption": "Rent, EMI, ghar ke kharch... aur doston ke saamne muskurane ki acting sab ek saath chalti hai!", "highlight": "MUSKURANE KI ACTING", "doc_tag": "PRESSURE", "emotion": "chuckle", "photo_prompt": "candid moody photo of a young Indian office worker sitting at a desk late evening looking out window, dim warm office lamp, 35mm film grain", "effect": "none"},
            {"tts_voice": "घर वाले फोन पर पूछते हैं सब ठीक है ना... और हम खाली जेब के साथ कह देते हैं, हाँ माँ सब बढ़िया है।", "caption": "Ghar wale phone par poochte hain sab theek hai na... aur hum khaali jeb ke saath keh dete hain, haan maa sab badhiya hai.", "highlight": "KHAALI JEB", "doc_tag": "SILENCE", "emotion": "emotional", "photo_prompt": "realistic candid photo of an Indian young man talking on phone on a quiet balcony at dusk, emotional expression, natural lighting, 35mm", "effect": "none"},
            {"tts_voice": "इस उम्र में कोई हमारा हाल नहीं पूछता भाई... सिर्फ हमारी कमाई और हैसियत देखी जाती है।", "caption": "Is umar mein koi hamara haal nahi poochta bhai... sirf hamari kamai aur haisiyat dekhi jaati hai.", "highlight": "KAMAI AUR HAISIYAT", "doc_tag": "TRUTH", "emotion": "wise", "photo_prompt": "cinematic candid shot of an Indian man walking alone through crowded evening market street, shallow depth of field, moody film look", "effect": "none"},
            {"tts_voice": "पर यही वो दौर है... जो एक आम लड़के को अंदर से फौलाद बना देता है।", "caption": "Par yahi woh daur hai... jo ek aam ladke ko andar se faulad bana deta hai.", "highlight": "FAULAD", "doc_tag": "STRENGTH", "emotion": "wise", "photo_prompt": "realistic early morning photo of an Indian young man drinking tea on rooftop watching sunrise over city rooftops, hopeful mood, 35mm", "effect": "none"},
            {"tts_voice": "अगर तुम भी इस दौर से गुज़र रहे हो... तो यह रील अपने उस जिगरी दोस्त को भेजो।", "caption": "Agar tum bhi is daur se guzar rahe ho... toh yeh reel apne us jigri dost ko bhejo.", "highlight": "JIGRI DOST", "doc_tag": "BROTHERHOOD", "emotion": "warm", "photo_prompt": "candid photo of two Indian male friends sitting on a motorbike talking at roadside tea stall at night, warm street light, 35mm film", "effect": "none"}
        ]
    }
]

used_history = load_used_topics()
unused_packs = [p for p in TOPIC_PACKS if p["caption_topic"].lower() not in [u.lower() for u in used_history]]
chosen_pack = rng.choice(unused_packs if unused_packs else TOPIC_PACKS)

CATEGORIES = [
    ("theme_1", "Hidden Indian Consumer Scams, Medical/Bank/Food App Traps & Real Savings Hacks (Investigative Newspaper Style)"),
    ("theme_3", "Real Dosti, Fake Friends, Respect & Silent Human Psychology Truths (Intimate Polaroid POV)"),
    ("theme_5", "25+ Middle-Class Salary Struggle, Ghar Ki Zimmedari & Late Night Overthinking (Warm Desi Storytelling)")
]
chosen_style, chosen_category = rng.choice(CATEGORIES)
if theme_mode in ("theme_1", "theme_3", "theme_5"):
    chosen_style = theme_mode

print(f"Selected Theme: {chosen_style} | Category: {chosen_category} | Past Topics: {len(used_history)}")


def build_prompt(explicit_topic, past_topics, style_name, category_hint):
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
        else f'Invent ONE brand-new, ultra-relatable, high-share Indian Hinglish Reel topic in the category "{category_hint}" that has NEVER been covered in the avoid list above. Write like a wise, experienced Indian elder brother/mentor speaking from real life—NOT a robotic AI listicle!'
    )

    return f"""You are a wise, emotionally expressive Indian storyteller & documentary Reel director for @sochbadlo.hq.
{topic_instruction}
{avoid_block}

Write a gripping, deeply relatable 6-scene Hinglish Reel script (18 to 22 seconds total -> 9 to 12 natural spoken words per scene).

CRITICAL VOICE & HUMAN EMOTION RULES:
1. WISE HUMAN MENTOR TONE: Speak like a grounded, wise Indian storyteller having a heart-to-heart conversation ("अरे भाई...", "सच कहूँ दोस्त...", "याद रखना..."). Use natural pauses (`...`), subtle ironic chuckles/smiles where fitting ("हँसी आती है ये सोच कर...", "हाहा!"), and deep warmth.
2. NO ROBOTIC LISTICLES: Never say "Pehla point, doosra point". Tell a cohesive 6-beat real-life story or investigative reveal with a strong 2-second open-loop hook in Scene 1, an emotional/factual twist in Scene 3/4, and a natural DM-share trigger in Scene 6.
3. For EACH scene, return:
   - 'tts_voice': Pure natural Devanagari Hindi script with English words written phonetically in Devanagari (e.g. 'सैलरी', 'मेडिकल', 'ईएमआई', 'व्हाट्सएप') and natural pauses (`...`) so the voiceover sounds like a wise, warm, emotional human!
   - 'caption': The exact same spoken sentence in clean Roman Hinglish (with ₹ symbols and numbers) for minimal subtitles.
   - 'highlight': The 1-3 most powerful words from 'caption' (uppercase, MAX 20 chars) to highlight.
   - 'doc_tag': Tiny 1-2 word documentary/timestamp label (MAX 16 chars, e.g. 'DOC. #0412', 'Dusk, 6:14 PM', 'REALITY').
   - 'emotion': One of ["wise", "chuckle", "emotional", "shocked", "warm", "serious", "urgent"] controlling voice pitch, pacing, and expressive delivery!
   - 'photo_prompt': A detailed, 100% REALISTIC CANDID PHOTOGRAPHY prompt (shot on 35mm film, natural lighting, Indian setting, real human emotion or real document/object) that directly shows what is being spoken in THAT scene. NEVER ask for 3D renders, neon lights, charts, or futuristic graphics!
   - 'effect': Choose one of ["highlighter_circle", "yellow_highlight", "red_circle", "red_underline", "none"] matching the mood.

Return ONLY valid JSON with:
- "topic_title": Short unique Roman Hinglish title (5-9 words)
- "thumbnail_hook": Punchy 4-6 word uppercase Hinglish hook for Frame 0 cover (MAX 34 chars)
- "thumbnail_badge": 2-word documentary stamp (MAX 16 chars, e.g. "BILL EVIDENCE", "Dusk, 6:14 PM", "GHAR KI ZIMMEDARI")
- "ig_caption": Raw, human 3-line Hinglish Instagram caption with DM-share question + 5 relevant hashtags
- "scenes": Array of 6 scene objects."""


def call_gemini_reliable(gemini_key, prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.92}
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
                    print(f"Gemini {model_name} HTTP {resp.status_code}: {resp.text[:220]}")
                    continue
                r_json = resp.json()
                raw = r_json["candidates"][0]["content"]["parts"][0]["text"]
                raw = re.sub(r"^```json\s*|```$", "", raw.strip(), flags=re.MULTILINE).strip()
                data = json.loads(raw)
                if isinstance(data, list) and len(data) == 6:
                    data = {"scenes": data}
                if isinstance(data, dict) and "scenes" in data and len(data["scenes"]) == 6:
                    print(f"SUCCESS! Gemini generated wise human script via {model_name}!")
                    return data
            except Exception as e:
                print(f"Gemini {model_name} retry:", e)
    return None


def generate_ai_script():
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        prompt = build_prompt(raw_topic, used_history, chosen_style, chosen_category)
        data = call_gemini_reliable(gemini_key, prompt)
        if data:
            final_title = data.get("topic_title") or raw_topic or f"{chosen_category} #{len(used_history)+1}"
            save_used_topic(final_title)
            ig_cap = data.get("ig_caption", "").strip()
            if ig_cap:
                with open("caption.txt", "w", encoding="utf-8") as cf:
                    cf.write(ig_cap)
            print(f"Generated Unique Story: {final_title}")
            return data

    fallback_title = chosen_pack["caption_topic"]
    save_used_topic(fallback_title)
    print(f"Using unused wise storytelling pack: {fallback_title}")
    return {
        "topic_title": fallback_title,
        "thumbnail_hook": chosen_pack.get("thumbnail_hook", fallback_title.upper()[:34]),
        "thumbnail_badge": chosen_pack.get("thumbnail_badge", "REALITY CHECK"),
        "scenes": chosen_pack["scenes"]
    }


def fetch_or_build_real_photos(scenes_list, style_name):
    """Downloads real candid 35mm photographic scenes via Pollinations Flux with textured editorial fallback."""
    os.makedirs("bg_assets", exist_ok=True)
    for idx, sc in enumerate(scenes_list):
        out_img = f"bg_assets/bg_{idx}.jpg"
        raw_prompt = sc.get("photo_prompt", "candid realistic photo of an Indian young man in city evening, 35mm film photography")
        full_prompt = f"{raw_prompt}, raw candid documentary photograph, natural lighting, subtle 35mm film grain, no text, no watermark, no 3d render, no neon"
        encoded = urllib.parse.quote(full_prompt)
        seed = rng.randint(1000, 999999)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={seed}"

        downloaded = False
        for attempt in range(2):
            try:
                r = requests.get(url, timeout=35)
                if r.status_code == 200 and len(r.content) > 25000:
                    with open(out_img, "wb") as f:
                        f.write(r.content)
                    im = Image.open(out_img).convert("RGB").resize((1080, 1920), Image.Resampling.LANCZOS)
                    if style_name == "theme_1":
                        # Archival documentary photo look
                        im = ImageEnhance.Color(im).enhance(0.25)
                        im = ImageEnhance.Contrast(im).enhance(1.20)
                    elif style_name == "theme_3":
                        # Moody Polaroid film tone
                        im = ImageEnhance.Color(im).enhance(0.84)
                        im = ImageEnhance.Contrast(im).enhance(1.15)
                    else:
                        # Theme 5: Warm Espresso cinema grade
                        im = ImageEnhance.Color(im).enhance(0.82)
                        im = ImageEnhance.Contrast(im).enhance(1.16)
                        im = ImageEnhance.Brightness(im).enhance(0.80)
                    im.save(out_img, quality=94)
                    downloaded = True
                    print(f"Scene {idx+1}/6: Real candid 35mm photo ready!")
                    break
            except Exception as e:
                print(f"Photo fetch retry {idx+1}:", e)
            time.sleep(1.0)

        if not downloaded:
            base_map = {"theme_1": (243, 239, 230), "theme_3": (22, 22, 24), "theme_5": (24, 18, 14)}
            base_c = base_map.get(style_name, (22, 22, 24))
            im = Image.new("RGB", (1080, 1920), base_c)
            dr = ImageDraw.Draw(im)
            for _ in range(11000):
                gx = rng.randint(0, 1079)
                gy = rng.randint(0, 1919)
                delta = rng.randint(-10, 10)
                c = tuple(max(0, min(255, base_c[k] + delta)) for k in range(3))
                dr.point((gx, gy), fill=c)
            im.save(out_img, quality=92)
            print(f"Scene {idx+1}/6: Textured paper/film fallback ready!")


script_obj = generate_ai_script()
scenes_data = script_obj["scenes"]

edit_dna = {
    "style": chosen_style,
    "thumbnail_hook": str(script_obj.get("thumbnail_hook") or script_obj.get("topic_title") or "SACH JAAN LO").upper()[:36],
    "thumbnail_badge": str(script_obj.get("thumbnail_badge") or "REALITY CHECK")[:18]
}

fetch_or_build_real_photos(scenes_data, chosen_style)

sfx_bank_plan = [
    [{"type": "thud", "offset": 0.02}, {"type": "paper", "offset": 0.35}],
    [{"type": "cut", "offset": 0.03}, {"type": "tick", "offset": 0.85}],
    [{"type": "cut", "offset": 0.03}, {"type": "paper", "offset": 0.45}],
    [{"type": "thud", "offset": 0.03}, {"type": "tick", "offset": 0.90}],
    [{"type": "cut", "offset": 0.03}, {"type": "paper", "offset": 0.40}],
    [{"type": "cut", "offset": 0.03}, {"type": "tick", "offset": 0.75}]
]


def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())


def generate_sfx_bank():
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.28:c=pink:a=0.24", "-af", "bandpass=f=1400:width_type=h:w=900,afade=t=in:ss=0:d=0.05,afade=t=out:st=0.10:d=0.18", "sfx_paper.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.14:c=white:a=0.20", "-af", "bandpass=f=1100:width_type=h:w=800,afade=t=out:st=0.03:d=0.11", "sfx_cut.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=56:d=0.36", "-af", "afade=t=in:ss=0:d=0.015,afade=t=out:st=0.05:d=0.31,volume=0.80", "sfx_thud.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=960:d=0.06", "-af", "afade=t=out:st=0.01:d=0.05,volume=0.30", "sfx_tick.wav"], check=True)


def generate_elevenlabs_tts(text, out_file, emotion="wise"):
    el_key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not el_key:
        return False

    # Deep wise storyteller male voice (Brian / Antoni style) or warm expressive female
    voice_id = "cgSgspJ2msm6clMCkdW9" if voice_style == "cute_viral" else "nPczCjzI2devNBz1zQrb"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": el_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}

    # Dynamic emotion tuning for human expression & subtle chuckle/warmth
    emo_map = {
        "chuckle": {"stability": 0.34, "style": 0.58},
        "emotional": {"stability": 0.42, "style": 0.52},
        "shocked": {"stability": 0.38, "style": 0.55},
        "wise": {"stability": 0.50, "style": 0.42},
        "warm": {"stability": 0.46, "style": 0.48},
        "serious": {"stability": 0.54, "style": 0.38},
        "urgent": {"stability": 0.40, "style": 0.54},
    }
    cfg = emo_map.get(emotion, {"stability": 0.46, "style": 0.45})

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": cfg["stability"],
            "similarity_boost": 0.82,
            "style": cfg["style"],
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
            if r.status_code in (401, 402, 429):
                break
        except Exception:
            pass
        time.sleep(1.5)
    return False


def run_edge_tts_fallback(text, out_file, emotion="wise"):
    """Expressive wise human neural voice fallback with emotion-aware pitch & rate."""
    voice_name = "hi-IN-SwaraNeural" if voice_style == "cute_viral" else "hi-IN-MadhurNeural"
    emo_prosody = {
        "chuckle": ("+10%", "+3Hz"),
        "emotional": ("+3%", "-4Hz"),
        "shocked": ("+12%", "+2Hz"),
        "wise": ("+5%", "-3Hz"),
        "warm": ("+6%", "-2Hz"),
        "serious": ("+4%", "-4Hz"),
        "urgent": ("+11%", "+1Hz"),
    }
    rate_str, pitch_str = emo_prosody.get(emotion, ("+6%", "-3Hz"))
    for attempt in range(5):
        res = subprocess.run([
            "edge-tts", "--voice", voice_name,
            "--rate", rate_str, "--pitch", pitch_str,
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
    emotion = str(sc.get("emotion", "wise")).lower()

    ok = generate_elevenlabs_tts(tts_text, raw_v, emotion=emotion)
    if ok:
        # Warm studio chest resonance + crisp human clarity
        af_str = "atempo=1.03,highpass=f=80,equalizer=f=155:width_type=h:width=110:g=2.8,equalizer=f=3200:width_type=h:width=1400:g=2.2,acompressor=threshold=-16dB:ratio=2.4:attack=8:release=70"
    else:
        run_edge_tts_fallback(tts_text, raw_v, emotion=emotion)
        af_str = "highpass=f=85,equalizer=f=165:width_type=h:width=110:g=3.0,acompressor=threshold=-16dB:ratio=2.5:attack=8:release=70"

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
        "highlight": str(sc.get("highlight", ""))[:22].upper(),
        "doc_tag": str(sc.get("doc_tag", f"SCENE 0{idx+1}"))[:18],
        "emotion": emotion,
        "effect": str(sc.get("effect", "yellow_highlight")),
        "bg_path": f"bg_assets/bg_{idx}.jpg"
    })

    for s in sfx_bank_plan[idx]:
        offset = min(s["offset"], max(0.05, dur - 0.20))
        sfx_time_ms = int((current_time + offset) * 1000)
        sfx_inputs.extend(["-i", f"sfx_{s['type']}.wav"])
        sfx_counter += 1
        filter_complex.append(f"[{sfx_counter}:a]adelay={sfx_time_ms}|{sfx_time_ms}[s{sfx_counter}]")

    current_time += dur

with open("vlist.txt", "w") as f:
    for vf in voice_files:
        f.write(f"file '{vf}'\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "vlist.txt", "full_voice.wav"], check=True)

# Subtle warm cinema room tone
subprocess.run([
    "ffmpeg", "-y", "-f", "lavfi",
    "-i", f"aevalsrc=0.020*sin(2*PI*55*t)+0.010*sin(2*PI*110*t):d={current_time+1}",
    "-af", "lowpass=f=220,afade=t=in:ss=0:d=0.6,afade=t=out:st=" + str(max(0.5, current_time - 0.6)) + ":d=0.6",
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

print(f"V20 Wise Human Voice + Themes 1/3/5 Engine Ready! ({round(current_time, 2)}s)")
