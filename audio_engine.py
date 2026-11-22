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
        "caption_topic": "Kisi Ka Bhi Jhooth 5 Second Mein Kaise Pakdein",
        "tts_topic": "किसी का भी झूठ 5 सेकंड में कैसे पकड़ें",
        "scenes": [
            {"tts_voice": "क्या आप जानते हैं किसी का भी झूठ सिर्फ 5 सेकंड में कैसे पकड़ा जा सकता है?", "caption": "Kya aap jaante hain kisi ka bhi jhooth sirf 5 second mein kaise pakda ja sakta hai?", "kicker": "LIE DETECTOR", "headline": "5-Second Lie Catch", "metric_big": "5 SEC", "metric_label": "MICRO CUE", "left_label": "Normal Baat", "right_label": "Eye Shift", "pct": 93},
            {"tts_voice": "पहला संकेत: झूठ बोलते वक्त इंसान या तो eye contact तोड़ता है या जरूरत से ज़्यादा घूरता है।", "caption": "Pehla sanket: jhooth bolte waqt insaan ya toh eye contact todta hai ya zaroorat se zyaada ghoorta hai.", "kicker": "CLUE 01", "headline": "Unnatural Eye Freeze", "metric_big": "78%", "metric_label": "EYE GIVEAWAY", "left_label": "Natural Blink", "right_label": "Forced Stare", "pct": 78},
            {"tts_voice": "दूसरा संकेत: सवाल पूछते ही अगर कोई जवाब से पहले बात दोहराए, तो दिमाग कहानी बना रहा है।", "caption": "Doosra sanket: sawaal poochte hi agar koi jawaab se pehle baat dohraaye, toh dimaag kahaani bana raha hai.", "kicker": "CLUE 02", "headline": "Question Repeat Delay", "metric_big": "2.4X", "metric_label": "RESPONSE DELAY", "left_label": "Direct Answer", "right_label": "Time Buying", "pct": 89},
            {"tts_voice": "तीसरा संकेत: झूठ बोलने वाला इंसान अक्सर अपने चेहरे, गर्दन या नाक को बार-बार छूने लगता है।", "caption": "Teesra sanket: jhooth bolne wala insaan aksar apne chehre, gardan ya naak ko baar-baar chhoone lagta hai.", "kicker": "CLUE 03", "headline": "Face & Neck Touch", "metric_big": "91%", "metric_label": "STRESS SIGNAL", "left_label": "Open Hands", "right_label": "Self Touch", "pct": 91},
            {"tts_voice": "चौथा संकेत: कहानी को उल्टे क्रम में पूछें, सच्चा इंसान बता देगा पर झूठा अटक जाएगा।", "caption": "Chautha sanket: kahaani ko ulte kram mein poochein, sachcha insaan bata dega par jhootha atak jaayega.", "kicker": "PRO TRICK", "headline": "Reverse Story Test", "metric_big": "100%", "metric_label": "FBI INTERROGATION", "left_label": "Forward Script", "right_label": "Reverse Check", "pct": 96},
            {"tts_voice": "यह psychology trick काम की लगी हो, तो reel को अभी save करके दोस्त को share करें!", "caption": "Yeh psychology trick kaam ki lagi ho, toh reel ko abhi save karke dost ko share karein!", "kicker": "SAVE NOW", "headline": "Never Get Fooled", "metric_big": "SAVE", "metric_label": "SMART MINDSET", "left_label": "Blind Trust", "right_label": "Sharp Eye", "pct": 98}
        ]
    },
    {
        "caption_topic": "Chup Rehne Ki Power: Kam Bolkar Respect Kaise Badhayein",
        "tts_topic": "चुप रहने की पावर: कम बोलकर रेस्पेक्ट कैसे बढ़ाएं",
        "scenes": [
            {"tts_voice": "कम बोलने वाले लोग हर room में सबसे ज़्यादा powerful और mysterious क्यों लगते हैं?", "caption": "Kam bolne wale log har room mein sabse zyaada powerful aur mysterious kyun lagte hain?", "kicker": "SILENT POWER", "headline": "Power Of Silence", "metric_big": "3X", "metric_label": "INSTANT AUTHORITY", "left_label": "Over Explaining", "right_label": "Calm Silence", "pct": 94},
            {"tts_voice": "पहला नियम: जब कोई आपको provoke करे, तो 3 सेकंड चुप रहकर सिर्फ हल्की सी smile दें।", "caption": "Pehla niyam: jab koi aapko provoke kare, toh 3 second chup rehkar sirf halki si smile dein.", "kicker": "RULE 01", "headline": "3-Second Silent Smile", "metric_big": "3 SEC", "metric_label": "EMOTIONAL CONTROL", "left_label": "Gussa & React", "right_label": "Silent Smile", "pct": 90},
            {"tts_voice": "दूसरा नियम: negotiation में अपनी बात बोलने के बाद सबसे पहले चुप रहना सीखें।", "caption": "Doosra niyam: negotiation mein apni baat bolne ke baad sabse pehle chup rehna seekhein.", "kicker": "RULE 02", "headline": "Negotiation Pause", "metric_big": "85%", "metric_label": "DEAL ADVANTAGE", "left_label": "Faltu Safai", "right_label": "Hold Silence", "pct": 85},
            {"tts_voice": "तीसरा नियम: अपने अगले plans किसी को मत बताओ, सीधा result से लोगों को चौंका दो।", "caption": "Teesra niyam: apne agle plans kisi ko mat batao, seedha result se logon ko chaunka do.", "kicker": "RULE 03", "headline": "Move In Silence", "metric_big": "10X", "metric_label": "EXECUTION FOCUS", "left_label": "Loud Announcements", "right_label": "Silent Results", "pct": 95},
            {"tts_voice": "याद रखो, जो इंसान हर जगह बोलता है उसकी बातों की कीमत अपने आप कम हो जाती है।", "caption": "Yaad rakho, jo insaan har jagah bolta hai uski baaton ki keemat apne aap kam ho jaati hai.", "kicker": "CORE TRUTH", "headline": "Scarcity Creates Value", "metric_big": "92%", "metric_label": "HIGH RESPECT", "left_label": "Cheap Words", "right_label": "Rare Gems", "pct": 92},
            {"tts_voice": "आज से ही कम बोलना शुरू करें और इस reel को save करके अपने status पर लगाएं!", "caption": "Aaj se hi kam bolna shuru karein aur iss reel ko save karke apne status par lagaayein!", "kicker": "APPLY TODAY", "headline": "Master Your Words", "metric_big": "SAVE", "metric_label": "DAILY RULE", "left_label": "React Fast", "right_label": "Stay Calm", "pct": 97}
        ]
    },
    {
        "caption_topic": "Warren Buffett Ka 5-25 Rule Jo Aapka Focus Badal Dega",
        "tts_topic": "वॉरेन बफेट का 5 टू 25 रूल जो आपका फोकस बदल देगा",
        "scenes": [
            {"tts_voice": "दुनिया के सबसे अमीर investor Warren Buffett का 5 to 25 rule आपकी life बदल सकता है!", "caption": "Duniya ke sabse ameer investor Warren Buffett ka 5-25 rule aapki life badal sakta hai!", "kicker": "BUFFETT SECRET", "headline": "The 5-25 Focus Rule", "metric_big": "5/25", "metric_label": "LASER PRIORITY", "left_label": "25 Goals", "right_label": "Top 5 Only", "pct": 95},
            {"tts_voice": "स्टेप वन: एक कागज़ पर अपनी जिंदगी के 25 सबसे बड़े goals को जल्दी से लिख डालिए।", "caption": "Step 1: ek kaagaz par apni zindagi ke 25 sabse bade goals ko jaldi se likh daaliye.", "kicker": "STEP 01", "headline": "List Your Top 25", "metric_big": "25", "metric_label": "LIFE GOALS", "left_label": "Dimag Mein Confusion", "right_label": "Paper Clarity", "pct": 88},
            {"tts_voice": "स्टेप टू: अब उनमें से सिर्फ 5 सबसे ज़रूरी goals को circle करें जो सच में मायने रखते हैं।", "caption": "Step 2: ab unmein se sirf 5 sabse zaroori goals ko circle karein jo sach mein maayne rakhte hain.", "kicker": "STEP 02", "headline": "Circle Only Top 5", "metric_big": "TOP 5", "metric_label": "CORE MISSION", "left_label": "Sab Kuch Karna", "right_label": "Sirf Top 5", "pct": 94},
            {"tts_voice": "सबसे बड़ा twist: बाकी बचे 20 goals को अपनी avoid list में डालकर पूरी तरह भूल जाइए!", "caption": "Sabse bada twist: baaki bache 20 goals ko apni avoid list mein daalkar poori tarah bhool jaaiye!", "kicker": "THE TWIST", "headline": "Avoid The Other 20", "metric_big": "ZERO", "metric_label": "DISTRACTION ZONE", "left_label": "Part-Time Focus", "right_label": "Total Cut-Off", "pct": 96},
            {"tts_voice": "क्योंकि यही 20 goals आपके top 5 सपनों का सबसे कीमती वक्त और energy चुराते हैं।", "caption": "Kyunki yahi 20 goals aapke top 5 sapnon ka sabse keemti waqt aur energy churaate hain.", "kicker": "WHY IT WORKS", "headline": "Kill Silent Thieves", "metric_big": "4X", "metric_label": "FASTER SUCCESS", "left_label": "Scattered Energy", "right_label": "100% Depth", "pct": 93},
            {"tts_voice": "अभी अपने top 5 goals लिखें और इस reel को save करके दोस्त को ज़रूर भेजें!", "caption": "Abhi apne top 5 goals likhein aur iss reel ko save karke dost ko zaroor bhejein!", "kicker": "TAKE ACTION", "headline": "Start Today", "metric_big": "SAVE", "metric_label": "FOCUS BLUEPRINT", "left_label": "Busy All Day", "right_label": "Truly Productive", "pct": 99}
        ]
    },
    {
        "caption_topic": "Overthinking Ko 60 Second Mein Rokne Ki Military Trick",
        "tts_topic": "ओवरथिंकिंग को 60 सेकंड में रोकने की मिलिट्री ट्रिक",
        "scenes": [
            {"tts_voice": "रात को सोते वक्त दिमाग में विचारों का तूफान चलता है? यह Navy SEAL trick try करो!", "caption": "Raat ko sote waqt dimaag mein vichaaron ka toofan chalta hai? Yeh Navy SEAL trick try karo!", "kicker": "MIND RESET", "headline": "60-Sec Brain Stop", "metric_big": "60S", "metric_label": "INSTANT CALM", "left_label": "Racing Thoughts", "right_label": "Box Breathing", "pct": 94},
            {"tts_voice": "स्टेप वन: 4 सेकंड तक नाक से गहरी सांस अंदर लें और पेट को पूरी तरह फूलने दें।", "caption": "Step 1: 4 second tak naak se gehri saans andar lein aur pet ko poori tarah phoolne dein.", "kicker": "PHASE 01", "headline": "4-Second Inhale", "metric_big": "4 SEC", "metric_label": "OXYGEN SURGE", "left_label": "Shallow Breath", "right_label": "Deep Inhale", "pct": 87},
            {"tts_voice": "स्टेप टू: अब 4 सेकंड तक सांस को अंदर रोकें, इससे heart rate तुरंत slow होने लगती है।", "caption": "Step 2: ab 4 second tak saans ko andar rokein, isse heart rate turant slow hone lagti hai.", "kicker": "PHASE 02", "headline": "4-Second Hold", "metric_big": "HOLD", "metric_label": "HEART RATE DROP", "left_label": "Panic Mode", "right_label": "Vagus Reset", "pct": 91},
            {"tts_voice": "स्टेप थ्री: 4 सेकंड में मुंह से सांस बाहर छोड़ें और फिर 4 सेकंड खाली रुकें।", "caption": "Step 3: 4 second mein munh se saans baahar chhodein aur phir 4 second khaali rukein.", "kicker": "PHASE 03", "headline": "Exhale & Pause", "metric_big": "4X4", "metric_label": "COMBAT CYCLE", "left_label": "Stress Loop", "right_label": "Calm System", "pct": 95},
            {"tts_voice": "सिर्फ 4 बार यह cycle दोहराने से आपका nervous system stress से निकलकर शांत हो जाता है।", "caption": "Sirf 4 baar yeh cycle dohraane se aapka nervous system stress se nikalkar shaant ho jaata hai.", "kicker": "SCIENTIFIC PROOF", "headline": "Nervous System Calm", "metric_big": "89%", "metric_label": "STRESS REDUCTION", "left_label": "Overthinking", "right_label": "Deep Sleep", "pct": 89},
            {"tts_voice": "इस reel को save कर लें ताकि अगली बार overthinking होते ही यह काम आए!", "caption": "Iss reel ko save kar lein taaki agli baar overthinking hote hi yeh kaam aaye!", "kicker": "SAVE THIS", "headline": "Peace In 60 Sec", "metric_big": "SAVE", "metric_label": "MENTAL HACK", "left_label": "Sleepless Night", "right_label": "Instant Peace", "pct": 98}
        ]
    },
    {
        "caption_topic": "Ameer Log Salary Aate Hi Sabse Pehle Kya Karte Hain",
        "tts_topic": "अमीर लोग सैलरी आते ही सबसे पहले क्या करते हैं",
        "scenes": [
            {"tts_voice": "90% लोग salary आते ही खर्च करते हैं, लेकिन अमीर लोग पहले 10 मिनट में यह करते हैं!", "caption": "90% log salary aate hi kharch karte hain, lekin ameer log pehle 10 minute mein yeh karte hain!", "kicker": "WEALTH SECRET", "headline": "First 10-Min Rule", "metric_big": "90%", "metric_label": "MIDDLE CLASS TRAP", "left_label": "Spend First", "right_label": "Invest First", "pct": 90},
            {"tts_voice": "पहला कदम: salary credit होते ही कम से कम 20% हिस्सा auto-debit से SIP में चला जाता है।", "caption": "Pehla kadam: salary credit hote hi kam se kam 20% hissa auto-debit se SIP mein chala jaata hai.", "kicker": "STEP 01", "headline": "Pay Yourself First", "metric_big": "20%", "metric_label": "AUTO INVESTMENT", "left_label": "End Month Bachat", "right_label": "Day-1 Auto SIP", "pct": 94},
            {"tts_voice": "दूसरा कदम: बाकी पैसे को 50% needs और 30% wants के अलग-अलग bank accounts में बांट देते हैं।", "caption": "Doosra kadam: baaki paise ko 50% needs aur 30% wants ke alag-alag bank accounts mein baant dete hain.", "kicker": "STEP 02", "headline": "The 50-30-20 Split", "metric_big": "50/30", "metric_label": "SMART BUCKETS", "left_label": "Ek Hi Account", "right_label": "3 Clean Buckets", "pct": 88},
            {"tts_voice": "तीसरा कदम: वे कभी भी EMI पर depreciating gadget या दिखावे की चीज़ें नहीं खरीदते।", "caption": "Teesra kadam: ve kabhi bhi EMI par depreciating gadget ya dikhaave ki cheezein nahi khareedte.", "kicker": "STEP 03", "headline": "Zero Bad EMI Rule", "metric_big": "0% EMI", "metric_label": "NO DEBT TRAP", "left_label": "Phone On EMI", "right_label": "Asset Building", "pct": 96},
            {"tts_voice": "यही छोटा सा automation 10 साल में एक साधारण salary को करोड़ों के corpus में बदल देता है।", "caption": "Yahi chhota sa automation 10 saal mein ek saadharan salary ko karodon ke corpus mein badal deta hai.", "kicker": "COMPOUNDING", "headline": "10-Year Wealth Engine", "metric_big": "10X", "metric_label": "COMPOUND GROWTH", "left_label": "Zero Savings", "right_label": "Crore Corpus", "pct": 97},
            {"tts_voice": "अगली salary आने से पहले इस reel को save करें और दोस्तों के साथ share करें!", "caption": "Agli salary aane se pehle iss reel ko save karein aur doston ke saath share karein!", "kicker": "SHARE WEALTH", "headline": "Automate Today", "metric_big": "SAVE", "metric_label": "MONEY FORMULA", "left_label": "Broke By 20th", "right_label": "Rich Every Month", "pct": 99}
        ]
    },
    {
        "caption_topic": "Subah 5 Baje Uthne Ka 21-Day Dopamine Formula",
        "tts_topic": "सुबह 5 बजे उठने का 21 डे डोपामिन फॉर्मूला",
        "scenes": [
            {"tts_voice": "अलार्म बंद करके बार-बार सो जाते हो? यह 3-step formula आपको बिना आलस 5 बजे उठा देगा!", "caption": "Alarm band karke baar-baar so jaate ho? Yeh 3-step formula aapko bina aalas 5 baje utha dega!", "kicker": "MORNING HACK", "headline": "5 AM Brain Switch", "metric_big": "5 AM", "metric_label": "ZERO SNOOZE", "left_label": "Snooze Loop", "right_label": "Instant Wake", "pct": 95},
            {"tts_voice": "पहला नियम: अपना फोन बिस्तर से कम से कम 10 कदम दूर रखो ताकि उठकर चलना पड़े।", "caption": "Pehla niyam: apna phone bistar se kam se kam 10 kadam door rakho taaki uthkar chalna pade.", "kicker": "STEP 01", "headline": "10-Step Phone Rule", "metric_big": "10 FT", "metric_label": "FORCED MOVEMENT", "left_label": "Phone In Bed", "right_label": "Across Room", "pct": 92},
            {"tts_voice": "दूसरा नियम: आंख खुलते ही 1 गिलास पानी पियो, इससे सोया हुआ दिमाग 90 सेकंड में active होता है।", "caption": "Doosra niyam: aankh khulte hi 1 gilaas paani piyo, isse soya hua dimaag 90 second mein active hota hai.", "kicker": "STEP 02", "headline": "90-Sec Water Trigger", "metric_big": "90S", "metric_label": "BRAIN HYDRATION", "left_label": "Groggy Mind", "right_label": "Sharp Focus", "pct": 89},
            {"tts_voice": "तीसरा नियम: उठने के पहले 10 मिनट बाहर की रोशनी में जाओ, cortisol तुरंत energy देगा।", "caption": "Teesra niyam: uthne ke pehle 10 minute baahar ki roshni mein jaao, cortisol turant energy dega.", "kicker": "STEP 03", "headline": "Morning Sunlight Hit", "metric_big": "10 MIN", "metric_label": "NATURAL DOPAMINE", "left_label": "Dark Room", "right_label": "Daylight Boost", "pct": 94},
            {"tts_voice": "सिर्फ 21 दिन यह करने से आपकी body clock अपने आप 4:55 पर आंख खोल देगी।", "caption": "Sirf 21 din yeh karne se aapki body clock apne aap 4:55 par aankh khol degi.", "kicker": "21-DAY HABIT", "headline": "Auto Body Clock", "metric_big": "21D", "metric_label": "PERMANENT HABIT", "left_label": "Late Mornings", "right_label": "5 AM Club", "pct": 96},
            {"tts_voice": "कल सुबह से इसे आज़माएं और इस reel को save करके दोस्त को challenge करें!", "caption": "Kal subah se isse aazmaayein aur iss reel ko save karke dost ko challenge karein!", "kicker": "CHALLENGE", "headline": "Win Your Morning", "metric_big": "SAVE", "metric_label": "DISCIPLINE MODE", "left_label": "Lazy Start", "right_label": "Unstoppable Day", "pct": 98}
        ]
    },
    {
        "caption_topic": "Dark Psychology: Log Aapko Halkay Mein Kyun Lete Hain",
        "tts_topic": "डार्क साइकोलॉजी: लोग आपको हल्के में क्यों लेते हैं",
        "scenes": [
            {"tts_voice": "अच्छे होने के बावजूद लोग आपकी value नहीं करते? यह 3 गलतियां आज ही बंद करो!", "caption": "Achhe hone ke baawajood log aapki value nahi karte? Yeh 3 galtiyan aaj hi band karo!", "kicker": "DARK PSYCHOLOGY", "headline": "Stop Being Taken Lightly", "metric_big": "3X", "metric_label": "INSTANT VALUE", "left_label": "Always Available", "right_label": "High Standard", "pct": 94},
            {"tts_voice": "गलती नंबर 1: हर किसी के message का 2 सेकंड में reply देकर खुद को हमेशा free दिखाना।", "caption": "Galti number 1: har kisi ke message ka 2 second mein reply dekar khud ko hamesha free dikhana.", "kicker": "MISTAKE 01", "headline": "24/7 Availability Trap", "metric_big": "82%", "metric_label": "VALUE DROP", "left_label": "Instant Reply", "right_label": "Busy Priority", "pct": 82},
            {"tts_voice": "गलती नंबर 2: बिना गलती के भी हर बात पर sorry बोलना और अपनी सीमाएं तय न करना।", "caption": "Galti number 2: bina galti ke bhi har baat par sorry bolna aur apni seemaayein tay na karna.", "kicker": "MISTAKE 02", "headline": "Over-Apologizing Habit", "metric_big": "ZERO", "metric_label": "WEAK BOUNDARIES", "left_label": "Sorry For Everything", "right_label": "Clear Standards", "pct": 90},
            {"tts_voice": "गलती नंबर 3: जो लोग आपकी disrespect करते हैं उन्हें बार-बार दूसरा मौका देते रहना।", "caption": "Galti number 3: jo log aapki disrespect karte hain unhe baar-baar doosra mauka dete rehna.", "kicker": "MISTAKE 03", "headline": "Tolerating Disrespect", "metric_big": "100%", "metric_label": "SELF RESPECT RULE", "left_label": "Free Second Chance", "right_label": "Walk Away", "pct": 95},
            {"tts_voice": "जिस दिन आप ना कहना सीख जाएंगे, उसी दिन से लोग आपकी असली कीमत समझेंगे।", "caption": "Jis din aap naa kehna seekh jaayenge, usi din se log aapki asli keemat samjhenge.", "kicker": "GOLDEN LAW", "headline": "Power Of Saying No", "metric_big": "93%", "metric_label": "RESPECT SHIFT", "left_label": "People Pleaser", "right_label": "Respected Leader", "pct": 93},
            {"tts_voice": "अपनी self-respect के लिए यह reel save करें और status par zaroor lagayein!", "caption": "Apni self-respect ke liye yeh reel save karein aur status par zaroor lagaayein!", "kicker": "SAVE & SHARE", "headline": "Know Your Worth", "metric_big": "SAVE", "metric_label": "MINDSET UPGRADE", "left_label": "Cheap Attention", "right_label": "High Value", "pct": 98}
        ]
    },
    {
        "caption_topic": "2-Minute Rule Jo Aapka Procrastination Khatam Kar Dega",
        "tts_topic": "2 मिनट रूल जो आपका प्रोक्रेस्टिनेशन खत्म कर देगा",
        "scenes": [
            {"tts_voice": "काम को कल पर टालने की आदत से परेशान हैं? Atomic Habits का 2-minute rule अपनाओ!", "caption": "Kaam ko kal par taalane ki aadat se pareshaan hain? Atomic Habits ka 2-minute rule apnaao!", "kicker": "ANTI-LAZY", "headline": "The 2-Minute Rule", "metric_big": "2 MIN", "metric_label": "ACTION TRIGGER", "left_label": "Kal Karunga", "right_label": "Start In 2 Min", "pct": 95},
            {"tts_voice": "नियम यह है कि किसी भी मुश्किल काम को सिर्फ 2 मिनट करने के लिए शुरू करो।", "caption": "Niyam yeh hai ki kisi bhi mushkil kaam ko sirf 2 minute karne ke liye shuru karo.", "kicker": "CORE RULE", "headline": "Just Start For 120 Sec", "metric_big": "120S", "metric_label": "FRICTION KILLER", "left_label": "Heavy Target", "right_label": "Tiny Start", "pct": 91},
            {"tts_voice": "किताब पढ़नी है? सिर्फ 1 पेज पढ़ो। Gym जाना है? सिर्फ जूते पहनकर बाहर निकलो।", "caption": "Kitaab padhni hai? Sirf 1 page padho. Gym jaana hai? Sirf joote pehenkar baahar niklo.", "kicker": "EXAMPLE", "headline": "Shrink The Habit", "metric_big": "1 PAGE", "metric_label": "ZERO RESISTANCE", "left_label": "2 Hours Plan", "right_label": "2-Minute Step", "pct": 88},
            {"tts_voice": "साइकोलॉजी कहती है एक बार काम शुरू होते ही दिमाग का resistance अपने आप खत्म हो जाता है।", "caption": "Psychology kehti hai ek baar kaam shuru hote hi dimaag ka resistance apne aap khatam ho jaata hai.", "kicker": "BRAIN SCIENCE", "headline": "Momentum Takes Over", "metric_big": "87%", "metric_label": "COMPLETION RATE", "left_label": "Overthinking", "right_label": "Flow State", "pct": 87},
            {"tts_voice": "90% मामलों में आप 2 मिनट के बाद भी उस काम को पूरा खत्म करके ही उठते हैं।", "caption": "90% maamlon mein aap 2 minute ke baad bhi uss kaam ko poora khatam karke hi uthte hain.", "kicker": "PROVEN RESULT", "headline": "Finish What You Start", "metric_big": "90%", "metric_label": "SUCCESS RATE", "left_label": "Pending List", "right_label": "Done & Dusted", "pct": 94},
            {"tts_voice": "अभी अपना सबसे जरूरी काम 2 मिनट के लिए शुरू करें और reel save कर लें!", "caption": "Abhi apna sabse zaroori kaam 2 minute ke liye shuru karein aur reel save kar lein!", "kicker": "DO IT NOW", "headline": "Beat Laziness Today", "metric_big": "SAVE", "metric_label": "PRODUCTIVITY HACK", "left_label": "Procrastinate", "right_label": "Execute Fast", "pct": 99}
        ]
    }
]

