# Content Ingestion Skill

> Extracts text content from diverse source types (PDF, YouTube, webpage, text files) into standardized markdown format.

## Purpose

This skill handles Step 2 (Content Extraction) of the content dashboard pipeline. It takes a content source and produces clean, structured text ready for analysis.

## Supported Source Types

| source_type | Script | Output files |
|-------------|--------|-------------|
| `pdf` | `extract_pdf.py` | `raw_text.md` |
| `text` | Direct file copy | `raw_text.md` |
| `youtube` | `extract_youtube.py` | `raw_text.md` + `timestamps.json` + `source_metadata.json` |
| `webpage` | `extract_webpage.py` | `raw_text.md` |

## Usage

### PDF Extraction
```bash
python .claude/skills/content-ingestion/scripts/extract_pdf.py "<pdf_file_path>" "<output_dir>"
```
- Uses `pdfplumber` for text extraction
- Preserves page structure with page markers
- Limited accuracy for scanned PDFs without text layers

### Text File Extraction
For `.md` and `.txt` files, directly copy the content:
```bash
cp "<source_file>" "<output_dir>/raw_text.md"
```
- Auto-detect encoding (UTF-8, UTF-16, EUC-KR, etc.)

### YouTube Extraction
```bash
python .claude/skills/content-ingestion/scripts/extract_youtube.py "<youtube_url>" "<output_dir>"
```
- Uses `youtube-transcript-api` for subtitle extraction
- Uses `yt-dlp --dump-json` for video metadata
- Subtitle priority: manual subtitles → auto-generated subtitles → escalation
- Produces three files:
  - `raw_text.md`: Plain transcript text (no timestamps)
  - `timestamps.json`: Array of `{"text", "start", "duration"}` objects
  - `source_metadata.json`: Video title, channel, duration, publish date

### Webpage Extraction
```bash
python .claude/skills/content-ingestion/scripts/extract_webpage.py "<webpage_url>" "<output_dir>"
```
- Uses `trafilatura` for body text extraction
- Falls back to `requests` + `beautifulsoup4` if trafilatura fails
- Strips navigation, ads, and boilerplate

## Validation

After extraction, validate the result:
```bash
python .claude/skills/content-ingestion/scripts/validate_extraction.py "<output_dir>/raw_text.md"
```

### Success criteria:
- File exists
- File is not empty
- Contains at least 500 characters

### On failure:
- Auto-retry extraction once
- If still fails, escalate to user (ask them to provide source text directly)

## Output Structure

All outputs are written to the specified `<output_dir>`:
```
<output_dir>/
├── raw_text.md              # Always produced
├── timestamps.json          # YouTube only
└── source_metadata.json     # YouTube only
```

## Notes

- Extracted text preserves source language (no translation)
- PDF extraction quality depends on the source PDF having an embedded text layer
- YouTube transcript extraction requires network access
- Webpage extraction requires network access
