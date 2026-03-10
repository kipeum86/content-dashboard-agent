"""Extraction result validation script.

Usage:
    python validate_extraction.py <raw_text_path>

Validates that the extracted text file meets minimum quality criteria.
Exit code 0 = pass, exit code 1 = fail.
"""

import sys
import os

MIN_CHAR_COUNT = 500


def validate(raw_text_path: str) -> bool:
    """Validate extraction result."""
    # Check file exists
    if not os.path.exists(raw_text_path):
        print(f"FAIL: File does not exist: {raw_text_path}")
        return False

    # Check file is not empty
    file_size = os.path.getsize(raw_text_path)
    if file_size == 0:
        print(f"FAIL: File is empty: {raw_text_path}")
        return False

    # Read and check character count
    with open(raw_text_path, "r", encoding="utf-8") as f:
        content = f.read()

    char_count = len(content.strip())

    if char_count < MIN_CHAR_COUNT:
        print(f"FAIL: Insufficient content — {char_count} characters (minimum: {MIN_CHAR_COUNT})")
        return False

    # Count lines for informational output
    line_count = len(content.splitlines())

    print(f"PASS: {char_count} characters, {line_count} lines")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_extraction.py <raw_text_path>")
        sys.exit(1)

    raw_text_path = sys.argv[1]
    success = validate(raw_text_path)
    sys.exit(0 if success else 1)
