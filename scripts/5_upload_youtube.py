#!/usr/bin/env python3
"""
Script 5: Upload to YouTube
Uses YouTube API to upload and schedule video
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """Authenticate with YouTube API"""
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", SCOPES
    )
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, video_path, title, description, tags):
    """Upload video to YouTube"""
    
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22"  # People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "publishAt": "2026-05-05T09:00:00Z"
        }
    }
    
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    
    youtube_service = authenticate_youtube()
    request = youtube_service.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media
    )
    
    response = request.execute()
    print(f"Video uploaded: {response['id']}")
    return response

if __name__ == "__main__":
    # Example usage - requires YouTube API setup
    title = "Amazing Apple Facts You Didn't Know!"
    description = "Learn interesting facts about apples in this short video."
    tags = ["apple", "fruit", "education", "facts", "health"]
    upload_video(None, "output_video.mp4", title, description, tags)