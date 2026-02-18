"""
composer.py – Composes the final vertical Quran Short video by overlaying
the transparent foreground on the Pexels background and mixing in the audio.

Pipeline:
  background.mp4 (9:16 background)
  + transparent.mov (lumakey overlay)
  + source_audio.m4a (original Quran recitation audio)
  → final.mp4 (1080x1920, H.264/AAC)
"""

import os
import subprocess

TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp")

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def compose_video(
    background_path: str | None = None,
    overlay_path: str | None = None,
    audio_path: str | None = None,
    output_path: str | None = None,
) -> str:
    """
    Compose the final video using FFmpeg.

    Steps:
    1. Scale background to 1080x1920, crop/pad to fill exactly.
    2. Scale transparent overlay to 1080x1920.
    3. Overlay transparent video on top of background.
    4. Mix in original audio, trim to shortest stream.
    5. Encode as H.264 + AAC for maximum compatibility.

    Args:
        background_path: Path to background video. Defaults to tmp/background.mp4.
        overlay_path:    Path to transparent overlay. Defaults to tmp/transparent.mov.
        audio_path:      Path to audio file. Defaults to tmp/source_audio.m4a.
        output_path:     Output path. Defaults to tmp/final.mp4.

    Returns:
        Absolute path to the composed final.mp4.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    if background_path is None:
        background_path = os.path.join(TMP_DIR, "background.mp4")
    if overlay_path is None:
        overlay_path = os.path.join(TMP_DIR, "transparent.mov")
    if audio_path is None:
        audio_path = os.path.join(TMP_DIR, "source_audio.m4a")
    if output_path is None:
        output_path = os.path.join(TMP_DIR, "final.mp4")

    if os.path.exists(output_path):
        os.remove(output_path)

    # FFmpeg filter_complex explanation:
    # [0:v] → background: scale to 1080x1920 using cover-crop strategy
    #         scale2ref ensures we fill the frame, then crop to exact size
    # [1:v] → overlay (transparent.mov): scale to 1080x1920
    # [bg][fg] → overlay fg on top of bg at position (0,0)
    # [2:a] → original audio stream

    filter_complex = (
        f"[0:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_WIDTH}:{TARGET_HEIGHT},setsar=1[bg];"
        f"[1:v]scale={TARGET_WIDTH}:{TARGET_HEIGHT},setsar=1[fg];"
        f"[bg][fg]overlay=0:0[v]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", background_path,      # Input 0: background
        "-i", overlay_path,          # Input 1: transparent overlay
        "-i", audio_path,            # Input 2: audio
        "-filter_complex", filter_complex,
        "-map", "[v]",               # Use composed video
        "-map", "2:a",               # Use original audio
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",                # Good quality / size balance
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",                 # Trim to shortest stream (audio = Quran clip)
        "-movflags", "+faststart",   # Web-optimized MP4
        output_path,
    ]

    print(f"[composer] Running FFmpeg composition...")
    print(f"[composer] Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"[composer] FFmpeg failed:\n{result.stderr}")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[composer] Final video saved: {output_path} ({size_mb:.1f} MB)")
    return output_path
