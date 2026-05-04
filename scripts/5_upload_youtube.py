"""
Step 5: Upload video to YouTube using YouTube Data API v3 (Free)
Uploads video + thumbnail, sets title, description, tags, and hashtags
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

    print("YouTube access token obtained")
    return data["access_token"]


# ── Build final description with hashtags appended ───────────────────────────
def build_description(fruit_name, raw_description, tags):
    """
    YouTube shows hashtags from the description above the title.
    We append them at the end of description to ensure they appear.
    """
    # Clean description — remove any existing hashtag line to avoid duplicates
    lines = raw_description.strip().split("\n")
    clean_lines = [l for l in lines if not l.strip().startswith("#")]
    clean_desc = "\n".join(clean_lines).strip()

    # Build hashtag line from tags (max 15 hashtags, YouTube limit)
    hashtag_terms = [
        fruit_name.replace(" ", ""),
        "FruitsWithFacts",
        "FruitFacts",
        "HealthyFood",
        "DidYouKnow",
        "NutritionFacts",
        "FoodFacts",
        "HealthyEating",
        "FruitLovers",
        "Education",
    ]

    # Add tags as hashtags too (cleaned)
    for tag in tags[:5]:
        cleaned = tag.replace(" ", "").replace("-", "")
        if cleaned not in hashtag_terms:
            hashtag_terms.append(cleaned)

    hashtag_line = " ".join(f"#{t}" for t in hashtag_terms[:15])

    final_description = f"{clean_desc}\n\n{hashtag_line}"

    return final_description


# ── Upload video to YouTube ───────────────────────────────────────────────────
def upload_video(access_token, title, description, tags):
    video_path = "output/final_video.mp4"
    file_size  = os.path.getsize(video_path)

    print(f"Uploading: {title}")
    print(f"File size: {file_size / 1024 / 1024:.1f} MB")
    print(f"Tags: {tags}")
    print(f"Description preview: {description[:100]}...")

    metadata = {
        "snippet": {
            "title":           title,
            "description":     description,
            "tags":            tags,
            "categoryId":      "27",        # 27 = Education
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus":           "public",
            "selfDeclaredMadeForKids": False,
            "madeForKids":             False
        }
    }

    # Initialize resumable upload session
    init_response = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos"
        "?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization":           f"Bearer {access_token}",
            "Content-Type":            "application/json",
            "X-Upload-Content-Type":   "video/mp4",
            "X-Upload-Content-Length": str(file_size)
        },
        json=metadata
    )

    if init_response.status_code != 200:
        raise Exception(f"Upload init failed {init_response.status_code}: {init_response.text}")

    upload_url = init_response.headers["Location"]
    print("Upload session started")

    # Upload in 5MB chunks
    chunk_size = 5 * 1024 * 1024
    uploaded   = 0
    video_id   = None

    with open(video_path, "rb") as f:
        while uploaded < file_size:
            chunk = f.read(chunk_size)
            end   = uploaded + len(chunk) - 1

            response = requests.put(
                upload_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type":  "video/mp4",
                    "Content-Range": f"bytes {uploaded}-{end}/{file_size}"
                },
                data=chunk
            )

            if response.status_code in [200, 201]:
                video_id = response.json().get("id")
                print(f"\nUpload complete! Video ID: {video_id}")
                break
            elif response.status_code == 308:
                uploaded  = end + 1
                progress  = (uploaded / file_size) * 100
                print(f"\rUploading: {progress:.1f}%", end="", flush=True)
            else:
                raise Exception(
                    f"Upload failed at chunk: {response.status_code} {response.text[:300]}"
                )

    return video_id


# ── Upload thumbnail ──────────────────────────────────────────────────────────
def upload_thumbnail(access_token, video_id):
    thumbnail_path = "output/thumbnail.jpg"

    if not os.path.exists(thumbnail_path):
        print("No thumbnail found, skipping")
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
        print("Thumbnail uploaded successfully!")
    else:
        print(f"Thumbnail upload failed: {response.status_code} — {response.text[:200]}")


# ── Mark fruit as done ────────────────────────────────────────────────────────
def mark_fruit_done(fruit_name):
    with open("fruits_done.txt", "a") as f:
        f.write(f"{fruit_name}\n")
    print(f"Marked '{fruit_name}' as done")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data       = load_video_data()
    fruit_name = data["fruit"]
    title      = data["title"]
    tags       = data["tags"]

    # Build enriched description with hashtags properly appended
    description = build_description(
        fruit_name,
        data["description"],
        tags
    )

    print(f"\nUploading video for: {fruit_name}")
    print(f"Title: {title}")
    print(f"Tags count: {len(tags)}")

    access_token = get_access_token()

    video_id = upload_video(access_token, title, description, tags)

    if video_id:
        print(f"Video URL: https://www.youtube.com/watch?v={video_id}")
        time.sleep(5)
        upload_thumbnail(access_token, video_id)
        mark_fruit_done(fruit_name)
        print(f"\nSUCCESS! '{title}' is now live on YouTube!")
    else:
        raise Exception("Upload failed — no video ID returned")