WHITE_PALETTES = [
    {"name": "apple_white_cobalt", "is_light": True, "bg": [248, 250, 253], "grid": [222, 232, 246], "card": [255, 255, 255], "card_border": [206, 220, 242], "text_main": [15, 23, 42], "text_muted": [92, 110, 136], "accent": [37, 99, 235], "secondary": [245, 158, 11], "positive": [16, 185, 129], "negative": [239, 68, 68]},
    {"name": "pure_paper_emerald", "is_light": True, "bg": [247, 252, 250], "grid": [216, 238, 230], "card": [255, 255, 255], "card_border": [198, 230, 218], "text_main": [14, 30, 26], "text_muted": [84, 115, 106], "accent": [5, 150, 105], "secondary": [217, 119, 6], "positive": [16, 185, 129], "negative": [225, 29, 72]},
    {"name": "swiss_grid_crimson", "is_light": True, "bg": [252, 250, 250], "grid": [238, 224, 228], "card": [255, 255, 255], "card_border": [232, 212, 218], "text_main": [24, 20, 24], "text_muted": [112, 102, 110], "accent": [225, 29, 72], "secondary": [37, 99, 235], "positive": [16, 185, 129], "negative": [220, 38, 38]},
    {"name": "studio_white_violet", "is_light": True, "bg": [249, 248, 254], "grid": [226, 222, 246], "card": [255, 255, 255], "card_border": [214, 208, 242], "text_main": [22, 18, 42], "text_muted": [102, 96, 134], "accent": [124, 58, 237], "secondary": [245, 158, 11], "positive": [16, 185, 129], "negative": [239, 68, 68]}
]

