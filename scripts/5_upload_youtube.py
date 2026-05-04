"""
Step 5: Upload video to YouTube using YouTube Data API v3 (Free)
No watermarks. Requires one-time OAuth setup.
"""

import json
import os
import requests
import time


# ── Load video data ───────────────────────────────────────────────────────────
def load_video_data():
    with open("output/video_data.json", "r") as f:
        return json.load(f)


# ── Refresh YouTube access token ──────────────────────────────────────────────
def get_access_token():
    client_id     = os.environ["YOUTUBE_CLIENT_ID"]
    client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
    refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

    response = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token"
    })

    data = response.json()
    if "access_token" not in data:
        raise Exception(f"Failed to get access token: {data}")

    print("✅ YouTube access token obtained")
    return data["access_token"]


# ── Upload video to YouTube ───────────────────────────────────────────────────
def upload_video(access_token, title, description, tags):
    video_path = "output/final_video.mp4"
    file_size  = os.path.getsize(video_path)

    print(f"📤 Uploading: {title}")
    print(f"📦 File size: {file_size / 1024 / 1024:.1f} MB")

    # Step 1: Initialize resumable upload
    metadata = {
        "snippet": {
            "title":       title,
            "description": description,
            "tags":        tags,
            "categoryId":  "26",   # 26 = How-to & Style | 27 = Education
            "defaultLanguage": "en"
        },
        "status": {
            "privacyStatus":          "public",   # "public", "private", or "unlisted"
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False
        }
    }

    init_response = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization":       f"Bearer {access_token}",
            "Content-Type":        "application/json",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(file_size)
        },
        json=metadata
    )

    if init_response.status_code != 200:
        raise Exception(f"Upload init failed: {init_response.text}")

    upload_url = init_response.headers["Location"]
    print("✅ Upload session created")

    # Step 2: Upload video in chunks
    chunk_size = 5 * 1024 * 1024  # 5MB chunks
    uploaded = 0
    video_id = None

    with open(video_path, "rb") as f:
        while uploaded < file_size:
            chunk = f.read(chunk_size)
            end = uploaded + len(chunk) - 1

            response = requests.put(
                upload_url,
                headers={
                    "Authorization":  f"Bearer {access_token}",
                    "Content-Type":   "video/mp4",
                    "Content-Range":  f"bytes {uploaded}-{end}/{file_size}"
                },
                data=chunk
            )

            if response.status_code in [200, 201]:
                video_id = response.json().get("id")
                print(f"\n✅ Upload complete!")
                break
            elif response.status_code == 308:
                # Chunk accepted, continue
                uploaded = end + 1
                progress = (uploaded / file_size) * 100
                print(f"\r📤 Upload progress: {progress:.1f}%", end="", flush=True)
            else:
                raise Exception(f"Upload chunk failed: {response.status_code} {response.text}")

    return video_id


# ── Upload thumbnail ──────────────────────────────────────────────────────────
def upload_thumbnail(access_token, video_id):
    thumbnail_path = "output/thumbnail.jpg"

    if not os.path.exists(thumbnail_path):
        print("⚠️ No thumbnail found, skipping")
        return

    with open(thumbnail_path, "rb") as f:
        response = requests.post(
            f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
            f"?videoId={video_id}&uploadType=media",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "image/jpeg"
            },
            data=f.read()
        )

    if response.status_code == 200:
        print("✅ Thumbnail uploaded!")
    else:
        print(f"⚠️ Thumbnail upload failed: {response.status_code} - {response.text[:200]}")


# ── Mark fruit as done ────────────────────────────────────────────────────────
def mark_fruit_done(fruit_name):
    with open("fruits_done.txt", "a") as f:
        f.write(f"{fruit_name}\n")
    print(f"✅ Marked '{fruit_name}' as done in fruits_done.txt")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data        = load_video_data()
    fruit_name  = data["fruit"]
    title       = data["title"]
    description = data["description"]
    tags        = data["tags"]

    print(f"\n🍎 Uploading video for: {fruit_name}")
    print(f"📋 Title: {title}")

    # Get access token
    access_token = get_access_token()

    # Upload video
    video_id = upload_video(access_token, title, description, tags)

    if video_id:
        print(f"🎉 Video ID: {video_id}")
        print(f"🔗 URL: https://www.youtube.com/watch?v={video_id}")

        # Upload thumbnail
        time.sleep(5)  # Wait for video to process
        upload_thumbnail(access_token, video_id)

        # Mark as done
        mark_fruit_done(fruit_name)

        print(f"\n✅ SUCCESS! '{title}' is now live on YouTube!")
    else:
        raise Exception("Upload failed - no video ID returned")
