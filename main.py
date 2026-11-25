import sys
import subprocess

topic = sys.argv[1] if len(sys.argv) > 1 else ""
voice_style = sys.argv[2] if len(sys.argv) > 2 else "adam_ref"
theme_mode = sys.argv[3] if len(sys.argv) > 3 else "kinetic_16x9"

print(f"Starting @sochbadlo.hq V23 Pipeline | Topic: {topic or 'AUTO'}")
subprocess.run(["python3", "audio_engine.py", topic, voice_style, theme_mode], check=True)
subprocess.run(["python3", "render_video.py"], check=True)
print("Pipeline complete! Output saved to final_reel.mp4")