DARK_PALETTES = [
    {"name": "midnight_cyan_neon", "is_light": False, "bg": [8, 12, 24], "grid": [22, 34, 62], "card": [15, 23, 42], "card_border": [42, 68, 118], "text_main": [248, 250, 252], "text_muted": [148, 163, 184], "accent": [56, 189, 248], "secondary": [250, 204, 21], "positive": [52, 211, 153], "negative": [248, 113, 113]},
    {"name": "obsidian_amber_gold", "is_light": False, "bg": [12, 11, 16], "grid": [34, 30, 44], "card": [22, 20, 30], "card_border": [68, 58, 86], "text_main": [250, 250, 250], "text_muted": [161, 161, 170], "accent": [245, 158, 11], "secondary": [168, 85, 247], "positive": [52, 211, 153], "negative": [244, 63, 94]},
    {"name": "cyber_emerald_dark", "is_light": False, "bg": [7, 16, 15], "grid": [18, 44, 40], "card": [13, 28, 26], "card_border": [34, 78, 70], "text_main": [240, 253, 250], "text_muted": [140, 175, 168], "accent": [16, 185, 129], "secondary": [56, 189, 248], "positive": [52, 211, 153], "negative": [248, 113, 113]}
]

if theme_mode == "white_grid":
    chosen_palette = rng.choice(WHITE_PALETTES)
