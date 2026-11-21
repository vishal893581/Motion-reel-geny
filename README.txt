sochbadlo.hq Anti-Duplicate Automation Update
===========================================
Files included in this ZIP:
1. audio_engine.py -> Generates 100% unique topics using used_topics.txt history + dynamic Instagram captions.
2. .github/workflows/generate-reel.yml -> Fixed lowercase 'name:' schedule trigger + auto-commits used_topics.txt after every Reel.
3. used_topics.txt -> Tracks every published topic so no script ever repeats.

How to upload to GitHub:
- Extract this ZIP folder.
- Upload 'audio_engine.py' and 'used_topics.txt' to the root of your GitHub repository.
- Upload 'generate-reel.yml' inside '.github/workflows/' folder (or replace existing file).
