"""
downloader.py – Downloads a YouTube video's video and audio streams separately
using yt-dlp, storing them in the tmp/ directory.
"""

import os
import subprocess

TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp")


def _ensure_tmp():
    os.makedirs(TMP_DIR, exist_ok=True)


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

    print(f"[downloader] Downloading video stream for {video_id}...")
    _run_ytdlp(
        url,
        format_selector="bestvideo[ext=mp4][height<=1080]",
        output_path=video_path,
    )

    print(f"[downloader] Downloading audio stream for {video_id}...")
    _run_ytdlp(
        url,
        format_selector="bestaudio[ext=m4a]/bestaudio",
        output_path=audio_path,
    )

    print(f"[downloader] Done. Video: {video_path}, Audio: {audio_path}")
    return video_path, audio_path


def _run_ytdlp(url: str, format_selector: str, output_path: str) -> None:
    """Run yt-dlp as a subprocess."""
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "-f", format_selector,
        "-o", output_path,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"[downloader] yt-dlp failed:\n{result.stderr}"
        )