elif theme_mode == "dark_pro":
    chosen_palette = rng.choice(DARK_PALETTES)
else:
    chosen_palette = rng.choice(WHITE_PALETTES + DARK_PALETTES)

WIDGET_POOL = [
    "radar_scanner",
    "vs_clash_cards",
    "stock_line_graph",
    "animated_bar_chart",
    "floating_checklist",
    "circular_gauge",
    "typing_terminal_hud",
    "waveform_pulse_card",
    "split_duel_banner",
    "neon_orbit_rings",
    "step_pyramid_stack",
    "spotlight_stat_pill"
]
scene_widgets = rng.sample(WIDGET_POOL, 6)

edit_dna = {
    "palette": chosen_palette,
    "widgets": scene_widgets,
    "transition": rng.choice(["shutter_bars", "iris_reveal", "prism_wipe", "flash_zoom"])
}

used_history = load_used_topics()
unused_packs = [p for p in TOPIC_PACKS if p["caption_topic"].lower() not in [u.lower() for u in used_history]]
chosen_pack = rng.choice(unused_packs if unused_packs else TOPIC_PACKS)

CATEGORIES = [
    "Dark Psychology & Body Language Secrets",
    "Rich Mindset, Money Habits & Financial Discipline",
    "Stoic Philosophy & Emotional Control",
    "Brain Hacks, Focus & Anti-Procrastination",
    "Communication Mastery & High-Value Respect",
    "Dopamine Detox & Self-Discipline",
    "Life Lessons Most People Learn Too Late",
    "Negotiation & Persuasion Psychology"
]
chosen_category = rng.choice(CATEGORIES)

