"""
downloader.py – Downloads a YouTube video's video and audio streams separately
using yt-dlp, storing them in the tmp/ directory.

Bot Detection Fix:
  YouTube blocks yt-dlp on server environments (GitHub Actions).
  Solution: Export your YouTube cookies from your browser and store them
  as a GitHub Secret named YOUTUBE_COOKIES (the full contents of cookies.txt).
  The downloader will write them to a temp file and pass them to yt-dlp.
"""

import os
import subprocess
import tempfile

TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp")
COOKIES_ENV = "YOUTUBE_COOKIES"  # GitHub Secret name


def _ensure_tmp():
    os.makedirs(TMP_DIR, exist_ok=True)


def _get_cookies_file() -> str | None:
    """
    Write YOUTUBE_COOKIES env var content to a temp file and return its path.
    Returns None if the env var is not set.
    """
    cookies_content = os.environ.get(COOKIES_ENV, "").strip()
    if not cookies_content:
        return None
    # Write to a temp file in the tmp directory
    cookies_path = os.path.join(TMP_DIR, "yt_cookies.txt")
    with open(cookies_path, "w", encoding="utf-8") as f:
        f.write(cookies_content)
    return cookies_path


def download_video_and_audio(video_id: str) -> tuple[str, str]:
    """
    Download video-only and audio-only streams for a YouTube video.

    Args:
        video_id: YouTube video ID (e.g. "dQw4w9WgXcQ")

    Returns:
        Tuple of (video_path, audio_path) as absolute strings.

    Raises:
        RuntimeError: If yt-dlp fails.
    """
    _ensure_tmp()
    url = f"https://www.youtube.com/watch?v={video_id}"
    video_path = os.path.join(TMP_DIR, "source_video.mp4")
    audio_path = os.path.join(TMP_DIR, "source_audio.m4a")

    # Remove stale files
    for path in [video_path, audio_path]:
        if os.path.exists(path):
            os.remove(path)

    cookies_file = _get_cookies_file()
    if cookies_file:
        print(f"[downloader] Using cookies file for authentication.")
    else:
        print(f"[downloader] ⚠️  No YOUTUBE_COOKIES found. May fail on CI environments.")

    print(f"[downloader] Downloading video stream for {video_id}...")
    _run_ytdlp(
        url,
        format_selector="bestvideo[ext=mp4][height<=1080]",
        output_path=video_path,
        cookies_file=cookies_file,
    )

    print(f"[downloader] Downloading audio stream for {video_id}...")
    _run_ytdlp(
        url,
        format_selector="bestaudio[ext=m4a]/bestaudio",
        output_path=audio_path,
        cookies_file=cookies_file,
    )

    print(f"[downloader] Done. Video: {video_path}, Audio: {audio_path}")
    return video_path, audio_path


def _run_ytdlp(url: str, format_selector: str, output_path: str, cookies_file: str | None = None) -> None:
    """Run yt-dlp as a subprocess, optionally with a cookies file."""
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--extractor-retries", "3",
        "--sleep-interval", "2",       # Be polite to YouTube
        "--max-sleep-interval", "5",
        "-f", format_selector,
        "-o", output_path,
    ]

    if cookies_file:
        cmd += ["--cookies", cookies_file]

    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"[downloader] yt-dlp failed:\n{result.stderr}"
        )
