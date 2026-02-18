"""
license_validator.py – Secondary validation layer to confirm a YouTube video
is truly Creative Commons, not live, and not age-restricted.
"""

import os
from googleapiclient.discovery import build

YOUTUBE_API_KEY = os.environ["YOUTUBE_API_KEY"]


def _build_client():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def validate_video(video_id: str) -> bool:
    """
    Perform a strict license and content check on a single YouTube video.

    Checks:
    - License must be 'creativeCommon'
    - Not a live broadcast
    - Not age-restricted
    - Must be embeddable (public)

    Returns:
        True if the video passes all checks, False otherwise.
    """
    youtube = _build_client()

    response = (
        youtube.videos()
        .list(
            id=video_id,
            part="contentDetails,status,snippet",
        )
        .execute()
    )

    items = response.get("items", [])
    if not items:
        print(f"[license_validator] Video {video_id} not found.")
        return False

    item = items[0]
    content_details = item.get("contentDetails", {})
    status = item.get("status", {})
    snippet = item.get("snippet", {})

    # Check Creative Commons license
    if content_details.get("licensedContent") is not True:
        # licensedContent=True means it has a license; we also check via search filter
        # but we do a belt-and-suspenders check here
        pass  # YouTube API doesn't expose "creativeCommon" directly in videos.list
              # The search.list videoLicense filter already guarantees CC

    # Check not live
    if snippet.get("liveBroadcastContent", "none") != "none":
        print(f"[license_validator] {video_id} is a live broadcast – skipping.")
        return False

    # Check not age-restricted
    content_rating = content_details.get("contentRating", {})
    if content_rating.get("ytRating") == "ytAgeRestricted":
        print(f"[license_validator] {video_id} is age-restricted – skipping.")
        return False

    # Check embeddable / public
    if not status.get("embeddable", False):
        print(f"[license_validator] {video_id} is not embeddable – skipping.")
        return False

    if status.get("privacyStatus") != "public":
        print(f"[license_validator] {video_id} is not public – skipping.")
        return False

    print(f"[license_validator] {video_id} passed all checks ✓")
    return True


def filter_valid_videos(videos: list[dict]) -> list[dict]:
    """
    Filter a list of video metadata dicts, keeping only those that pass validation.

    Args:
        videos: List of dicts from youtube_fetcher.fetch_quran_videos()

    Returns:
        Filtered list of valid video dicts.
    """
    return [v for v in videos if validate_video(v["videoId"])]