print(f"Theme: {chosen_palette['name']} | Category: {chosen_category} | Past Topics: {len(used_history)}")


def build_prompt(explicit_topic, past_topics, category_hint):
    avoid_block = ""
    if past_topics:
        recent_list = "\n".join(f"- {t}" for t in past_topics[-60:])
        avoid_block = f"""
STRICT ANTI-DUPLICATE RULE:
You MUST NOT repeat or closely resemble ANY of these previously used topics:
{recent_list}
"""

    topic_instruction = (
        f'Write the script specifically on this topic: "{explicit_topic}"'
        if explicit_topic
        else f'Invent ONE brand-new, ultra-viral, specific Hinglish Reel topic in the category "{category_hint}" that has NEVER been covered in the avoid list above.'
    )

    return f"""You are India's #1 viral Instagram Reel scriptwriter & motion graphics director for @sochbadlo.hq.
{topic_instruction}
{avoid_block}

Write an addictive, punchy, high-retention 6-scene Hinglish Reel script (strictly 24 to 30 seconds total -> 9 to 12 words per scene).

CRITICAL PRONUNCIATION & CONTENT RULES:
1. Scene 1 MUST be a shocking scroll-stopping hook. NEVER use generic intros like 'Hello friends' or 'Aaj hum baat karenge'.
2. Scenes 2, 3, 4, 5 MUST give concrete, actionable steps, real facts, or psychological tricks directly solving the topic!
3. For EACH scene, return TWO text fields:
   - 'tts_voice': Pure natural Devanagari Hindi script with English buzzwords written phonetically in Devanagari (e.g. write 'रूल' instead of 'rule', 'सेकंड' instead of 'second', 'फोकस' instead of 'focus', 'मेन' NEVER for 'में') so an English-trained TTS voice pronounces every single word with 100% crisp accuracy and zero weird accent!
   - 'caption': The exact same spoken sentence written in clean, easy Roman Hinglish for on-screen karaoke captions!
4. Also return compact motion-graphic UI strings per scene:
   - 'kicker': 2-3 word badge (MAX 18 chars)
   - 'headline': 3-4 word bold title (MAX 28 chars)
   - 'metric_big': Punchy 2-5 char hero stat (e.g. '5 SEC', '94%', 'TRAP', '3X', 'SAVE')
   - 'metric_label': Compact 2-word label (MAX 15 chars, e.g. 'INSTANT CALM', 'LASER FOCUS')
   - 'left_label': Short point A (MAX 15 chars)
   - 'right_label': Short point B (MAX 15 chars)
   - 'pct': Integer between 76 and 98

Return ONLY valid JSON with:
- "topic_title": Short unique Roman Hinglish title of this Reel (5-9 words)
- "ig_caption": Engaging 3-line Instagram caption with CTA to follow @sochbadlo.hq + 7 relevant hashtags
- "scenes": Array of 6 scene objects."""


