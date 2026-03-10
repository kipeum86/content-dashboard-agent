"""YouTube transcript and metadata extraction script.

Usage:
    python extract_youtube.py <youtube_url> <output_dir>

Extracts:
  - raw_text.md: Plain transcript text (no timestamps)
  - timestamps.json: Array of {text, start, duration} objects
  - source_metadata.json: Video title, channel, duration, publish date
"""

import sys
import os
import json
import re
import subprocess


def parse_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_transcript(video_id: str):
    """Extract transcript using youtube-transcript-api."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("ERROR: youtube-transcript-api is not installed. Run: pip install youtube-transcript-api")
        sys.exit(1)

    ytt_api = YouTubeTranscriptApi()

    # Try fetching transcript with multiple language fallbacks
    language_priorities = ['ko', 'en', 'ja', 'zh', 'es', 'fr', 'de']
    for lang in language_priorities:
        try:
            transcript = ytt_api.fetch(video_id, languages=[lang])
            entries = []
            for snippet in transcript:
                entries.append({
                    "text": snippet.text,
                    "start": snippet.start,
                    "duration": snippet.duration,
                })
            print(f"Transcript found in language: {lang}")
            return entries
        except Exception:
            continue

    # Final fallback: let the library auto-select
    try:
        transcript = ytt_api.fetch(video_id)
        entries = []
        for snippet in transcript:
            entries.append({
                "text": snippet.text,
                "start": snippet.start,
                "duration": snippet.duration,
            })
        return entries
    except Exception as e:
        print(f"ERROR: Could not fetch transcript: {e}")
        return None


def extract_metadata(url: str) -> dict:
    """Extract video metadata using yt-dlp --dump-json."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"WARNING: yt-dlp metadata extraction failed: {result.stderr[:200]}")
            return {}

        data = json.loads(result.stdout)
        duration_seconds = data.get("duration", 0)
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)

        return {
            "title": data.get("title", "Unknown Title"),
            "channel": data.get("channel", data.get("uploader", "Unknown Channel")),
            "publish_date": data.get("upload_date", ""),
            "duration": f"{hours:02d}:{minutes:02d}:{seconds:02d}",
            "duration_seconds": duration_seconds,
            "source_url": url,
        }
    except FileNotFoundError:
        print("WARNING: yt-dlp not found. Install with: pip install yt-dlp")
        return {}
    except Exception as e:
        print(f"WARNING: Metadata extraction error: {e}")
        return {}


def extract_youtube(url: str, output_dir: str):
    """Main extraction function for YouTube content."""
    video_id = parse_video_id(url)
    if not video_id:
        print(f"ERROR: Could not parse video ID from URL: {url}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # Extract transcript
    print(f"Extracting transcript for video ID: {video_id}...")
    entries = extract_transcript(video_id)
    if entries is None:
        print("ERROR: No transcript available. Ask user to provide transcript text directly.")
        sys.exit(1)

    # Write raw_text.md (plain text, no timestamps)
    raw_text_path = os.path.join(output_dir, "raw_text.md")
    plain_text = "\n".join(entry["text"] for entry in entries)
    with open(raw_text_path, "w", encoding="utf-8") as f:
        f.write(plain_text)

    # Write timestamps.json
    timestamps_path = os.path.join(output_dir, "timestamps.json")
    with open(timestamps_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    # Extract and write metadata
    print("Extracting video metadata...")
    metadata = extract_metadata(url)
    metadata_path = os.path.join(output_dir, "source_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    char_count = len(plain_text)
    segment_count = len(entries)
    print(f"SUCCESS: Extracted {char_count} characters, {segment_count} transcript segments")
    print(f"  → {raw_text_path}")
    print(f"  → {timestamps_path}")
    print(f"  → {metadata_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_youtube.py <youtube_url> <output_dir>")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2]
    extract_youtube(url, output_dir)
