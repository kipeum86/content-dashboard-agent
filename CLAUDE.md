# Content Dashboard Agent

> Automated content-to-dashboard pipeline. Accepts diverse content sources and transforms them into professional, interactive HTML dashboards.

## Project Overview

This agent orchestrates a pipeline that:
1. Accepts content input from `/input/` folder (PDF, text file) or URL (YouTube, webpage)
2. Extracts text from the source
3. Analyzes and structures the content into JSON
4. Generates an interactive HTML dashboard

## Input Folder

Users place source files in the `/input/` folder. The agent scans this folder for content to process.

- **Supported files**: `.pdf`, `.md`, `.txt`
- **URLs**: YouTube and webpage URLs are provided directly by the user (not placed in `/input/`)
- When the user says "make a dashboard" without specifying a file, check `/input/` for available files
- If multiple files exist in `/input/`, ask the user which one to process (v1 processes one file at a time)

## Workflow Summary

```
[User Input] → Preference Collection → Content Ingestion → Parameter Resolution → Content Analysis → Dashboard Generation → [Revision Loop] → [Done]
```

---

## Step 0: Preference Collection Protocol

When the user provides a content source, ask **only one question** — the layout choice:

```
대시보드 레이아웃을 선택해주세요:
1. Interactive Dashboard (기본값 — 섹션별 네비게이션, 상세 분석)
2. Visual Infographic (스크롤 기반, 시각적 스토리텔링)
3. One-Page Executive Summary (핵심 요약, 컴팩트)
```

**Everything else is auto-determined.** Do NOT ask the user about:
- Theme → auto-resolved from content analysis at Step 4
- Library example → auto-selected at Step 2.5
- Content type → auto-detected at Step 1 / Step 2.5
- Cover image URL → skip; user can add later via revision loop

**The user can override any of these by mentioning them in their initial request** (e.g., "dark theme으로 해줘", "example-book-01처럼 만들어줘"). But never proactively ask.

---

## Step 1: Input Handling & Source Type Classification

### Source type rules (definitive at Step 1):
```
*.pdf                              → pdf
*.md, *.txt                        → text
youtube.com/*, youtu.be/*          → youtube
notebooklm.google.com/notebook/*   → notebooklm
Other URLs (http/https)            → webpage
```

### Content type rules (may be deferred):
```
User explicitly specified      → use specified value (definitive)
source_type is youtube         → media (definitive)
source_type is webpage         → article (definitive)
source_type is notebooklm      → pending — resolved at Step 2.5
source_type is pdf/text        → pending — resolved at Step 2.5
```

### Validation:
- Confirm source_type is one of: `pdf`, `text`, `youtube`, `webpage`, `notebooklm`
- If ambiguous, default to `document` and proceed (do not ask the user)

---

## Step 2: Content Extraction

Invoke the appropriate skill based on source_type.

### Invocation:
Run the appropriate extraction script based on source_type:
```bash
# For files in /input/ folder:
python .claude/skills/content-ingestion/scripts/extract_pdf.py input/<filename>.pdf output/<title>
# For text files, directly copy:
cp input/<filename>.md output/<title>/raw_text.md

# For URLs (provided directly by user):
python .claude/skills/content-ingestion/scripts/extract_youtube.py <url> output/<title>
python .claude/skills/content-ingestion/scripts/extract_webpage.py <url> output/<title>

# For NotebookLM notebooks (invoke notebooklm-ingestion skill):
python .claude/skills/notebooklm-ingestion/scripts/extract_notebooklm.py <notebook_url_or_id> output/<title>
```

### Output location: `/output/<title>/`
- `raw_text.md` — extracted text (all source types)
- `timestamps.json` — subtitle timestamps (YouTube only)
- `source_metadata.json` — video/notebook metadata (YouTube and NotebookLM)
- `notebooklm_report.md` — Study Guide Markdown (NotebookLM only, best-effort)

### Validation:
Run `validate_extraction.py` to confirm:
- File exists and is not empty
- Contains at least 500 characters

### Failure handling:
- Auto-retry once on failure
- If still fails, report the error to user (do not ask for alternative input — user will decide next steps)

---

## Step 2.5: Parameter Resolution Protocol

After content extraction, resolve any unspecified preferences using the actual extracted content.

### Auto-resolution rules:

**content_type** (if not user-specified):
- Academic structure (abstract, methodology, references) → `paper`
- Chapter-based, 10+ chapters → `book`
- Short single-topic → `article`
- YouTube source → `media`
- NotebookLM source with ≥10 processed sources → `book`
- Default → `document`

**Layout** (if not user-specified):
- 5+ sections/chapters/segments → Interactive Dashboard
- Strong narrative flow → Visual Infographic
- Short key-points → One-Page Executive Summary

**Theme** (if not user-specified):
- Deferred to web-content-designer skill's content analysis at Step 4

**Library example** (if not user-specified):
- Read `/library/README.md` and select the most recent example matching content_type + layout
- If no match or library is empty, fall back to web-content-designer built-in patterns

