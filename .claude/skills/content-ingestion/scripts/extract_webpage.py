"""Webpage body text extraction script.

Usage:
    python extract_webpage.py <webpage_url> <output_dir>

Extracts body text from a webpage using trafilatura (primary) or
requests + beautifulsoup4 (fallback).
"""

import sys
import os


def extract_with_trafilatura(url: str) -> str:
    """Primary extraction using trafilatura."""
    try:
        import trafilatura
    except ImportError:
        return None

    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        return None

    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )
    return text


def extract_with_beautifulsoup(url: str) -> str:
    """Fallback extraction using requests + BeautifulSoup."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("ERROR: requests and beautifulsoup4 are required. Run: pip install requests beautifulsoup4")
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"ERROR: Failed to fetch webpage: {e}")
        return None

    # Try to detect encoding
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()

    # Extract text from article or main content area
    article = soup.find("article") or soup.find("main") or soup.find("div", {"role": "main"})
    if article:
        text = article.get_text(separator="\n", strip=True)
    else:
        body = soup.find("body")
        text = body.get_text(separator="\n", strip=True) if body else soup.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)


def extract_webpage(url: str, output_dir: str):
    """Main extraction function for webpages."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_text.md")

    # Try trafilatura first
    print(f"Extracting text from: {url}")
    text = extract_with_trafilatura(url)

    if not text or len(text.strip()) < 100:
        print("Trafilatura extraction insufficient, trying BeautifulSoup fallback...")
        fallback_text = extract_with_beautifulsoup(url)
        if fallback_text and len(fallback_text.strip()) > len((text or "").strip()):
            text = fallback_text

    if not text or not text.strip():
        print("ERROR: Could not extract meaningful text from the webpage.")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text.strip())

    char_count = len(text.strip())
    print(f"SUCCESS: Extracted {char_count} characters → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_webpage.py <webpage_url> <output_dir>")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2]
    extract_webpage(url, output_dir)
