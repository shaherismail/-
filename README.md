# Quran Shorts Automation 🕌

An automated, serverless pipeline that creates **Quran Shorts** videos and uploads them to **YouTube**, **Instagram**, and **TikTok** — running entirely on **GitHub Actions** with no external server required.

---

## How It Works

```
YouTube API (CC videos) → yt-dlp download → FFmpeg lumakey (remove bg)
    ↓
Pexels API (spiritual background) → FFmpeg compose (1080×1920)
    ↓
YouTube + Instagram + TikTok upload → database/used_videos.json updated
```

The workflow runs **every 6 hours** automatically, or can be triggered manually.

---

## Repository Structure

```
.
├── .github/
│   └── workflows/
│       └── workflow.yml          # GitHub Actions workflow
├── database/
│   └── used_videos.json          # Tracks used videos & background scores
├── scripts/
│   ├── main.py                   # Pipeline orchestrator
│   ├── logger.py                 # Database read/write
│   ├── youtube_fetcher.py        # YouTube Data API search
│   ├── license_validator.py      # CC license verification
│   ├── downloader.py             # yt-dlp video/audio downloader
│   ├── background_remover.py     # FFmpeg lumakey background removal
│   ├── pexels_fetcher.py         # Intelligent Pexels background selector
│   ├── composer.py               # FFmpeg video composition
│   ├── metadata_generator.py     # Title, description, hashtags
│   ├── uploader.py               # YouTube / Instagram / TikTok upload
│   └── generate_token.py         # One-time YouTube OAuth2 token generator
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Fork / Clone this repository

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret**:

| Secret Name | Where to get it |
|---|---|
| `YOUTUBE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/) → YouTube Data API v3 |
| `YOUTUBE_CLIENT_ID` | Google Cloud Console → OAuth 2.0 Client ID |
| `YOUTUBE_CLIENT_SECRET` | Google Cloud Console → OAuth 2.0 Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | Run `python scripts/generate_token.py` locally (see below) |
| `PEXELS_API_KEY` | [Pexels API](https://www.pexels.com/api/) |
| `INSTAGRAM_ACCESS_TOKEN` | [Meta for Developers](https://developers.facebook.com/) → Long-lived token |
| `INSTAGRAM_ACCOUNT_ID` | Your Instagram Business Account ID |
| `TIKTOK_ACCESS_TOKEN` | [TikTok for Developers](https://developers.tiktok.com/) → Content Posting API |

### 3. Generate YouTube Refresh Token (one-time)

```bash
# Install dependencies locally
pip install google-auth-oauthlib

# Set your credentials
export YOUTUBE_CLIENT_ID="your_client_id"
export YOUTUBE_CLIENT_SECRET="your_client_secret"

# Run the token generator
python scripts/generate_token.py
```

Copy the printed refresh token into the `YOUTUBE_REFRESH_TOKEN` secret.

> ⚠️ **Never commit `youtube_token.json` to git!** Add it to `.gitignore`.

### 4. Enable YouTube Data API v3

In Google Cloud Console:
1. Enable **YouTube Data API v3**
2. Create an **OAuth 2.0 Client ID** (Desktop app type)
3. Request a **quota increase** if needed (default: 10,000 units/day; 1 upload ≈ 1,600 units)

---

## Running Manually

1. Go to **Actions** tab in your repository
2. Select **Quran Shorts Automation**
3. Click **Run workflow**
4. Optionally set `dry_run = true` to test without uploading

---

## Dry Run Mode

Set `dry_run: true` in the manual trigger to run the full pipeline (fetch → download → compose) but **skip all uploads**. Useful for testing FFmpeg composition and checking logs.

---

## Intelligent Background Selection

The `pexels_fetcher.py` module uses a scoring algorithm:

1. **Re-use high performers**: If a Pexels background has been used before and has a score ≥ 2.0 (used 2+ times successfully), it's preferred.
2. **Spiritual keyword search**: Searches Pexels with keywords like `mosque`, `desert sunset`, `islamic architecture`, `ocean waves calm`, etc.
3. **Score candidates**: Known backgrounds get a 3× boost; longer (more cinematic) videos score higher.
4. **Portrait filter**: Only videos with ≥ 1080px width or ≥ 1920px height are selected.

---

## FFmpeg Commands

### Background Removal (lumakey)
```bash
ffmpeg -i source_video.mp4 \
  -vf "lumakey=threshold=0.15:tolerance=0.20:softness=0.10" \
  -c:v qtrle \
  -an \
  transparent.mov
```

### Video Composition (1080×1920)
```bash
ffmpeg \
  -i background.mp4 \
  -i transparent.mov \
  -i source_audio.m4a \
  -filter_complex "
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];
    [1:v]scale=1080:1920,setsar=1[fg];
    [bg][fg]overlay=0:0[v]
  " \
  -map "[v]" -map 2:a \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 192k \
  -shortest -movflags +faststart \
  final.mp4
```

---

## Platform Requirements

| Platform | Requirement |
|---|---|
| **YouTube** | YouTube Data API v3 + OAuth2 app approved for upload |
| **Instagram** | Business/Creator account linked to Facebook Page + Graph API app |
| **TikTok** | Developer app with **Content Posting API** access approved |

---

## License

This project is for educational and personal use. All Quran recitations used are sourced from Creative Commons licensed videos. Full attribution is included in every video description.
