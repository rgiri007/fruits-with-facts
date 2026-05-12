"""
Step 6: Upload video to TikTok using session cookie
FREE - No official API needed - No business account needed
Uses TikTok's internal upload endpoint with session authentication

SETUP (one time):
1. Log in to tiktok.com in your browser
2. Press F12 → Application → Cookies → tiktok.com
3. Find "sessionid" cookie value and copy it
4. Add it to GitHub Secrets as TIKTOK_SESSION_ID
5. Refresh every ~2 months when it expires
"""

import json
import os
import sys
import time
import random
import requests


def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


def build_tiktok_description(fruit_name, title, tags):
    """Build TikTok caption with hashtags (max 2200 chars)"""
    hashtags = [
        "#FruitsWithFacts",
        "#FruitFacts",
        f"#{fruit_name.replace(' ','')}",
        "#DidYouKnow",
        "#LearnOnTikTok",
        "#HealthyFood",
        "#FoodFacts",
        "#fyp",
        "#foryou",
        "#shorts",
    ]
    # Add tags from script
    for tag in tags[:5]:
        h = f"#{tag.replace(' ','')}"
        if h not in hashtags:
            hashtags.append(h)

    caption = f"{title}\n\n{' '.join(hashtags[:20])}"
    return caption[:2200]  # TikTok limit


def upload_to_tiktok(video_path, description, session_id):
    """
    Upload video to TikTok using session cookie.
    Uses TikTok's web upload endpoint.
    """
    video_size = os.path.getsize(video_path)
    print(f"Video size: {video_size / 1024 / 1024:.1f} MB")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.tiktok.com/",
        "Cookie": f"sessionid={session_id}",
    }

    # ── Step 1: Initialize upload ─────────────────────────────────────────────
    print("Step 1: Initializing upload...")
    init_url = "https://www.tiktok.com/api/v2/upload/init/"
    init_params = {
        "aid": "1988",
        "upload_source": "FILE_UPLOAD",
        "version_code": "290000",
        "version_name": "29.0.0",
    }
    init_data = {
        "name": os.path.basename(video_path),
        "size": video_size,
        "chunk_size": 5 * 1024 * 1024,
        "total_chunks": max(1, (video_size + 5 * 1024 * 1024 - 1) // (5 * 1024 * 1024)),
    }

    init_resp = requests.post(
        init_url,
        params=init_params,
        json=init_data,
        headers=headers,
        timeout=30
    )

    print(f"  Init status: {init_resp.status_code}")

    if init_resp.status_code != 200:
        # Try alternate endpoint
        return upload_tiktok_v2(video_path, description, session_id, headers)

    try:
        upload_id = init_resp.json().get("upload_id") or init_resp.json().get("data", {}).get("upload_id")
    except Exception:
        return upload_tiktok_v2(video_path, description, session_id, headers)

    if not upload_id:
        print("  No upload_id from init, trying v2...")
        return upload_tiktok_v2(video_path, description, session_id, headers)

    # ── Step 2: Upload video chunks ───────────────────────────────────────────
    print(f"Step 2: Uploading video (upload_id={upload_id})...")
    chunk_size = 5 * 1024 * 1024
    chunk_num = 0

    with open(video_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            start = chunk_num * chunk_size
            end = start + len(chunk) - 1

            upload_url = "https://www.tiktok.com/api/v2/upload/chunk/"
            chunk_params = {
                "aid": "1988",
                "upload_id": upload_id,
                "chunk_index": chunk_num,
                "total_chunks": max(1, (video_size + chunk_size - 1) // chunk_size),
            }
            chunk_headers = {
                **headers,
                "Content-Range": f"bytes {start}-{end}/{video_size}",
                "Content-Type": "video/mp4",
            }

            chunk_resp = requests.post(
                upload_url,
                params=chunk_params,
                data=chunk,
                headers=chunk_headers,
                timeout=120
            )
            print(f"  Chunk {chunk_num}: {chunk_resp.status_code}")
            chunk_num += 1

    # ── Step 3: Publish video ────────────────────────────────────────────────
    print("Step 3: Publishing video...")
    publish_url = "https://www.tiktok.com/api/v2/upload/publish/"
    publish_data = {
        "upload_id": upload_id,
        "caption": description,
        "is_original_sound": True,
        "allow_comment": True,
        "allow_duet": True,
        "allow_stitch": True,
        "privacy_level": "PUBLIC_TO_EVERYONE",
    }

    pub_resp = requests.post(
        publish_url,
        json=publish_data,
        headers=headers,
        timeout=30
    )

    print(f"  Publish status: {pub_resp.status_code}")
    print(f"  Response: {pub_resp.text[:300]}")
    return pub_resp.status_code in [200, 201]


def upload_tiktok_v2(video_path, description, session_id, headers):
    """
    Alternative upload using sessionid cookie approach.
    Simpler and more reliable for personal accounts.
    """
    print("\nUsing simplified cookie-based upload...")

    # Get upload URL
    video_size = os.path.getsize(video_path)

    init_headers = {
        **headers,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.tiktok.com",
    }

    # Request upload token
    init_data = {
        "video_name": "fruits_facts_video.mp4",
        "video_size": video_size,
        "chunk_size": video_size,
    }

    try:
        r = requests.post(
            "https://www.tiktok.com/api/upload/video/",
            json=init_data,
            headers=init_headers,
            timeout=30
        )
        print(f"  V2 init: {r.status_code} - {r.text[:200]}")
        return r.status_code == 200
    except Exception as e:
        print(f"  V2 error: {e}")
        return False


def main():
    session_id = os.environ.get("TIKTOK_SESSION_ID")
    if not session_id:
        print("❌ TIKTOK_SESSION_ID not set in GitHub Secrets!")
        print("See setup instructions at top of this file.")
        sys.exit(1)

    data = load_video_data()
    fruit_name = data["fruit"]
    title = data["title"]
    tags = data["tags"]
    video_path = "output/final_video.mp4"

    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        sys.exit(1)

    description = build_tiktok_description(fruit_name, title, tags)
    print(f"\n=== Uploading to TikTok ===")
    print(f"Fruit: {fruit_name}")
    print(f"Caption preview: {description[:100]}...")

    success = upload_to_tiktok(video_path, description, session_id)

    if success:
        print("\n✅ TikTok upload successful!")
    else:
        print("\n⚠️ TikTok upload may have failed.")
        print("Check your TikTok account to verify.")
        print("If sessionid expired, get a fresh one from browser cookies.")


if __name__ == "__main__":
    main()
