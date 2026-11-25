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
            {
                "tts_voice": "अरे भाई... मेडिकल स्टोर पर जो दवाई चार सौ पचास रुपये की मिलती है ना, वही सरकारी दुकान पर सिर्फ पैंतालीस रुपये की है!",
                "caption": "Are bhai... medical store par jo dawai ₹450 ki milti hai na, wahi sarkari dukaan par sirf ₹45 ki hai!",
                "highlight": "₹450 VS ₹45",
                "doc_tag": "DOC. #0412",
                "emotion": "shocked",
                "wiki_query": "Indian pharmacy medicine shop counter",
                "photo_prompt": "natural unedited smartphone photo of an Indian pharmacy counter with medicine strips and a printed paper bill in warm daylight, authentic Indian shop background, shot on 35mm lens",
                "effect": "highlighter_circle"
            },
            {
                "tts_voice": "हँसी आती है ये सोच कर... कि फर्क सिर्फ कंपनी के महंगे नाम और कमीशन का है, अंदर का सॉल्ट सौ परसेंट सेम है!",
                "caption": "Hansi aati hai yeh soch kar... ki farq sirf company ke mehenge naam ka hai, andar ka salt 100% same hai!",
                "highlight": "100% SAME SALT",
                "doc_tag": "SALT FORMULA",
                "emotion": "chuckle",
                "wiki_query": "medicine blister pack tablets close up",
                "photo_prompt": "natural close-up daylight photo of two medicine blister strips kept on a wooden home table in India, realistic shadows, organic colors, authentic photography",
                "effect": "yellow_highlight"
            },
            {
                "tts_voice": "बस दवाई के पत्ते के पीछे लिखा जेनेरिक सॉल्ट नाम ध्यान से पढ़ो... और गूगल पर चेक करो।",
                "caption": "Bas dawai ke patte ke peeche likha generic salt naam dhyan se padho... aur Google par check karo.",
                "highlight": "SALT CHECK KARO",
                "doc_tag": "BACK LABEL",
                "emotion": "wise",
                "wiki_query": "hand holding medicine strip reading label",
                "photo_prompt": "candid natural photo of an Indian person holding a medicine strip near a window reading the back label in morning sunlight, realistic skin texture",
                "effect": "red_circle"
            },
            {
                "tts_voice": "इसके बाद अपने नज़दीकी प्रधानमंत्री जन औषधि केंद्र पर जाकर... सीधे वही सॉल्ट मांगो।",
                "caption": "Iske baad apne nazdeeki Jan Aushadhi Kendra par jaakar... seedhe wahi salt maango.",
                "highlight": "JAN AUSHADHI",
                "doc_tag": "GOVT STORE",
                "emotion": "wise",
                "wiki_query": "Jan Aushadhi Kendra pharmacy India",
                "photo_prompt": "candid street-level daytime photograph of a neighborhood medical store in an Indian market with scooters parked outside, natural sunlight, realistic colors",
                "effect": "yellow_highlight"
            },
            {
                "tts_voice": "यकीन मानो, हर महीने घर की दवाई का बिल अस्सी परसेंट तक कम हो जाएगा।",
                "caption": "Yakeen mano, har mahine ghar ki dawai ka bill 80% tak kam ho jayega.",
                "highlight": "80% BACHAT",
                "doc_tag": "MONTHLY SAVE",
                "emotion": "warm",
                "wiki_query": "Indian rupee notes wallet cash",
                "photo_prompt": "natural everyday photograph of Indian 500 and 100 rupee notes inside a worn leather wallet on a wooden table, soft indoor daylight",
                "effect": "highlighter_circle"
            },
            {
                "tts_voice": "ये बात हर घर को पता होनी चाहिए... अभी अपने परिवार के व्हाट्सएप ग्रुप में शेयर करो!",
                "caption": "Yeh baat har ghar ko pata honi chahiye... abhi apne parivar ke WhatsApp group mein share karo!",
                "highlight": "SHARE NOW",
                "doc_tag": "FAMILY ALERT",
                "emotion": "urgent",
                "wiki_query": "Indian family living room tea",
                "photo_prompt": "warm candid photograph of an Indian young man sitting with his parents in a middle-class Indian living room showing something on his phone, natural home lighting",
                "effect": "yellow_highlight"
            }
        ]
    },
    {
        "caption_topic": "Jo Dost Har Baat Par Bole Mazak Tha Woh Asal Mein Tumse Jalta Hai",
        "style": "theme_3",
        "thumbnail_hook": "JO DOST BOLE 'MAZAK THA'...",
        "thumbnail_badge": "Dusk, 6:14 PM",
        "scenes": [
            {
                "tts_voice": "जो दोस्त सबके सामने तुम्हारी बेइज़्ज़ती करके... हँसते हुए बोलता है, अरे मैं तो मज़ाक कर रहा था...",
                "caption": "Jo dost sabke saamne tumhari beizzati karke... hanste hue bolta hai, are main toh mazak kar raha tha...",
                "highlight": "MAZAK THA",
                "doc_tag": "Sign 01",
                "emotion": "chuckle",
                "wiki_query": "Indian friends talking tea stall",
                "photo_prompt": "natural candid evening photograph of two young Indian men sitting at a roadside chai tapri in Delhi, one laughing while the other looks thoughtful, warm street light",
                "effect": "red_underline"
            },
            {
                "tts_voice": "सच कहूँ दोस्त... वो मज़ाक नहीं कर रहा होता, बल्कि अपने दिल की जलन को हँसी के पीछे छुपा रहा होता है।",
                "caption": "Sach kahoon dost... woh mazak nahi kar raha hota, balki apne dil ki jalan ko hansi ke peeche chhupa raha hota hai.",
                "highlight": "JALAN",
                "doc_tag": "Deep Truth",
                "emotion": "wise",
                "wiki_query": "young Indian man thoughtful portrait evening",
                "photo_prompt": "candid natural portrait of an ordinary young Indian man in a casual cotton shirt looking quietly towards the street at dusk, realistic skin tones, soft natural light",
                "effect": "red_underline"
            },
            {
                "tts_voice": "क्योंकि असली दोस्त तुम्हारी कमियों को अकेले में बताता है... भरी महफ़िल में तमाशा नहीं बनाता।",
                "caption": "Kyunki asli dost tumhari kamiyon ko akele mein batata hai... bhari mehfil mein tamasha nahi banata.",
                "highlight": "ASLI DOST",
                "doc_tag": "Golden Rule",
                "emotion": "wise",
                "wiki_query": "two friends walking street India",
                "photo_prompt": "natural candid photograph of two Indian friends walking side by side on a quiet residential colony road at sunset having an honest talk, warm natural light",
                "effect": "yellow_highlight"
            },
            {
                "tts_voice": "याद रखना... तुम्हारी जीत पर जिसकी मुस्कान फीकी पड़ जाए, उससे दूरी बना लेना ही बेहतर है।",
                "caption": "Yaad rakhna... tumhari jeet par jiski muskaan feeki pad jaaye, usse doori bana lena hi behtar hai.",
                "highlight": "DOORI BANA LENA",
                "doc_tag": "Warning",
                "emotion": "serious",
                "wiki_query": "Indian man looking out window rain",
                "photo_prompt": "natural candid photo of a young Indian man standing near an apartment balcony railing looking out at evening traffic, calm expression, realistic lighting",
                "effect": "red_underline"
            },
            {
                "tts_voice": "कम दोस्त रखो... लेकिन ऐसे रखो जो तुम्हारी पीठ पीछे भी तुम्हारी इज़्ज़त करें।",
                "caption": "Kam dost rakho... lekin aise rakho jo tumhari peeth peeche bhi tumhari izzat karein.",
                "highlight": "IZZAT",
                "doc_tag": "Wisdom",
                "emotion": "warm",
                "wiki_query": "cutting chai glass Indian roadside",
                "photo_prompt": "natural close-up candid photo of two glasses of hot masala chai on a wooden bench at an Indian roadside stall during golden hour, warm authentic vibe",
                "effect": "yellow_highlight"
            },
            {
                "tts_voice": "अपने उस एक सच्चे दोस्त को यह रील भेज कर... आज शुक्रिया ज़रूर कहना।",
                "caption": "Apne us ek sachche dost ko yeh reel bhej kar... aaj shukriya zaroor kehna.",
                "highlight": "SHUKRIYA",
                "doc_tag": "Send Now",
                "emotion": "warm",
                "wiki_query": "Indian friends smiling street evening",
                "photo_prompt": "candid genuine photo of two Indian male friends smiling warmly together beside a parked motorcycle in an evening Indian market, natural warm light",
                "effect": "yellow_highlight"
            }
        ]
    },
    {
        "caption_topic": "25 Ki Umar Ke Baad Jab Salary 10 Tareekh Ko Khatam Ho Jaati Hai",
        "style": "theme_5",
        "thumbnail_hook": "25 KE BAAD SALARY 10 TAREEKH KO KHATAM...",
        "thumbnail_badge": "MIDDLE CLASS REALITY",
        "scenes": [
            {
                "tts_voice": "पच्चीस की उम्र के बाद जब सैलरी दस तारीख को ही खत्म हो जाती है ना... तब असली ज़िंदगी समझ आती है।",
                "caption": "25 ki umar ke baad jab salary 10 tareekh ko hi khatam ho jaati hai na... tab asli zindagi samajh aati hai.",
                "highlight": "10 TAREEKH",
                "doc_tag": "REALITY",
                "emotion": "emotional",
                "wiki_query": "Delhi metro station commuters evening",
                "photo_prompt": "candid natural evening photograph of an ordinary young Indian man in office shirt with backpack waiting at a crowded Delhi metro platform, authentic warm station lights",
                "effect": "none"
            },
            {
                "tts_voice": "रेंट, ईएमआई, घर के खर्च... और दोस्तों के सामने मुस्कुराने की एक्टिंग सब एक साथ चलती है, हाहा!",
                "caption": "Rent, EMI, ghar ke kharch... aur doston ke saamne muskurane ki acting sab ek saath chalti hai!",
                "highlight": "MUSKURANE KI ACTING",
                "doc_tag": "PRESSURE",
                "emotion": "chuckle",
                "wiki_query": "Indian office worker desk evening",
                "photo_prompt": "natural candid photo of a young Indian man sitting at a simple rented room study table with a notebook and tea cup at night, warm desk lamp light",
                "effect": "none"
            },
            {
                "tts_voice": "घर वाले फोन पर पूछते हैं सब ठीक है ना... और हम खाली जेब के साथ कह देते हैं, हाँ माँ सब बढ़िया है।",
                "caption": "Ghar wale phone par poochte hain sab theek hai na... aur hum khaali jeb ke saath keh dete hain, haan maa sab badhiya hai.",
                "highlight": "KHAALI JEB",
                "doc_tag": "SILENCE",
                "emotion": "emotional",
                "wiki_query": "Indian man talking on phone balcony evening",
                "photo_prompt": "candid natural photograph of a young Indian man talking gently on his mobile phone on a small apartment terrace at twilight, warm city lights in distance",
                "effect": "none"
            },
            {
                "tts_voice": "इस उम्र में कोई हमारा हाल नहीं पूछता भाई... सिर्फ हमारी कमाई और हैसियत देखी जाती है।",
                "caption": "Is umar mein koi hamara haal nahi poochta bhai... sirf hamari kamai aur haisiyat dekhi jaati hai.",
                "highlight": "KAMAI AUR HAISIYAT",
                "doc_tag": "TRUTH",
                "emotion": "wise",
                "wiki_query": "Indian street evening traffic pedestrians",
                "photo_prompt": "authentic candid street photograph of an Indian man walking home along a busy neighborhood market road with warm yellow shop lights and auto-rickshaws",
                "effect": "none"
            },
            {
                "tts_voice": "पर यही वो दौर है... जो एक आम लड़के को अंदर से फौलाद बना देता है।",
                "caption": "Par yahi woh daur hai... jo ek aam ladke ko andar se faulad bana deta hai.",
                "highlight": "FAULAD",
                "doc_tag": "STRENGTH",
                "emotion": "wise",
                "wiki_query": "Indian rooftop morning sunrise tea",
                "photo_prompt": "natural warm morning photograph of an Indian young man standing on a house terrace holding a steel cup of tea watching soft golden sunrise over Indian rooftops",
                "effect": "none"
            },
            {
                "tts_voice": "अगर तुम भी इस दौर से गुज़र रहे हो... तो यह रील अपने उस जिगरी दोस्त को भेजो।",
                "caption": "Agar tum bhi is daur se guzar rahe ho... toh yeh reel apne us jigri dost ko bhejo.",
                "highlight": "JIGRI DOST",
                "doc_tag": "BROTHERHOOD",
                "emotion": "warm",
                "wiki_query": "Indian friends tea stall night",
                "photo_prompt": "candid warm photograph of two Indian friends sitting together at a local roadside tea stall at night talking and smiling, natural street light",
                "effect": "none"
            }
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

CRITICAL VOICE & NATURAL IMAGE RULES:
1. WISE HUMAN MENTOR TONE: Speak like a grounded, wise Indian storyteller having a heart-to-heart conversation ("अरे भाई...", "सच कहूँ दोस्त...", "याद रखना..."). Use natural pauses (`...`), subtle ironic chuckles/smiles where fitting ("हँसी आती है ये सोच कर...", "हाहा!"), and deep warmth.
2. NO ROBOTIC LISTICLES: Never say "Pehla point, doosra point". Tell a cohesive 6-beat real-life story or investigative reveal with a strong 2-second open-loop hook in Scene 1, an emotional/factual twist in Scene 3/4, and a natural DM-share trigger in Scene 6.
3. For EACH scene, return:
   - 'tts_voice': Pure natural Devanagari Hindi script with English words written phonetically in Devanagari (e.g. 'सैलरी', 'मेडिकल', 'ईएमआई', 'व्हाट्सएप') and natural pauses (`...`) so the voiceover sounds like a wise, warm, emotional human!
   - 'caption': The exact same spoken sentence in clean Roman Hinglish (with ₹ symbols and numbers) for minimal subtitles.
   - 'highlight': The 1-3 most powerful words from 'caption' (uppercase, MAX 20 chars) to highlight.
   - 'doc_tag': Tiny 1-2 word documentary/timestamp label (MAX 16 chars, e.g. 'DOC. #0412', 'Dusk, 6:14 PM', 'REALITY').
   - 'emotion': One of ["wise", "chuckle", "emotional", "shocked", "warm", "serious", "urgent"] controlling voice pitch, pacing, and expressive delivery!
   - 'wiki_query': Simple 3-4 word English search query for real Wikimedia Commons Indian photography (e.g. "Indian street market evening", "Indian rupee banknotes", "Delhi metro commuters").
   - 'photo_prompt': A 100% NATURAL, UNEDITED, REAL-WORLD smartphone/35mm candid photograph description set in everyday India (natural daylight or warm street lamps, ordinary middle-class Indian people/places, genuine expressions, natural skin tones). NEVER ask for cinematic teal-orange CGI, 3D renders, neon lights, studio lighting, or artificial AI perfection!
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
    """3-Tier Zero-Blank Natural Photo Engine: Pollinations Flux -> Wikimedia Real Indian Photos -> Picsum Stock."""
    os.makedirs("bg_assets", exist_ok=True)
    default_wiki_queries = [
        "India street market evening",
        "Indian rupee banknotes cash",
        "Mumbai local train commuters",
        "Indian roadside tea stall chai",
        "Indian office desk laptop",
        "pharmacy medicine tablets India"
    ]

    for idx, sc in enumerate(scenes_list):
        out_img = f"bg_assets/bg_{idx}.jpg"
        raw_prompt = sc.get("photo_prompt", "natural candid smartphone photo of an ordinary young Indian man in city evening, natural lighting")
        full_prompt = (
            f"{raw_prompt}, natural unedited real-life candid photograph, natural lighting, "
            f"authentic Indian environment, realistic skin texture, no artificial AI glow, no 3d render, no neon, no text"
        )
        encoded = urllib.parse.quote(full_prompt)
        seed = rng.randint(1000, 999999)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&model=flux&nologo=true&seed={seed}"

        downloaded = False
        # Tier 1: Pollinations Flux with polite delay so rate-limit never triggers
        for attempt in range(3):
            try:
                time.sleep(2.4 if idx > 0 else 0.5)
                r = requests.get(url, timeout=42)
                if r.status_code == 200 and len(r.content) > 25000:
                    with open(out_img, "wb") as f:
                        f.write(r.content)
                    downloaded = True
                    print(f"Scene {idx+1}/6: Natural Candid Photo Ready!")
                    break
            except Exception as e:
                print(f"Scene {idx+1} Pollinations retry {attempt+1}:", e)

        # Tier 2: Wikimedia Commons Real Documentary Photography (100% Real Photos, Zero API Key)
        if not downloaded:
            try:
                wq = sc.get("wiki_query") or default_wiki_queries[idx % len(default_wiki_queries)]
                q = urllib.parse.quote(wq)
                w_api = (
                    f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                    f"&gsrsearch=filetype:bitmap+{q}&gsrnamespace=6&gsrlimit=10"
                    f"&prop=imageinfo&iiprop=url&iiurlwidth=1080&format=json"
                )
                wr = requests.get(w_api, headers={"User-Agent": "SochBadloBot/2.0"}, timeout=20).json()
                pages = list(wr.get("query", {}).get("pages", {}).values())
                rng.shuffle(pages)
                for p in pages:
                    img_u = p.get("imageinfo", [{}])[0].get("thumburl") or p.get("imageinfo", [{}])[0].get("url")
                    if img_u and img_u.lower().endswith((".jpg", ".jpeg", ".png")):
                        ir = requests.get(img_u, headers={"User-Agent": "SochBadloBot/2.0"}, timeout=20)
                        if ir.status_code == 200 and len(ir.content) > 25000:
                            with open(out_img, "wb") as f:
                                f.write(ir.content)
                            downloaded = True
                            print(f"Scene {idx+1}/6: Real Wikimedia Documentary Photo Ready!")
                            break
            except Exception as e:
                print(f"Scene {idx+1} Wikimedia backup:", e)

        # Tier 3: Picsum Real Photography Backup (Guaranteed Non-Blank Image)
        if not downloaded:
            try:
                pr = requests.get(f"https://picsum.photos/seed/{seed}/1080/1920", timeout=20)
                if pr.status_code == 200 and len(pr.content) > 20000:
                    with open(out_img, "wb") as f:
                        f.write(pr.content)
                    downloaded = True
                    print(f"Scene {idx+1}/6: Real Stock Photo Backup Ready!")
            except Exception:
                pass

        if downloaded:
            im = Image.open(out_img).convert("RGB").resize((1080, 1920), Image.Resampling.LANCZOS)
            if style_name == "theme_1":
                # Natural warm editorial contrast (keeps real colors intact, not greyed out)
                im = ImageEnhance.Color(im).enhance(0.75)
                im = ImageEnhance.Contrast(im).enhance(1.12)
            elif style_name == "theme_3":
                # Warm natural Polaroid film look
                im = ImageEnhance.Color(im).enhance(0.95)
                im = ImageEnhance.Contrast(im).enhance(1.08)
            else:
                # Theme 5: Rich natural evening warmth (clear & bright enough to see every detail)
                im = ImageEnhance.Color(im).enhance(0.92)
                im = ImageEnhance.Contrast(im).enhance(1.10)
                im = ImageEnhance.Brightness(im).enhance(0.88)
            im.save(out_img, quality=94)
        else:
            # Textured dark warm charcoal fallback (never a blank white box)
            im = Image.new("RGB", (1080, 1920), (28, 24, 20))
            dr = ImageDraw.Draw(im)
            for _ in range(12000):
                gx = rng.randint(0, 1079)
                gy = rng.randint(0, 1919)
                delta = rng.randint(-8, 8)
                dr.point((gx, gy), fill=(28 + delta, 24 + delta, 20 + delta))
            im.save(out_img, quality=92)


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

    voice_id = "cgSgspJ2msm6clMCkdW9" if voice_style == "cute_viral" else "nPczCjzI2devNBz1zQrb"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": el_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}

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

print(f"V20.1 Natural Candid Photos + Wise Human Voice Engine Ready! ({round(current_time, 2)}s)")
