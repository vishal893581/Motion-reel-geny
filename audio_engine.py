import sys
import subprocess
import json
import os
import time
import re
import random
import urllib.parse
import requests

raw_topic = sys.argv[1].strip() if len(sys.argv) > 1 else ""
voice_style = sys.argv[2].strip() if len(sys.argv) > 2 else "cute_viral"

rng = random.SystemRandom()

TRENDING_VIRAL_TOPICS = [
    "Kisi Ka Bhi Jhooth 5 Second Mein Kaise Pakdein",
    "Chup Rehne Ki Power: Kam Bolkar Logon Ko Apna Deewana Kaise Banayein",
    "Ratan Tata Ka Woh Ek Rule Jo Har Middle Class Ko Sikhna Chahiye",
    "Ameer Log Apni Salary Aate Hi Sabse Pehle Kya Karte Hain",
    "Mobile Charging Ki Woh Galti Jo Aapke Phone Ko Andar Se Kharab Kar Rahi Hai",
    "Neend Na Aane Par Dimaag Ko 2 Minute Mein Shant Karne Ki Military Trick",
    "Dark Psychology: Pehli Mulakat Mein Kisi Ka Bhi Dil Kaise Jeetein",
    "Overthinking Ko 60 Second Mein Rokne Ki Navy SEAL Breathing Trick",
    "Duniya Ke Sabse Amir Log Subah Uthkar Yeh 2 Kaam Kabhi Nahi Karte",
    "Kisi Bhi Conversation Mein Samne Wale Ko Apni Baat Manwane Ki Trick",
    "Instagram Aur Reels Ki Lat Chhodne Ka Sabse Aasan 48-Hour Reset",
    "Aapka Phone Chupke Se Aapki Baatein Kaise Sunta Hai Aur Kaise Rokein",
    "Middle Class Trap: EMI Aur Credit Card Se Bachne Ka Real Formula",
    "Body Language Secret: Bina Bole Room Mein Sabse Confident Kaise Dikhein",
    "Warren Buffett Ka 5-25 Rule Jo Aapki Life Ka Focus Badal Dega",
    "Log Aapko For Granted Kyun Lete Hain Aur Isse Turant Kaise Badlein",
    "Dimaag Ki Memory Aur Focus Tez Karne Ki Japanese Kaizen Aadat",
    "Interview Ya Meeting Mein Pehle 7 Second Mein Impression Kaise Jamayein"
]

topic = raw_topic if raw_topic else rng.choice(TRENDING_VIRAL_TOPICS)
print(f"Selected Viral Topic: {topic}")

EDIT_PROFILES = [
    {
        "style_id": "cinematic_story",
        "name": "Dark Cinema Storytelling",
        "accent": [244, 63, 94],
        "highlight": [250, 204, 21],
        "bg_tint": [10, 12, 20],
        "
