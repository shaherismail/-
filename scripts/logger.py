"""
logger.py – Manages the used_videos.json database.
Tracks processed YouTube video IDs and Pexels background performance scores.
"""

import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "used_videos.json")


def load_db() -> dict:
    """Load the database from disk. Returns default structure if missing."""
    if not os.path.exists(DB_PATH):
        return {"used_video_ids": [], "background_performance": {}}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(data: dict) -> None:
    """Persist the database to disk."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_used(video_id: str) -> bool:
    """Return True if this YouTube video ID has already been processed."""
    db = load_db()
    return video_id in db.get("used_video_ids", [])


def mark_used(video_id: str) -> None:
    """Add a YouTube video ID to the used list."""
    db = load_db()
    if video_id not in db["used_video_ids"]:
        db["used_video_ids"].append(video_id)
    save_db(db)


def record_background(pexels_id: str, engagement_boost: float = 1.0) -> None:
    """
    Record or update the engagement score for a Pexels background video.

    Args:
        pexels_id: The Pexels video ID (as string).
        engagement_boost: A positive float to add to the score (default 1.0 per use).
                          Callers can pass higher values when actual view counts are known.
    """
    db = load_db()
    perf = db.setdefault("background_performance", {})
    current = perf.get(str(pexels_id), 0.0)
    perf[str(pexels_id)] = round(current + engagement_boost, 4)
    save_db(db)


def get_background_scores() -> dict:
    """Return the full background_performance mapping {pexels_id: score}."""
    db = load_db()
    return db.get("background_performance", {})
