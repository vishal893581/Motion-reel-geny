import os
import sys
import time
import glob
import requests

IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
GRAPH_API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def find_latest_reel():
    mp4_files = glob.glob("**/*.mp4", recursive=True)
    if not mp4_files:
        raise FileNotFoundError("Koi bhi .mp4 Reel file nahi mili!")
    latest_video = max(mp4_files, key=os.path.getmtime)

    # Caption file check karo (agar generator ne banayi ho)
    base_name = os.path.splitext(latest_video)[0]
    caption = (
        "Apni soch badlo, zindagi khud badal jayegi! 🔥💡\n\n"
        "Roz aisi hi mind-shifting baatein aur life lessons ke liye follow karein 👉 @sochbadlo.hq\n\n"
        "#sochbadlo #mindset #hindimotivation #lifelessons #successmindset #selfimprovement #reelsindia"
    )
    for txt_candidate in [f"{base_name}.txt", "caption.txt", "output/caption.txt"]:
        if os.path.exists(txt_candidate):
            with open(txt_candidate, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if text:
                    caption = text
                    break

    return latest_video, caption


def upload_temp_video(video_path):
    print(f"Uploading {video_path} to temporary public host...")
    with open(video_path, "rb") as f:
        resp = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "1h"},
            files={"fileToUpload": (os.path.basename(video_path), f, "video/mp4")},
            timeout=120,
        )
    resp.raise_for_status()
    public_url = resp.text.strip()
    if not public_url.startswith("https://"):
        raise RuntimeError(f"Temp upload failed: {public_url}")
    print(f"Temporary Public URL ready: {public_url}")
    return public_url


def publish_reel(video_url, caption):
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        raise ValueError("IG_USER_ID ya IG_ACCESS_TOKEN missing hai!")

    # Step 1: Create Reel Media Container
    print("Creating Instagram Reel container...")
    create_resp = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    create_data = create_resp.json()
    if "id" not in create_data:
        raise RuntimeError(f"Container creation failed: {create_data}")

    creation_id = create_data["id"]
    print(f"Container ID: {creation_id} — Instagram processing shuru...")

    # Step 2: Wait until video processing is FINISHED
    for attempt in range(30):
        time.sleep(10)
        status_resp = requests.get(
            f"{BASE_URL}/{creation_id}",
            params={
                "fields": "status_code,status",
                "access_token": IG_ACCESS_TOKEN,
            },
            timeout=30,
        ).json()
        status_code = status_resp.get("status_code")
        print(f"[{attempt + 1}/30] Status: {status_code}")

        if status_code == "FINISHED":
            break
        if status_code == "ERROR":
            raise RuntimeError(f"Instagram video processing error: {status_resp}")
    else:
        raise TimeoutError("Instagram video processing 5 minute mein complete nahi hui.")

    # Step 3: Publish Reel to @sochbadlo.hq
    print("Publishing Reel to @sochbadlo.hq...")
    publish_resp = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    publish_data = publish_resp.json()
    if "id" not in publish_data:
        raise RuntimeError(f"Media publish failed: {publish_data}")

    print(f"SUCCESS! Reel live on @sochbadlo.hq! Media ID: {publish_data['id']}")


if __name__ == "__main__":
    try:
        video_file, reel_caption = find_latest_reel()
        temp_url = upload_temp_video(video_file)
        publish_reel(temp_url, reel_caption)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
