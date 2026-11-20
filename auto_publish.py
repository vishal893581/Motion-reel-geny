import os
import sys
import time
import glob
import base64
import requests

IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "").strip()
GRAPH_API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


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


def upload_to_github_release(video_path):
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        raise ValueError("GITHUB_TOKEN ya GITHUB_REPOSITORY missing hai!")

    gh_headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    tag_name = "temp-reel-host"

    # Purana temp release agar hai toh delete karo
    old_rel = requests.get(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/tags/{tag_name}", headers=gh_headers).json()
    if "id" in old_rel:
        requests.delete(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/{old_rel['id']}", headers=gh_headers)
    requests.delete(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/git/refs/tags/{tag_name}", headers=gh_headers)

    # Naya temporary release banao
    rel_resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases",
        headers=gh_headers,
        json={"tag_name": tag_name, "name": "Temp Reel Host", "draft": False, "prerelease": True},
        timeout=30,
    ).json()

    upload_url = rel_resp["upload_url"].split("{")[0]
    release_id = rel_resp["id"]
    asset_name = f"reel_{int(time.time())}.mp4"

    print("Uploading Reel to GitHub CDN...")
    with open(video_path, "rb") as f:
        asset_resp = requests.post(
            f"{upload_url}?name={asset_name}",
            headers={**gh_headers, "Content-Type": "video/mp4"},
            data=f,
            timeout=120,
        ).json()

    public_url = asset_resp["browser_download_url"]
    print(f"Direct GitHub CDN URL ready: {public_url}")
    return public_url, release_id, tag_name, gh_headers


def cleanup_github_release(release_id, tag_name, gh_headers):
    try:
        requests.delete(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/{release_id}", headers=gh_headers)
        requests.delete(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/git/refs/tags/{tag_name}", headers=gh_headers)
        print("Temporary GitHub release cleaned up.")
    except Exception:
        pass


def publish_reel(video_url, caption):
    if not IG_USER_ID or not IG_ACCESS_TOKEN:
        raise ValueError("IG_USER_ID ya IG_ACCESS_TOKEN missing hai!")

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
    ).json()

    if "id" not in create_resp:
        raise RuntimeError(f"Container creation failed: {create_resp}")

    creation_id = create_resp["id"]
    print(f"Container ID: {creation_id} — Instagram processing shuru...")

    for attempt in range(30):
        time.sleep(10)
        status_resp = requests.get(
            f"{BASE_URL}/{creation_id}",
            params={"fields": "status_code,status", "access_token": IG_ACCESS_TOKEN},
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

    print("Publishing Reel to @sochbadlo.hq...")
    publish_resp = requests.post(
        f"{BASE_URL}/{IG_USER_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": IG_ACCESS_TOKEN},
        timeout=60,
    ).json()

    if "id" not in publish_resp:
        raise RuntimeError(f"Media publish failed: {publish_resp}")

    print(f"SUCCESS! Reel live on @sochbadlo.hq! Media ID: {publish_resp['id']}")


if __name__ == "__main__":
    rel_id = None
    try:
        video_file, reel_caption = find_latest_reel()
        cdn_url, rel_id, tag, headers = upload_to_github_release(video_file)
        publish_reel(cdn_url, reel_caption)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if rel_id:
            cleanup_github_release(rel_id, tag, headers)
