"""
background_remover.py – Removes the black background from a Quran recitation
video using FFmpeg's lumakey filter, producing a transparent overlay file.

Input:  tmp/source_video.mp4  (black background, white text/speaker)
Output: tmp/transparent.mov   (QuickTime RLE with alpha channel)
"""

import os
import subprocess

TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp")


def remove_background(
    input_path: str | None = None,
    output_path: str | None = None,
    threshold: float = 0.15,
    tolerance: float = 0.20,
    softness: float = 0.10,
) -> str:
    """
    Apply FFmpeg lumakey filter to remove the black background.

    The lumakey filter treats dark pixels as transparent, keeping bright
    pixels (white text, speaker) fully opaque.

    Args:
        input_path:  Path to source video. Defaults to tmp/source_video.mp4.
        output_path: Path for output. Defaults to tmp/transparent.mov.
        threshold:   Luma level treated as key color (0=black, 1=white). Default 0.15.
        tolerance:   Range around threshold to also key out. Default 0.20.
        softness:    Edge softness for smooth blending. Default 0.10.

    Returns:
        Absolute path to the transparent .mov file.

    Raises:
        RuntimeError: If FFmpeg fails.
    """
    if input_path is None:
        input_path = os.path.join(TMP_DIR, "source_video.mp4")
    if output_path is None:
        output_path = os.path.join(TMP_DIR, "transparent.mov")

    # Remove stale output
    if os.path.exists(output_path):
        os.remove(output_path)

    # FFmpeg lumakey filter:
    # lumakey=threshold:tolerance:softness
    # threshold=0.15 → pixels with luma < 0.15 become transparent
    # tolerance=0.20 → extend the key range
    # softness=0.10  → smooth edges
    vf_filter = f"lumakey=threshold={threshold}:tolerance={tolerance}:softness={softness}"

    cmd = [
        "ffmpeg",
        "-y",                    # Overwrite output without asking
        "-i", input_path,
        "-vf", vf_filter,
        "-c:v", "qtrle",         # QuickTime RLE codec supports alpha channel
        "-an",                   # No audio in the overlay (audio handled separately)
        output_path,
    ]

    print(f"[background_remover] Running FFmpeg lumakey filter...")
    print(f"[background_remover] Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"[background_remover] FFmpeg failed:\n{result.stderr}"
        )

    print(f"[background_remover] Transparent overlay saved to: {output_path}")
    return output_path
