"""PDF text extraction script.

Usage:
    python extract_pdf.py <pdf_file_path> <output_dir>

Extracts text from a PDF file using pdfplumber and writes it to raw_text.md.
"""

import sys
import os

def extract_pdf(pdf_path: str, output_dir: str) -> str:
    """Extract text from a PDF file and save as raw_text.md."""
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: pdfplumber is not installed. Run: pip install pdfplumber")
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "raw_text.md")

    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(f"<!-- Page {i}/{total_pages} -->\n\n{text.strip()}")

    if not pages_text:
        print("WARNING: No text could be extracted from the PDF. The PDF may be scanned/image-based.")
        # Write empty file so validation can catch it
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("")
        return output_path

    full_text = "\n\n---\n\n".join(pages_text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    char_count = len(full_text)
    print(f"SUCCESS: Extracted {char_count} characters from {total_pages} pages → {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_pdf.py <pdf_file_path> <output_dir>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    extract_pdf(pdf_path, output_dir)
