"""
metadata_generator.py – Generates title, description, and hashtags for the
Quran Short video, including proper attribution to the original creator.
"""


def generate_metadata(
    original_title: str,
    channel_title: str,
    video_id: str,
) -> dict:
    """
    Generate upload metadata for a Quran Short.

    Args:
        original_title: Title of the original YouTube video.
        channel_title:  Name of the original YouTube channel.
        video_id:       YouTube video ID of the original video.

    Returns:
        Dict with keys: title, description, tags, category_id, default_language
    """
    # Clean up the original title for use in our title
    clean_title = original_title.strip()
    if len(clean_title) > 60:
        clean_title = clean_title[:57] + "..."

    title = f"🕌 {clean_title} | Quran Recitation Short"

    original_url = f"https://www.youtube.com/watch?v={video_id}"

    description = f"""\
{clean_title}

🌙 A beautiful Quran recitation short to bring peace to your heart.

📖 Original recitation by: {channel_title}
🔗 Original video: {original_url}

This video is shared under the Creative Commons license (CC BY).
All credit goes to the original creator.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤲 Subscribe for daily Quran recitations
🔔 Turn on notifications to never miss a short
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#Quran #QuranRecitation #IslamicShorts #QuranShorts #Alhamdulillah \
#Islam #QuranKareem #MuslimShorts #QuranDaily #Subhanallah \
#IslamicContent #QuranVerses #Deen #Iman #Salah
"""

    tags = [
        "Quran",
        "Quran Recitation",
        "Islamic Shorts",
        "Quran Shorts",
        "Alhamdulillah",
        "Islam",
        "Quran Kareem",
        "Muslim Shorts",
        "Quran Daily",
        "Subhanallah",
        "Islamic Content",
        "Quran Verses",
        "Deen",
        "Iman",
        "Salah",
        channel_title,
    ]

    return {
        "title": title,
        "description": description.strip(),
        "tags": tags,
        "category_id": "29",        # Nonprofits & Activism
        "default_language": "ar",
        "hashtags": "#Quran #QuranRecitation #IslamicShorts #QuranShorts #Alhamdulillah",
    }
