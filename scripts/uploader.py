"""
uploader.py – Uploads the final video to YouTube, Instagram (Reels), and TikTok.

All credentials are read from environment variables (GitHub Secrets).
"""

import os
import time
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ─── Environment Variables ────────────────────────────────────────────────────
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


# ─── YouTube ──────────────────────────────────────────────────────────────────

def _get_youtube_credentials() -> Credentials:
    """Build OAuth2 credentials from stored refresh token."""
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    return creds


def upload_youtube(video_path: str, metadata: dict) -> str:
    """
    Upload a video to YouTube as a Short.

    Args:
        video_path: Path to final.mp4.
        metadata:   Dict from metadata_generator.generate_metadata().

    Returns:
        YouTube video ID of the uploaded video.
    """
    print("[uploader] Uploading to YouTube...")
    creds = _get_youtube_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": metadata["category_id"],
            "defaultLanguage": metadata.get("default_language", "ar"),
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5,  # 5 MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"[uploader] YouTube upload progress: {pct}%")

    yt_video_id = response.get("id", "")
    print(f"[uploader] YouTube upload complete. Video ID: {yt_video_id}")
    print(f"[uploader] URL: https://www.youtube.com/shorts/{yt_video_id}")
    return yt_video_id


# ─── Instagram ────────────────────────────────────────────────────────────────

def upload_instagram(video_path: str, metadata: dict) -> str:
    """
    Upload a video as an Instagram Reel using the Graph API.

    Flow:
    1. Create a media container (upload the video).
    2. Poll until the container is FINISHED processing.
    3. Publish the container.

    Args:
        video_path: Path to final.mp4.
        metadata:   Dict from metadata_generator.generate_metadata().

    Returns:
        Instagram media ID of the published Reel.

    Note:
        Instagram requires the video to be accessible via a public URL.
        In GitHub Actions, we upload the file to a temporary public host
        or use the resumable upload endpoint. This implementation uses
        the resumable upload approach (Graph API v19+).
    """
    print("[uploader] Uploading to Instagram Reels...")

    caption = (
        metadata["description"][:2200]  # Instagram caption limit
        + "\n\n"
        + metadata["hashtags"]
    )

    # Step 1: Initialize resumable upload session
    init_url = f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/reels"
    init_payload = {
        "media_type": "REELS",
        "caption": caption,
        "share_to_feed": True,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    init_resp = requests.post(init_url, data=init_payload, timeout=30)
    init_resp.raise_for_status()
    container_id = init_resp.json().get("id")
    print(f"[uploader] Instagram container created: {container_id}")

    # Step 2: Upload video bytes to the container
    upload_url = f"https://rupload.facebook.com/video-upload/v19.0/{container_id}"
    file_size = os.path.getsize(video_path)
    headers = {
        "Authorization": f"OAuth {INSTAGRAM_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size),
    }
    with open(video_path, "rb") as f:
        upload_resp = requests.post(upload_url, headers=headers, data=f, timeout=120)
    upload_resp.raise_for_status()
    print(f"[uploader] Instagram video bytes uploaded.")

    # Step 3: Poll for processing completion
    _instagram_wait_for_ready(container_id)

    # Step 4: Publish the Reel
    publish_url = f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    pub_resp = requests.post(publish_url, data=publish_payload, timeout=30)
    pub_resp.raise_for_status()
    media_id = pub_resp.json().get("id", "")
    print(f"[uploader] Instagram Reel published. Media ID: {media_id}")
    return media_id


def _instagram_wait_for_ready(container_id: str, max_wait: int = 300) -> None:
    """Poll Instagram until the media container finishes processing."""
    check_url = f"{GRAPH_API_BASE}/{container_id}"
    params = {
        "fields": "status_code,status",
        "access_token": INSTAGRAM_ACCESS_TOKEN,
    }
    elapsed = 0
    while elapsed < max_wait:
        resp = requests.get(check_url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        status_code = data.get("status_code", "")
        print(f"[uploader] Instagram container status: {status_code}")
        if status_code == "FINISHED":
            return
        if status_code == "ERROR":
            raise RuntimeError(f"[uploader] Instagram processing error: {data}")
        time.sleep(10)
        elapsed += 10
    raise TimeoutError("[uploader] Instagram media processing timed out.")


# ─── TikTok ───────────────────────────────────────────────────────────────────

def upload_tiktok(video_path: str, metadata: dict) -> str:
    """
    Upload a video to TikTok using the Content Posting API v2.

    Flow:
    1. Initialize upload → get upload_url and publish_id.
    2. Upload video bytes to the upload_url.
    3. Publish the video.

    Args:
        video_path: Path to final.mp4.
        metadata:   Dict from metadata_generator.generate_metadata().

    Returns:
        TikTok publish_id.

    Note:
        Requires TikTok Content Posting API access (approved developer app).
    """
    print("[uploader] Uploading to TikTok...")

    file_size = os.path.getsize(video_path)

    # Step 1: Initialize upload
    init_url = f"{TIKTOK_API_BASE}/post/publish/video/init/"
    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    init_body = {
        "post_info": {
            "title": metadata["title"][:150],  # TikTok title limit
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,  # Single chunk upload
            "total_chunk_count": 1,
        },
    }
    init_resp = requests.post(init_url, headers=headers, json=init_body, timeout=30)
    init_resp.raise_for_status()
    init_data = init_resp.json().get("data", {})
    publish_id = init_data.get("publish_id")
    upload_url = init_data.get("upload_url")
    print(f"[uploader] TikTok publish_id: {publish_id}")

    # Step 2: Upload video bytes
    chunk_headers = {
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        "Content-Type": "video/mp4",
    }
    with open(video_path, "rb") as f:
        upload_resp = requests.put(upload_url, headers=chunk_headers, data=f, timeout=120)
    upload_resp.raise_for_status()
    print(f"[uploader] TikTok video bytes uploaded.")

    # Step 3: Check publish status
    _tiktok_wait_for_publish(publish_id)

    print(f"[uploader] TikTok upload complete. Publish ID: {publish_id}")
    return publish_id


def _tiktok_wait_for_publish(publish_id: str, max_wait: int = 300) -> None:
    """Poll TikTok until the video is published."""
    status_url = f"{TIKTOK_API_BASE}/post/publish/status/fetch/"
    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    elapsed = 0
    while elapsed < max_wait:
        resp = requests.post(
            status_url,
            headers=headers,
            json={"publish_id": publish_id},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        status = data.get("status", "")
        print(f"[uploader] TikTok publish status: {status}")
        if status in ("PUBLISH_COMPLETE", "SUCCESS"):
            return
        if status in ("FAILED", "PUBLISH_FAILED"):
            raise RuntimeError(f"[uploader] TikTok publish failed: {data}")
        time.sleep(10)
        elapsed += 10
    raise TimeoutError("[uploader] TikTok publish timed out.")