---

## Step 3: Content Analysis (Invoke content-analyzer sub-agent)

Invoke the **content-analyzer** sub-agent to generate structured JSON.

### Data to pass:
- File path: `/output/<title>/raw_text.md`
- Resolved `content_type`
- (YouTube) `/output/<title>/timestamps.json`
- (YouTube) `/output/<title>/source_metadata.json`
- (NotebookLM) `/output/<title>/notebooklm_report.md` — if file exists, pass as structural hint with instruction: "이 파일은 NotebookLM이 생성한 Study Guide입니다. 구조 참고용으로만 사용하고, 분석은 raw_text.md 기준으로 수행하세요."
- (NotebookLM) `/output/<title>/source_metadata.json`
- (Book) Cover image URL if available

### Expected output:
- `/output/<title>/content_analysis.json`

### Validation:
- JSON must be valid and parseable
- Must conform to the content_type-specific schema
- All required fields must be present

### Failure handling:
- Auto-retry up to 2 times on schema errors
- If still fails, report error details to user

---

## Step 4: Dashboard Generation (Invoke web-content-designer skill)

### Library example selection (before generation):
1. If user specified a library example → use it directly
2. If not, read `/library/README.md` → select 1 example matching content_type + layout (prefer most recent)
3. Scan the selected example HTML for structural/stylistic patterns only
4. If library is empty, use web-content-designer built-in patterns

### Reference principles:
- **Absorb from examples**: HTML structure, CSS styling patterns, interaction patterns, component layout, visualization types
- **Do NOT absorb**: text content, data values, quotes, keywords, color theme

### Information to pass to web-content-designer:
- Full analysis JSON content (`content_analysis.json`)
- Source text (`raw_text.md`) — for theme analysis unless user specified a theme
- Layout selection
- User-specified theme (if any)
- Content type-specific instructions:
  - `book`: Place cover image at top of sidebar if available
  - `media`: **Must** reference a media-type library example for styling (scan `/library/` for YouTube-sourced dashboards). Include timeline visualization with time markers. **Must** include a prominent "Watch Original Video" button at the top of the dashboard linking to `media_meta.source_url`
- Language: always preserve source language

### Output:
- `/output/<title>/<title>-dashboard.html`

---

## Step 5: Revision Loop Protocol

After presenting the dashboard, enter the revision loop. No limit on iterations.

### Revision type auto-classification:

| Type | Detection signal | Action |
|------|-----------------|--------|
| **Design-only** | Color, font, spacing, layout, visual styling | Edit HTML directly |
| **Content-only** | Summary inaccurate, section missing, quote wrong | Re-invoke content-analyzer → regenerate JSON → regenerate dashboard |
| **Mixed** | Both design and content changes | Process content first, then apply design |

### Design preservation (for content revisions):
When content revision triggers dashboard regeneration:
1. Extract **design overrides** from current HTML (CSS custom properties, colors, fonts, layout modifications)
2. Pass overrides to web-content-designer alongside updated JSON
3. Skill applies overrides on top of freshly generated dashboard
4. If extraction fails, warn user and ask them to re-state design preferences

### Content revision — sub-agent invocation:
Pass to content-analyzer:
- Source text (`raw_text.md`)
- Existing JSON (`content_analysis.json`)
- User's specific revision request

Sub-agent modifies only relevant portions and returns updated JSON.

---

## Output Management

### File naming:
- Output folder: `/output/<title>/` (title derived from content, sanitized for filesystem)
- Dashboard file: `<title>-dashboard.html`

### Per-content folder structure:
```
/output/<title>/
├── raw_text.md
├── timestamps.json          # YouTube only
├── source_metadata.json     # YouTube only
├── content_analysis.json
└── <title>-dashboard.html
```

---

## Library Management

The `/library/` folder stores high-quality dashboard examples for reference.

### Registration (user-initiated only):
1. User explicitly requests "add to library"
2. Copy dashboard HTML → `/library/example-<content_type>-<sequence>.html`
3. Update `/library/README.md` with metadata
4. Never auto-register

### Naming convention:
```
example-<content_type>-<sequence>.html
```

### Reference considerations:
- Library files can be large — selectively scan structure, not full content
- When user says "like example-book-01", use that file regardless of content_type match
- Library examples take priority over built-in examples

---

## Skill & Sub-agent Invocation Summary

| Component | When | What to pass |
|-----------|------|-------------|
| **content-ingestion** skill | Step 2 (pdf, text, youtube, webpage) | source file/URL + source_type |
| **notebooklm-ingestion** skill | Step 2 (notebooklm) | notebook URL or ID |
| **content-analyzer** sub-agent | Step 3, Step 5 (content revisions) | raw_text.md + content_type + timestamps/metadata (if YouTube) + notebooklm_report.md hint (if NotebookLM) + cover URL (if book) |
| **web-content-designer** skill | Step 4 | content_analysis.json + raw_text.md + layout + theme + library example |
