"""
main.py – Orchestrator for the Quran Shorts automation pipeline.

Execution order:
  1. Load DB → fetch YouTube videos → validate licenses
  2. Pick first unused, valid video
  3. Download video + audio streams
  4. Remove black background (FFmpeg lumakey)
  5. Select intelligent Pexels background
  6. Compose final 1080x1920 video
  7. Generate metadata
  8. Upload to YouTube, Instagram, TikTok (unless DRY_RUN=true)
  9. Update DB (mark video used, record background)
  10. Clean up tmp/
"""

import os
import sys
import shutil

# Add scripts/ to path so relative imports work
sys.path.insert(0, os.path.dirname(__file__))

import logger
import youtube_fetcher
import license_validator
import downloader
import background_remover
import pexels_fetcher
import composer
import metadata_generator
import uploader

TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def cleanup_tmp():
    """Remove all files in the tmp/ directory."""
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR, exist_ok=True)
    print("[main] tmp/ directory cleaned.")


def main():
    print("=" * 60)
    print("🕌  Quran Shorts Automation Pipeline")
    print(f"    DRY_RUN = {DRY_RUN}")
    print("=" * 60)

    # ── Step 1: Fetch and validate videos ─────────────────────────
    print("\n[main] Step 1: Fetching YouTube videos...")
    videos = youtube_fetcher.fetch_quran_videos()

    if not videos:
        print("[main] No videos returned from YouTube. Exiting.")
        sys.exit(0)

    print(f"\n[main] Step 2: Filtering out already-used videos...")
    unused_videos = [v for v in videos if not logger.is_used(v["videoId"])]

    if not unused_videos:
        print("[main] All fetched videos have already been used. Exiting.")
        sys.exit(0)

    print(f"\n[main] Step 3: Validating licenses ({len(unused_videos)} candidates)...")
    valid_videos = license_validator.filter_valid_videos(unused_videos)

    if not valid_videos:
        print("[main] No valid CC videos found after license check. Exiting.")
        sys.exit(0)

    # Pick the first valid video
    video = valid_videos[0]
    video_id = video["videoId"]
    print(f"\n[main] Selected video: '{video['title']}' by {video['channelTitle']} ({video_id})")

    # ── Step 4: Download ───────────────────────────────────────────
    print("\n[main] Step 4: Downloading video and audio...")
    os.makedirs(TMP_DIR, exist_ok=True)
    video_path, audio_path = downloader.download_video_and_audio(video_id)

    # ── Step 5: Remove background ──────────────────────────────────
    print("\n[main] Step 5: Removing black background (FFmpeg lumakey)...")
    overlay_path = background_remover.remove_background(
        input_path=video_path,
        output_path=os.path.join(TMP_DIR, "transparent.mov"),
    )

    # ── Step 6: Select Pexels background ──────────────────────────
    print("\n[main] Step 6: Selecting intelligent Pexels background...")
    pexels_id, bg_path = pexels_fetcher.select_and_download_background()

    # ── Step 7: Compose final video ────────────────────────────────
    print("\n[main] Step 7: Composing final 1080x1920 video...")
    final_path = composer.compose_video(
        background_path=bg_path,
        overlay_path=overlay_path,
        audio_path=audio_path,
        output_path=os.path.join(TMP_DIR, "final.mp4"),
    )

    # ── Step 8: Generate metadata ──────────────────────────────────
    print("\n[main] Step 8: Generating metadata...")
    meta = metadata_generator.generate_metadata(
        original_title=video["title"],
        channel_title=video["channelTitle"],
        video_id=video_id,
    )
    print(f"[main] Title: {meta['title']}")

    # ── Step 9: Upload ─────────────────────────────────────────────
    if DRY_RUN:
        print("\n[main] ⚠️  DRY RUN MODE – Skipping uploads.")
        print(f"[main] Would upload: {final_path}")
        print(f"[main] Metadata:\n  Title: {meta['title']}\n  Tags: {meta['tags'][:5]}...")
    else:
        print("\n[main] Step 9: Uploading to all platforms...")

        # YouTube Upload Check
        if all([os.environ.get("YOUTUBE_CLIENT_ID"), os.environ.get("YOUTUBE_CLIENT_SECRET"), os.environ.get("YOUTUBE_REFRESH_TOKEN")]):
            try:
                uploader.upload_youtube(final_path, meta)
            except Exception as e:
                print(f"[main] ⚠️  YouTube upload failed: {e}")
        else:
            print("[main] ⏩ Skipping YouTube: Credentials missing.")

        # Instagram Upload Check
        if all([os.environ.get("INSTAGRAM_ACCESS_TOKEN"), os.environ.get("INSTAGRAM_ACCOUNT_ID")]):
            try:
                uploader.upload_instagram(final_path, meta)
            except Exception as e:
                print(f"[main] ⚠️  Instagram upload failed: {e}")
        else:
            print("[main] ⏩ Skipping Instagram: Credentials missing.")

        # TikTok Upload Check
        if os.environ.get("TIKTOK_ACCESS_TOKEN"):
            try:
                uploader.upload_tiktok(final_path, meta)
            except Exception as e:
                print(f"[main] ⚠️  TikTok upload failed: {e}")
        else:
            print("[main] ⏩ Skipping TikTok: Credentials missing.")

    # ── Step 10: Update database ───────────────────────────────────
    print("\n[main] Step 10: Updating database...")
    logger.mark_used(video_id)
    # Record background with a base engagement score of 1.0 per use
    logger.record_background(pexels_id, engagement_boost=1.0)
    print(f"[main] Marked video {video_id} as used.")
    print(f"[main] Recorded background {pexels_id} in performance DB.")

    # ── Step 11: Cleanup ───────────────────────────────────────────
    print("\n[main] Step 11: Cleaning up tmp/...")
    cleanup_tmp()

    print("\n" + "=" * 60)
    print("✅  Quran Shorts pipeline completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