def call_gemini_reliable(gemini_key, prompt):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0}
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
                    print(f"SUCCESS! Gemini API generated fresh unique script via {model_name}!")
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
    print(f"Using unused fallback pack: {fallback_title}")
    return {"scenes": chosen_pack["scenes"]}


def generate_grid_canvases(scenes_list):
    os.makedirs("bg_assets", exist_ok=True)
    pal = edit_dna["palette"]
    is_light = pal.get("is_light", True)
    bg_c = tuple(pal["bg"])
    grid_c = tuple(pal["grid"])
    ac = tuple(pal["accent"])
    sc_c = tuple(pal["secondary"])

    for idx in range(len(scenes_list)):
        out_img = f"bg_assets/bg_{idx}.jpg"
        base = Image.new("RGB", (1080, 1920), bg_c)
        gd = ImageDraw.Draw(base)

        w_bg = 0.85 if is_light else 0.72
        w_ac = 1.0 - w_bg
        orb1 = tuple(int(bg_c[i] * w_bg + ac[i] * w_ac) for i in range(3))
        orb2 = tuple(int(bg_c[i] * w_bg + sc_c[i] * w_ac) for i in range(3))
        gd.ellipse([rng.randint(-150, 250), rng.randint(-100, 300), rng.randint(650, 1050), rng.randint(650, 1050)], fill=orb1)
        gd.ellipse([rng.randint(150, 450), rng.randint(950, 1300), rng.randint(850, 1200), rng.randint(1650, 2000)], fill=orb2)
        im = base.filter(ImageFilter.GaussianBlur(130))
        dr = ImageDraw.Draw(im)

        step = 60
        for gx in range(0, 1080, step):
            w_line = 2 if gx % (step * 4) == 0 else 1
            dr.line([(gx, 0), (gx, 1920)], fill=grid_c, width=w_line)
        for gy in range(0, 1920, step):
            w_line = 2 if gy % (step * 4) == 0 else 1
            dr.line([(0, gy), (1080, gy)], fill=grid_c, width=w_line)

        plus_c = tuple(int(grid_c[i] * 0.78 + ac[i] * 0.22) for i in range(3))
        for gx in range(step * 4, 1080, step * 4):
            for gy in range(step * 4, 1920, step * 4):
                dr.line([(gx - 10, gy), (gx + 10, gy)], fill=plus_c, width=2)
                dr.line([(gx, gy - 10), (gx, gy + 10)], fill=plus_c, width=2)

        im.save(out_img, quality=95)
    print("Generated 6 Architectural Grid Canvases!")


