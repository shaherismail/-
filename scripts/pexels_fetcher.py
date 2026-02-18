"""
pexels_fetcher.py – Intelligently selects and downloads a spiritual/calm
background video from Pexels, prioritizing backgrounds that have performed
well in previous Quran Shorts (based on engagement scores in the DB).
"""

import os
import random
import requests

from logger import get_background_scores

PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/videos/search"

TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp")

# Spiritual / visually calm search keywords for backgrounds
SPIRITUAL_KEYWORDS = [
    "mosque",
    "desert sunset",
    "islamic architecture",
    "nature calm water",
    "forest light rays",
    "ocean waves calm",
    "mountains sunrise",
    "starry night sky",
    "green meadow peaceful",
    "arabic architecture",
]

# Minimum engagement score to prefer a known background over a new one
HIGH_SCORE_THRESHOLD = 2.0

# Minimum resolution for portrait video
MIN_WIDTH = 1080
MIN_HEIGHT = 1920


def _fetch_pexels_videos(keyword: str, per_page: int = 15) -> list[dict]:
    """Query Pexels API for portrait videos matching a keyword."""
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": keyword,
        "orientation": "portrait",
        "size": "large",
        "per_page": per_page,
    }
    response = requests.get(PEXELS_VIDEO_SEARCH_URL, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("videos", [])


def _get_best_video_file(video: dict) -> str | None:
    """
    From a Pexels video object, return the URL of the best portrait file
    that meets the minimum resolution requirement.
    """
    files = video.get("video_files", [])
    # Filter for portrait files with sufficient resolution
    portrait_files = [
        f for f in files
        if f.get("width", 0) >= MIN_WIDTH or f.get("height", 0) >= MIN_HEIGHT
    ]
    if not portrait_files:
        # Fall back to any file with height >= width (portrait-ish)
        portrait_files = [
            f for f in files
            if f.get("height", 0) >= f.get("width", 1)
        ]
    if not portrait_files:
        return None

    # Pick highest resolution
    best = max(portrait_files, key=lambda f: f.get("height", 0) * f.get("width", 0))
    return best.get("link")


def _download_video(url: str, output_path: str) -> None:
    """Stream-download a video file to disk."""
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)


def select_and_download_background() -> tuple[str, str]:
    """
    Intelligently select and download a Pexels background video.

    Selection algorithm:
    1. Load known background performance scores from DB.
    2. If any background has score >= HIGH_SCORE_THRESHOLD, try to re-download it.
    3. Otherwise, search Pexels with a random spiritual keyword.
    4. Score candidates: boost known high-performers, pick best.
    5. Download to tmp/background.mp4.

    Returns:
        Tuple of (pexels_id: str, local_path: str)
    """
    os.makedirs(TMP_DIR, exist_ok=True)
    output_path = os.path.join(TMP_DIR, "background.mp4")

    scores = get_background_scores()

    # --- Strategy 1: Re-use a high-performing known background ---
    high_performers = {
        pid: score for pid, score in scores.items()
        if score >= HIGH_SCORE_THRESHOLD
    }

    if high_performers:
        # Pick the top scorer
        best_id = max(high_performers, key=lambda k: high_performers[k])
        print(f"[pexels_fetcher] Re-using high-performing background ID: {best_id} (score={high_performers[best_id]})")

        # Fetch its details from Pexels to get a fresh download URL
        headers = {"Authorization": PEXELS_API_KEY}
        resp = requests.get(
            f"https://api.pexels.com/videos/videos/{best_id}",
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            video = resp.json()
            url = _get_best_video_file(video)
            if url:
                print(f"[pexels_fetcher] Downloading background from Pexels...")
                _download_video(url, output_path)
                return str(best_id), output_path
        print(f"[pexels_fetcher] Could not re-fetch {best_id}, falling back to search.")

    # --- Strategy 2: Search with a spiritual keyword ---
    keyword = random.choice(SPIRITUAL_KEYWORDS)
    print(f"[pexels_fetcher] Searching Pexels with keyword: '{keyword}'")
    candidates = _fetch_pexels_videos(keyword)

    if not candidates:
        # Try another keyword as fallback
        keyword = random.choice(SPIRITUAL_KEYWORDS)
        candidates = _fetch_pexels_videos(keyword)

    if not candidates:
        raise RuntimeError("[pexels_fetcher] No Pexels videos found for any keyword.")

    # Score candidates: boost known performers, otherwise use duration as proxy for quality
    def candidate_score(v: dict) -> float:
        vid_id = str(v.get("id", ""))
        known_score = scores.get(vid_id, 0.0)
        # Prefer longer videos (more cinematic) and known performers
        duration_score = min(v.get("duration", 0) / 60.0, 1.0)
        return known_score * 3.0 + duration_score

    candidates.sort(key=candidate_score, reverse=True)

    # Pick the best candidate that has a valid portrait file
    for video in candidates:
        url = _get_best_video_file(video)
        if url:
            pexels_id = str(video["id"])
            print(f"[pexels_fetcher] Selected Pexels video ID: {pexels_id}")
            print(f"[pexels_fetcher] Downloading background...")
            _download_video(url, output_path)
            return pexels_id, output_path

    raise RuntimeError("[pexels_fetcher] No suitable portrait video found on Pexels.")
