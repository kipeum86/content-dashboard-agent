# Content Dashboard Agent

> Automated content-to-dashboard pipeline. Accepts diverse content sources and transforms them into professional, interactive HTML dashboards.

## Project Overview

This agent orchestrates a pipeline that:
1. Accepts content input (PDF, text file, YouTube URL, webpage URL)
2. Extracts text from the source
3. Analyzes and structures the content into JSON
4. Generates an interactive HTML dashboard

## Workflow Summary

```
[User Input] → Preference Collection → Content Ingestion → Parameter Resolution → Content Analysis → Dashboard Generation → [Revision Loop] → [Done]
```

---

## Step 0: Preference Collection Protocol

When the user provides a content source, collect all optional preferences in **a single prompt** before starting the pipeline:

| Preference | Required? | If not specified |
|-----------|-----------|-----------------|
| Layout (Dashboard / Infographic / Summary) | No | Auto-resolved after content extraction (Step 2.5) |
| Theme | No | Auto-resolved based on content analysis at dashboard generation |
| Library example ("make it like example-book-01") | No | Auto-resolved after content_type is confirmed (Step 2.5) |
| Content type override (document/book/paper/article/media) | No | Auto-resolved after content extraction (Step 2.5) |
| Cover image URL (book only) | Conditional | Always ask the user to provide one when content_type is book |

**Prompt template:**
```
I'll create a dashboard from this content. Before I start, do you have any preferences?

- **Layout**: Interactive Dashboard / Visual Infographic / One-Page Executive Summary (default: auto)
- **Theme**: Any color theme preference? (default: auto based on content)
- **Style reference**: Want it similar to a library example? (e.g., "like example-book-01")
- **Content type**: document / book / paper / article / media (default: auto-detect)

You can skip all of these — I'll auto-determine everything.
```

If user skips all, proceed with auto-determination at Step 2.5.

---

## Step 1: Input Handling & Source Type Classification

### Source type rules (definitive at Step 1):
```
*.pdf                          → pdf
*.md, *.txt                    → text
youtube.com/*, youtu.be/*      → youtube
Other URLs (http/https)        → webpage
```

### Content type rules (may be deferred):
```
User explicitly specified      → use specified value (definitive)
source_type is youtube         → media (definitive)
source_type is webpage         → article (definitive)
source_type is pdf/text        → pending — resolved at Step 2.5
```

### Validation:
- Confirm source_type is one of: `pdf`, `text`, `youtube`, `webpage`
- If ambiguous, ask the user directly

### Conditional: book content_type
When content_type is determined to be `book` (either user-specified or resolved at Step 2.5):
- Always ask user for a book cover image URL
- If user cannot provide one, proceed without it but recommend adding via revision loop

---

## Step 2: Content Extraction (Invoke content-ingestion skill)

Invoke the **content-ingestion** skill to extract text from the source.

### Invocation:
Run the appropriate extraction script based on source_type:
```bash
python .claude/skills/content-ingestion/scripts/extract_pdf.py <file_path> <output_dir>
python .claude/skills/content-ingestion/scripts/extract_youtube.py <url> <output_dir>
python .claude/skills/content-ingestion/scripts/extract_webpage.py <url> <output_dir>
```

### Output location: `/output/<title>/`
- `raw_text.md` — extracted text (all source types)
- `timestamps.json` — subtitle timestamps (YouTube only)
- `source_metadata.json` — video metadata (YouTube only)

### Validation:
Run `validate_extraction.py` to confirm:
- File exists and is not empty
- Contains at least 500 characters

### Failure handling:
- Auto-retry once on failure
- If still fails, ask user to provide source text directly

---

## Step 2.5: Parameter Resolution Protocol

After content extraction, resolve any unspecified preferences using the actual extracted content.

### Auto-resolution rules:

**content_type** (if not user-specified):
- Academic structure (abstract, methodology, references) → `paper`
- Chapter-based, 10+ chapters → `book`
- Short single-topic → `article`
- YouTube source → `media`
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
  - `media`: Include timeline visualization with time markers
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
| **content-ingestion** skill | Step 2 | source file/URL + source_type |
| **content-analyzer** sub-agent | Step 3, Step 5 (content revisions) | raw_text.md + content_type + timestamps/metadata (if YouTube) + cover URL (if book) |
| **web-content-designer** skill | Step 4 | content_analysis.json + raw_text.md + layout + theme + library example |