script_obj = generate_ai_script()
scenes_data = script_obj["scenes"]
generate_grid_canvases(scenes_data)

sfx_bank_plan = [
    [{"type": "sub_boom", "offset": 0.02}, {"type": "rise", "offset": 0.08}, {"type": "pop", "offset": 0.55}, {"type": "whoosh", "offset": 2.1}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "impact", "offset": 0.55}, {"type": "pop", "offset": 1.15}, {"type": "ping", "offset": 2.0}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "ping", "offset": 0.65}, {"type": "pop", "offset": 1.45}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "impact", "offset": 0.70}, {"type": "ping", "offset": 1.80}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "pop", "offset": 0.45}, {"type": "ping", "offset": 1.10}, {"type": "pop", "offset": 1.85}],
    [{"type": "whoosh", "offset": 0.05}, {"type": "sub_boom", "offset": 0.85}, {"type": "ping", "offset": 1.95}]
]


def get_duration(file_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    return float(subprocess.check_output(cmd).decode().strip())


def generate_sfx_bank():
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.38:c=pink:a=0.52", "-af", "bandpass=f=900:width_type=h:w=1300,afade=t=in:ss=0:d=0.07,afade=t=out:st=0.14:d=0.24", "sfx_whoosh.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=820:d=0.11", "-af", "asetrate=44100*0.72,aresample=44100,afade=t=out:st=0.02:d=0.09,volume=0.65", "sfx_pop.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=82:d=0.40", "-af", "afade=t=out:st=0.04:d=0.36,volume=1.0", "sfx_impact.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=52:d=0.55", "-af", "afade=t=in:ss=0:d=0.02,afade=t=out:st=0.08:d=0.47,volume=1.1", "sfx_sub_boom.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=f=1318:d=0.24", "-af", "afade=t=in:ss=0:d=0.015,afade=t=out:st=0.04:d=0.20,volume=0.55", "sfx_ping.wav"], check=True)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=0.48:c=pink:a=0.34", "-af", "highpass=f=650,afade=t=in:ss=0:d=0.36,afade=t=out:st=0.36:d=0.12", "sfx_rise.wav"], check=True)


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
            "stability": 0.48,
            "similarity_boost": 0.78,
            "style": 0.35,
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
    rate = "+12%"
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
        print(f"SUCCESS! ElevenLabs Human Voice generated for Scene {idx+1}/6")
        af_str = "atempo=1.08,highpass=f=85,equalizer=f=190:width_type=h:width=120:g=2.5,equalizer=f=3600:width_type=h:width=1600:g=3.2,acompressor=threshold=-16dB:ratio=2.8:attack=5:release=50"
    else:
        print(f"Scene {idx+1}/6 using Edge-TTS fallback")
        run_edge_tts_fallback(tts_text, raw_v)
        af_str = "highpass=f=90,equalizer=f=220:width_type=h:width=120:g=3,equalizer=f=3400:width_type=h:width=1600:g=3.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50"

    subprocess.run(["ffmpeg", "-y", "-i", raw_v, "-af", af_str, v_file], check=True)

    dur = get_duration(v_file) + 0.12
    padded_v = f"padded_{idx}.wav"
    subprocess.run(["ffmpeg", "-y", "-i", v_file, "-af", f"apad=whole_dur={dur}", padded_v], check=True)
    voice_files.append(padded_v)

    timeline.append({
        "index": idx,
        "start": round(current_time, 3),
        "duration": round(dur, 3),
        "voice": cap_text,
        "kicker": sc.get("kicker", "INSIGHT")[:20],
        "headline": sc.get("headline", "")[:32],
        "metric_big": sc.get("metric_big", "95%")[:7],
        "metric_label": sc.get("metric_label", "PROVEN IMPACT")[:18],
        "left_label": sc.get("left_label", "Old Way")[:18],
        "right_label": sc.get("right_label", "Smart Way")[:18],
        "pct": int(sc.get("pct", 92)),
        "widget": scene_widgets[idx],
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

print(f"V16 Gemini-3.8 + Anti-Duplicate Studio Ready! ({round(current_time, 2)}s)")
