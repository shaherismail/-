"""
youtube_fetcher.py – Searches YouTube for Creative Commons Quran recitation videos
under 60 seconds and returns their metadata.
"""

import os
import isodate
from googleapiclient.discovery import build

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]
SEARCH_QUERY = "Quran recitation"
MAX_RESULTS = 20  # Fetch more than needed so we have fallbacks after filtering


def _build_client():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def _parse_duration_seconds(iso_duration: str) -> int:
    """Convert ISO 8601 duration string to total seconds."""
    try:
        return int(isodate.parse_duration(iso_duration).total_seconds())
    except Exception:
        return 9999  # Treat unparseable durations as too long


def fetch_quran_videos() -> list[dict]:
    """
    Search YouTube for short (<60s) Creative Commons Quran recitation videos.

    Returns:
        List of dicts: {videoId, title, channelTitle, duration_seconds}
    """
    youtube = _build_client()

    # Step 1: Search with CC license filter and short duration hint
    search_response = (
        youtube.search()
        .list(
            q=SEARCH_QUERY,
            part="id,snippet",
            type="video",
            videoLicense="creativeCommon",
            videoDuration="short",  # YouTube defines "short" as < 4 minutes
            maxResults=MAX_RESULTS,
            relevanceLanguage="ar",
            safeSearch="strict",
        )
        .execute()
    )

    video_ids = [
        item["id"]["videoId"]
        for item in search_response.get("items", [])
        if item["id"].get("kind") == "youtube#video"
    ]

    if not video_ids:
        print("[youtube_fetcher] No videos found in search.")
        return []

    # Step 2: Get full details (duration, status) for each video
    details_response = (
        youtube.videos()
        .list(
            id=",".join(video_ids),
            part="id,snippet,contentDetails,status",
        )
        .execute()
    )

    results = []
    for item in details_response.get("items", []):
        video_id = item["id"]
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})
        status = item.get("status", {})

        duration_iso = content_details.get("duration", "PT0S")
        duration_seconds = _parse_duration_seconds(duration_iso)

        # Hard filter: must be under 60 seconds
        if duration_seconds >= 60:
            continue

        # Skip live broadcasts
        if snippet.get("liveBroadcastContent", "none") != "none":
            continue

        # Skip age-restricted content
        if content_details.get("contentRating", {}).get("ytRating") == "ytAgeRestricted":
            continue

        results.append(
            {
                "videoId": video_id,
                "title": snippet.get("title", ""),
                "channelTitle": snippet.get("channelTitle", ""),
                "duration_seconds": duration_seconds,
                "license": content_details.get("licensedContent", False),
                "embeddable": status.get("embeddable", False),
            }
        )

    print(f"[youtube_fetcher] Found {len(results)} valid short CC videos.")
    return results
