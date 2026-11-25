====================================================
SOCHBADLO.HQ — V20 HUMAN STORYTELLING REEL ENGINE
====================================================

1. INCLUDED FILES:
   - audio_engine.py   : Wise Indian human mentor voiceover (chuckle, warm, emotional, wise prosody) + Gemini unique topic generator + 35mm candid photo fetcher.
   - render_video.py   : 3 completely distinct human-edited styles (no AI charts/boxes):
       * theme_1 : Newspaper Documentary Cutout (#F3EFE6 Ivory Paper + Orange Text + Yellow Highlighter + Red Circle)
       * theme_3 : Charcoal Slate & Coral Red (#161618 Matte Dark + Tilted Polaroid + Warm Cream & Coral Red Underline)
       * theme_5 : Espresso Brown & Burnt Orange (#18120E Deep Espresso + 35mm Candid Film + Warm Sand & Burnt Orange)
   - main.py           : Master runner script.
   - requirements.txt  : Python dependencies.
   - .github/workflows/reel_pipeline.yml : Automated GitHub Actions workflow.

2. HOW TO UPDATE YOUR GITHUB REPO:
   - Extract this ZIP folder.
   - Upload/replace audio_engine.py, render_video.py, main.py, requirements.txt, and .github/workflows/reel_pipeline.yml in your repository.
   - Ensure GEMINI_API_KEY (and optional ELEVENLABS_API_KEY) are set in GitHub Repo -> Settings -> Secrets and variables -> Actions.
