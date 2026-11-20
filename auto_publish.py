import os
import sys
import time
import glob
import requests

IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
GRAPH_API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def find_latest_reel():
    mp4_files = glob.glob("**/*.mp4", recursive=True)
    if not mp4_files:
        raise FileNotFoundError("Koi bhi .mp4 Reel file nahi mili!")
    latest_video = max(mp4_files, key=os.path.getmtime)

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
    filename = os.path.basename(video_path)

    # Host 1: tmpfiles.org (Direct download URL via /dl/)
    try:
        print("Trying Host 1: tmpfiles.org...")
        with open(video_path, "rb") as f:
            resp = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": (filename, f, "video/mp4")},
                headers=HEADERS,
                timeout=120,
            )
        if resp.status_code == 200:
            data = resp.json()
            raw_url = data.get("data", {}).get("url", "")
            if "tmpfiles.org/" in raw_url:
                direct_url = raw_url.replace("http://", "https://").replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)
                print(f"Public URL ready (tmpfiles): {direct_url}")
                return direct_url
    except Exception as e:
        print(f"Host 1 failed: {e}")

    # Host 2: 0x0.st
    try:
        print("Trying Host 2: 0x0.st...")
        with open(video_path, "rb") as f:
            resp = requests.post(
                "https://0x0.st",
                files={"file": (filename, f, "video/mp4")},
                headers=HEADERS,
                timeout=120,
            )
        if resp.status_code == 200 and resp.text.strip().startswith("https://"):
            direct_url = resp.text.strip()
            print(f"Public URL ready (0x0.st): {direct_url}")
            return direct_url
    except Exception as e:
        print(f"Host 2 failed: {e}")

    # Host 3: catbox.moe with browser headers
    try:
        print("Trying Host 3: catbox.moe...")
        with open(video_path, "rb") as f:
            resp = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": (filename, f, "video/mp4")},
                headers=HEADERS,
                timeout=120,
            )
        if resp.status_code == 200 and resp.text.strip().startswith("https://"):
            direct_url = resp.text.strip()
            print(f"Public URL ready (catbox): {direct_url}")
            return direct_url
    except Exception as e:
        print(f"Host 3 failed: {e}")

    raise RuntimeError("Teeno temporary video hosts upload mein fail ho gaye!")


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
