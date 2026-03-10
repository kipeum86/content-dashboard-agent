# Content Dashboard Agent — Design Document

> Implementation plan for Claude Code
> Version: v2.1 | Date: 2026-03-10

---

## 1. Task Context

### 1.1 Background

The current content dashboard creation workflow operates as a 3-step manual pipeline:

1. **Summary generation** — Generate a structured markdown summary using Notebook LM or another LLM
2. **JSON conversion** — Convert the summary into a dashboard-ready JSON schema using Gemini or another LLM
3. **Dashboard generation** — Build the HTML dashboard in Gemini Canvas

This project consolidates the entire pipeline into a single Claude Code agent system, automating everything from content input to HTML dashboard output.

### 1.2 Purpose

An agent system that accepts diverse content sources (papers, books, YouTube videos, webpages, text files) and transforms them into professional, interactive HTML dashboards — best-effort automated with escalation on ambiguity and a post-generation revision loop.

### 1.3 Scope

**In scope (v1):**
- Support for 4 content source types: PDF (papers/books), text files (md/txt), YouTube URLs, webpage URLs
- 5 content type schemas: `document`, `book`, `paper`, `article`, `media`
- Content analysis and structured JSON generation via dedicated sub-agent
- HTML dashboard generation via the existing `web-content-designer` skill
- Best-effort automated pipeline with user escalation on ambiguity (no formal human review checkpoints)
- Post-generation revision loop (unlimited, natural language)
- Pre-pipeline preference collection (layout, theme, library example)

**Out of scope (v1):**
- Multi-source merging (combining multiple content sources into a single dashboard)
- Dashboard template customization UI
- Automatic deployment/hosting
- Translation (dashboards are generated in the source language)

### 1.4 Input/Output Definition

| Item | Description |
|------|-------------|
| **Input** | Content file path or URL (PDF, md, txt, YouTube URL, webpage URL) |
| **Final output** | Single HTML file (interactive dashboard) |
| **Intermediate outputs** | Structured JSON file (`content_analysis.json`), extracted source text file, timestamps file (YouTube only) |

### 1.5 Constraints

- YouTube transcript extraction requires network access
- PDF text extraction quality depends on whether the source PDF has an embedded text layer
- Dashboard generation is limited to the layout options available in the `web-content-designer` skill (Dashboard, Infographic, Summary)
- For `book` content type, the user must be prompted for a cover image URL
- Dashboard content language always follows the source language
- Timestamp accuracy for media segments is approximate (±1-2 minutes tolerance)

### 1.6 Glossary

| Term | Definition |
|------|------------|
| **Content source** | The original material to be transformed into a dashboard (file or URL) |
| **Source type** | Classification by input format: `pdf`, `text`, `youtube`, `webpage` |
| **Content type** | Classification by content nature: `document`, `book`, `paper`, `article`, `media` — boundaries are soft; agent auto-judges based on content |
| **Analysis JSON** | The structured JSON data used to generate the dashboard |
| **Layout** | One of three output formats from the web-content-designer skill: Interactive Dashboard, Visual Infographic, One-Page Executive Summary |
| **Revision loop** | Post-generation cycle where the user requests modifications and the agent applies them |

---

## 2. Workflow Definition

### 2.1 Pipeline Overview

```
[User Input] → Preference Collection → Content Ingestion → Parameter Resolution → Content Analysis → Dashboard Generation → [Revision Loop] → [Done]
```

### 2.2 Workflow: Content-to-Dashboard Pipeline

#### Step 0: Preference Collection

| Item | Details |
|------|---------|
| **Executor** | Main agent (CLAUDE.md) |
| **Input** | User's initial request (file path or URL + any stated preferences) |
| **Processing** | Collect all optional preferences in a single prompt before starting the pipeline |
| **Output** | Preference set: layout, theme, library example reference, content_type override (if any) |
| **Success criteria** | User confirms or skips; pipeline proceeds |
| **Validation method** | N/A — all fields are optional |
| **Failure handling** | If user skips all, agent auto-determines everything |

**Items collected in a single prompt:**

| Preference | Required? | If not specified |
|-----------|-----------|-----------------|
| Layout (Dashboard / Infographic / Summary) | No | Auto-resolved after content extraction (Step 2.5) |
| Theme | No | Auto-resolved based on content analysis at dashboard generation |
| Library example ("make it like example-book-01") | No | Auto-resolved after content_type is confirmed (Step 2.5) |
| Content type override | No | Auto-resolved after content extraction (Step 2.5) |
| Cover image URL (book only) | Conditional | Agent always asks the user to provide one |

**Note:** Auto-selection of unspecified values cannot happen at Step 0 because content has not been extracted yet. Values the user does not specify are resolved at **Step 2.5** after content extraction, when the agent has actual content to analyze.

#### Step 1: Content Reception & Type Classification

| Item | Details |
|------|---------|
| **Executor** | Main agent judgment + script |
| **Input** | File path or URL provided by the user |
| **Processing** | Classify source type based on file extension and URL pattern. Content type is set only if user explicitly specified or if source_type has a clear default; otherwise deferred to Step 2.5 |
| **Output** | Classification result: `source_type` (definitive) + `content_type` (definitive or pending) |
| **Success criteria** | source_type is determined; content_type is either determined or marked pending for Step 2.5 |
| **Validation method** | Rule-based — check that source_type is within the allowed list |
| **Failure handling** | Escalation — ask the user directly if source_type is ambiguous |

**Classification logic:**

```
source_type determination (definitive at Step 1):
  *.pdf                          → pdf
  *.md, *.txt                    → text
  youtube.com/*, youtu.be/*      → youtube
  Other URLs                     → webpage

content_type determination (may be deferred):
  User explicitly specified      → use specified value (definitive)
  source_type is youtube         → media (definitive)
  source_type is webpage         → article (definitive)
  source_type is pdf/text        → pending — resolved at Step 2.5 after content extraction
```

**Conditional branch — when content_type is `book`:**
- Always ask user to provide a book cover image URL
- If user cannot provide one, proceed without it but recommend adding one later via revision loop

#### Step 2: Content Extraction (Ingestion)

| Item | Details |
|------|---------|
| **Executor** | Script (content-ingestion skill) |
| **Input** | Content source + source_type |
| **Processing** | Run the appropriate extraction script for the given source_type |
| **Output** | `/output/<title>/raw_text.md` + (YouTube only) `/output/<title>/timestamps.json` |
| **Success criteria** | Text file is created, is not empty, and contains at least 500 characters |
| **Validation method** | Rule-based — file existence + character count check |
| **Failure handling** | Auto-retry once → on failure, escalation (ask user to provide source text directly) |

**Extraction method by source_type:**

| source_type | Extraction tool | Output files | Notes |
|-------------|----------------|-------------|-------|
| `pdf` | `pdftotext` (poppler) or Python `pdfplumber` | `raw_text.md` | Limited for scanned PDFs without a text layer |
| `text` | Direct file read | `raw_text.md` | Auto-detect encoding |
| `youtube` | Python `youtube-transcript-api` + `yt-dlp` | `raw_text.md` + `timestamps.json` + `source_metadata.json` | Text in md; timestamps in json; video metadata in json |
| `webpage` | Python `trafilatura` or `requests` + `beautifulsoup4` | `raw_text.md` | Extract body text only; strip navigation/ads |

**YouTube transcript extraction details:**

`youtube-transcript-api` is the recommended tool. Rationale:
- No API key required (unlike YouTube Data API v3)
- Supports both manually created and auto-generated subtitles
- Self-contained Python library (`pip install youtube-transcript-api`)

Extraction priority:
1. Manual subtitles (source language)
2. Auto-generated subtitles (source language)
3. No subtitles available → escalation (ask user to provide transcript text directly)

**YouTube dual output:**
- `raw_text.md`: Plain text only (no timestamps) — used for content analysis
- `timestamps.json`: Array of `{ "text": "...", "start": 0.0, "duration": 3.5 }` — used by content-analyzer to generate segment start/end times

**YouTube metadata extraction:**

`youtube-transcript-api` only retrieves subtitles, not video metadata. The extraction script must also collect video metadata separately via page scraping or `yt-dlp --dump-json`:
- Video title, channel name, publish date, duration
- This metadata populates `media_meta` fields, preventing the LLM from fabricating values

The metadata is written to `source_metadata.json` alongside `raw_text.md` and `timestamps.json`.

#### Step 2.5: Resolve Unspecified Parameters

| Item | Details |
|------|---------|
| **Executor** | Main agent (CLAUDE.md) |
| **Input** | Extracted content (`raw_text.md`) + user preferences from Step 0 |
| **Processing** | For any preference the user did not specify in Step 0, auto-determine based on actual extracted content |
| **Output** | Fully resolved parameter set: content_type, layout, theme, library example |
| **Success criteria** | All parameters have values (user-specified or auto-resolved) |
| **Validation method** | Rule-based — all required parameters present |
| **Failure handling** | N/A — agent always resolves with best-effort defaults |

**Auto-resolution rules:**
- **content_type** (if not user-specified): Inspect extracted text — academic structure (abstract, methodology, references) → `paper`; chapter-based 10+ chapters → `book`; short single-topic → `article`; YouTube source → `media`; default → `document`
- **Layout** (if not user-specified): 5+ sections/chapters/segments → Interactive Dashboard; strong narrative flow → Visual Infographic; short key-points → One-Page Executive Summary
- **Theme** (if not user-specified): Deferred to web-content-designer skill's content analysis at Step 4
- **Library example** (if not user-specified): Most recent example matching content_type + layout; if none match, fall back to web-content-designer built-in examples

#### Step 3: Content Analysis & JSON Generation

| Item | Details |
|------|---------|
| **Executor** | **content-analyzer sub-agent** |
| **Input** | `/output/<title>/raw_text.md` + `content_type` + (YouTube) `timestamps.json` + `source_metadata.json` + (book) cover image URL |
| **Processing** | Analyze the source text and structure it into the JSON schema corresponding to the content_type |
| **Output** | `/output/<title>/content_analysis.json` |
| **Success criteria** | JSON is valid, passes JSON Schema validation against the content_type schema, all required fields are present, and summary content is grounded in the source text |
| **Validation method** | JSON Schema validation (structural correctness) + LLM self-check (missing sections, source fidelity) |
| **Failure handling** | Auto-retry up to 2 times (schema errors) → escalation (report to user with error details) |

**The content-analyzer sub-agent is responsible for:**
- Reading the appropriate schema from `json_schemas.md` based on content_type
- Analyzing source text and generating the structured JSON
- For `media` type: using `timestamps.json` to assign approximate start_time/end_time to each segment, and `source_metadata.json` to populate media_meta fields (not inferred by LLM)
- Long-content handling (deterministic threshold-based chunking for books)
- Omitting optional fields when the source material does not contain the corresponding information (anti-hallucination)

**JSON schemas by content_type — 5 separate schemas:**

All schemas are defined in `/.claude/skills/content-ingestion/references/json_schemas.md`. The key structural differences:

**Field optionality principle:** Only `<type>_meta` (title, author, main_theme), `overall_summary.abstract`, and the primary unit array (sections/chapters/segments) are required. All other fields are optional — if the information is not present in the source text, the field must be omitted rather than fabricated. This prevents hallucination of quotes, limitations, methodology sections, etc. that don't exist in the original content.

| content_type | Primary unit field | Unique fields | Omitted fields |
|-------------|-------------------|---------------|----------------|
| `document` | `sections` | `context_and_significance` | — |
| `book` | `chapters` | `cover_image_url`, `field_context` | — |
| `paper` | `sections` | `methodology`, `results`, `discussion`, `references_summary` | — |
| `article` | `sections` | `core_takeaway` | `limitations_and_future_directions` (optional) |
| `media` | `segments` | `start_time`, `end_time`, `source_url`, `total_duration` | `notable_quote`, `limitations_and_future_directions` |

**Common fields across all schemas (required core):**

```json
{
  "<type>_meta": {
    "title": "string (REQUIRED)",
    "author": "string (REQUIRED)",
    "publication_year": "string (optional)",
    "main_theme": "string (REQUIRED)"
  },
  "overall_summary": {
    "abstract": "string (REQUIRED)",
    "keywords": ["string"] // optional, 5-7 items if present
  }
}
```

All other fields below are **optional** — include only when the source material contains the corresponding information.
```

**`document` schema:**
```json
{
  "document_meta": { "title", "author", "publication_year?", "main_theme" },
  "overall_summary": { "abstract", "keywords?" },
  "sections": [
    {
      "section_number": "integer",
      "section_title": "string",
      "summary": "string — 5-6 sentences",
      "key_arguments": ["string"],          // optional
      "key_takeaways_or_insights": ["string"], // optional
      "notable_quote": "string",            // optional — omit if no suitable quote exists
      "keywords": ["string"]               // optional
    }
  ],
  "limitations_and_future_directions": {    // optional — omit if not discussed in source
    "acknowledged_constraints": ["string"],
    "future_research": ["string"]
  },
  "context_and_significance": {             // optional
    "statement": "string — 5-6 sentences"
  }
}
```

**`book` schema:**
```json
{
  "book_meta": { "title", "author", "publication_year?", "main_theme", "cover_image_url?" },
  "overall_summary": { "abstract", "keywords?" },
  "chapters": [
    {
      "chapter_number": "integer",
      "chapter_title": "string",
      "summary": "string — 5-6 sentences",
      "key_arguments": ["string"],          // optional
      "key_takeaways_or_insights": ["string"], // optional
      "notable_quote": "string",            // optional — omit if no suitable quote exists
      "keywords": ["string"]               // optional
    }
  ],
  "limitations_and_future_directions": {    // optional — omit for fiction, narratives, etc.
    "acknowledged_constraints": ["string"],
    "future_research": ["string"]
  },
  "field_context": {                        // optional
    "statement": "string — 5-6 sentences"
  }
}
```

**`paper` schema:**
```json
{
  "paper_meta": { "title", "author", "publication_year?", "main_theme", "journal?", "doi?" },
  "overall_summary": { "abstract", "keywords?" },
  "sections": [
    {
      "section_number": "integer",
      "section_title": "string",
      "summary": "string — 5-6 sentences",
      "key_arguments": ["string"],          // optional
      "key_takeaways_or_insights": ["string"], // optional
      "notable_quote": "string",            // optional
      "keywords": ["string"]               // optional
    }
  ],
  "methodology": {                          // optional — include only if paper has explicit methodology
    "approach": "string",
    "data_sources": ["string"],
    "limitations": ["string"]
  },
  "results": {                              // optional — include only if paper reports results
    "key_findings": ["string"],
    "statistical_highlights": ["string"]
  },
  "discussion": {                           // optional
    "interpretation": "string",
    "implications": ["string"]
  },
  "references_summary": {                   // optional
    "total_count": "integer",
    "key_references": ["string"]
  },
  "limitations_and_future_directions": {    // optional
    "acknowledged_constraints": ["string"],
    "future_research": ["string"]
  }
}
```

**`article` schema:**
```json
{
  "article_meta": { "title", "author", "publication_year?", "main_theme", "source_url?" },
  "overall_summary": { "abstract", "keywords?" },
  "sections": [
    {
      "section_number": "integer",
      "section_title": "string",
      "summary": "string — 3-4 sentences",
      "key_arguments": ["string"],          // optional
      "keywords": ["string"]               // optional
    }
  ],
  "core_takeaway": {                        // optional
    "statement": "string — 2-3 sentences",
    "action_items": ["string"]
  }
}
```

**`media` schema:**
```json
{
  "media_meta": {
    "title": "string (from source_metadata.json)",
    "author": "string (channel name from source_metadata.json)",
    "publication_year": "string (optional, from source_metadata.json)",
    "main_theme": "string",
    "source_url": "string",
    "total_duration": "string (HH:MM:SS, from source_metadata.json)"
  },
  "overall_summary": { "abstract", "keywords?" },
  "segments": [
    {
      "segment_number": "integer",
      "segment_title": "string (agent-generated topic label)",
      "start_time": "string (MM:SS, approximate ±1-2 min)",
      "end_time": "string (MM:SS, approximate ±1-2 min)",
      "summary": "string — 3-5 sentences",
      "key_arguments": ["string"],          // optional
      "keywords": ["string"]               // optional
    }
  ],
  "core_takeaway": {                        // optional
    "statement": "string",
    "action_items": ["string"]
  }
}
```

**Note on media_meta:** Fields marked "from source_metadata.json" are populated from the metadata file extracted in Step 2, not inferred by the LLM. This prevents fabrication of video titles, channel names, and durations.
```

**Long-content handling strategy:**

Use a **deterministic threshold** to decide chunking upfront, rather than attempting full context and falling back on failure.

- **Threshold**: If extracted text exceeds ~80,000 characters (~20,000 tokens), use chunked analysis
- **Below threshold**: Load full source text and generate JSON in one pass
- **Above threshold** (chunked analysis):
  1. Generate a structural outline first (section/chapter boundaries)
  2. Analyze each section/chapter individually, producing JSON fragments
  3. Generate overall_summary and meta information in a separate pass with the outline + all fragment summaries
  4. Merge fragments into the final `content_analysis.json`

#### Step 4: Dashboard Generation

| Item | Details |
|------|---------|
| **Executor** | Main agent — invokes `web-content-designer` skill |
| **Input** | `/output/<title>/content_analysis.json` + `/output/<title>/raw_text.md` + layout + theme + (optional) library example |
| **Processing** | Select reference example from library → generate HTML dashboard following the web-content-designer skill workflow |
| **Output** | `/output/<title>/<title>-dashboard.html` |
| **Success criteria** | HTML file renders correctly in browser, no console errors, mobile-responsive |
| **Validation method** | Rule-based (file exists, size > 0, basic HTML structure check: `<html>`, `<head>`, `<body>` present, no unclosed tags) + LLM self-check (code stability checklist from web-content-designer skill) |
| **Failure handling** | Auto-retry once (fix code errors) → escalation |

**Library example reference logic:**

Before generating the dashboard, select a reference example from the `/library/` folder.

1. Check if user specified a library example in Step 0; if so, use it directly
2. If not specified, read `/library/README.md` to review the registered example list and metadata
3. Select 1 example matching `content_type` + layout; prefer the most recently registered
4. Scan the selected example HTML and **absorb structural and stylistic patterns only** — never copy topic-specific content (text, data, quotes, etc.) from the example
5. If the library is empty, skip this step and reference only the web-content-designer skill's built-in examples

**`/library/README.md` format:**

```markdown
# Dashboard Library

| Filename | content_type | Layout | Source content | Date added | Notes |
|----------|-------------|--------|---------------|------------|-------|
| example-document-01.html | document | dashboard | Analysis of paper X | 2026-03-10 | Strong sidebar navigation pattern |
| example-book-01.html | book | dashboard | Summary of book Y | 2026-03-12 | Cover image + chapter structure reference |
```

**Reference principles (same as web-content-designer skill):**
- Absorb from examples: HTML structure, CSS styling patterns, interaction patterns, component layout, visualization types
- Do NOT absorb from examples: text content, data values, quotes, keywords, color theme (theme is determined fresh based on source text analysis or user preference)

**Information passed to skill invocation:**
- Full analysis JSON content (skill must handle all 5 schema types internally)
- Source text (for theme analysis, unless user specified a theme)
- Layout selection
- User-specified theme (if any)
- If content_type is `book` and a cover image URL is available, instruct placement at the top of the sidebar
- If content_type is `media`, instruct timeline visualization in the dashboard
- Language: always preserve source language

**Schema handling in web-content-designer:**

The web-content-designer skill must understand all 5 JSON schemas and render each appropriately:

| content_type | Rendering differentiation |
|-------------|--------------------------|
| `document` | Standard section-based navigation |
| `book` | Chapter navigation + optional cover image in sidebar |
| `paper` | Academic layout with methodology/results/discussion sections highlighted |
| `article` | Lighter layout, core takeaway prominently displayed |
| `media` | Timeline visualization, segment-based navigation with time markers |

#### Step 5: Revision Loop

| Item | Details |
|------|---------|
| **Executor** | Main agent (CLAUDE.md) — orchestrates between sub-agent and skill |
| **Input** | User's natural language revision request |
| **Processing** | Agent auto-classifies revision type and routes accordingly |
| **Output** | Updated dashboard HTML |
| **Success criteria** | User is satisfied (no explicit limit on iterations) |
| **Validation method** | User confirmation |
| **Failure handling** | If revision produces broken HTML → auto-retry once |

**Revision type auto-classification:**

| Revision type | Detection signal | Action |
|--------------|-----------------|--------|
| **Design-only** | Color, font, spacing, layout changes, visual styling | Edit HTML directly (no JSON regeneration) |
| **Content-only** | Summary inaccurate, section missing, quote wrong | Invoke content-analyzer sub-agent → regenerate JSON → regenerate dashboard |
| **Mixed** | Both design and content changes in one request | Process content changes first, then apply design changes |

**Content revision — sub-agent invocation:**

When a content revision is needed, the main agent invokes the content-analyzer sub-agent with:
- Source text (`raw_text.md`) — full re-load for accuracy
- Existing JSON (`content_analysis.json`)
- Specific revision request from the user

The sub-agent modifies only the relevant portions of the JSON and returns the updated file.

**Design preservation — design override pattern:**

Content and design state are conceptually separate. When a content revision triggers dashboard regeneration:

1. Before regeneration, the agent extracts **design overrides** from the current HTML (CSS custom properties, color values, font choices, layout modifications the user previously requested)
2. These overrides are stored as a `design_overrides` object and passed to the web-content-designer skill alongside the updated JSON
3. The skill applies these overrides on top of the freshly generated dashboard

This ensures design changes survive content regeneration without requiring a separate `render_state.json` file. If extraction fails or produces unexpected results, the agent warns the user and asks them to re-state design preferences.

### 2.3 State Transition Diagram

```
                         ┌──────────────┐
                         │  User Input   │
                         └──────┬───────┘
                                ▼
                    ┌───────────────────────┐
                    │ Step 0: Collect        │
                    │ Preferences            │
                    │ (layout/theme/example) │
                    └──────────┬────────────┘
                               ▼
                    ┌───────────────────────┐
                    │ Step 1: Classify       │
                    │ source_type            │
                    │ [Agent + Script]       │
                    └──────────┬────────────┘
                               │
              ┌────────────────┤ content_type == book (user-specified)?
              │ Yes            │ No
              ▼                ▼
    ┌──────────────────┐       │
    │ Ask user for      │       │
    │ cover image URL   │       │
    └────────┬─────────┘       │
             └────────┬────────┘
                      ▼
            ┌───────────────────────┐
            │ Step 2: Extract Text  │
            │ [Script]              │
            │ (+timestamps.json     │
            │  +source_metadata.json│
            │  for YouTube)         │
            └──────────┬────────────┘
                       │
                       │ Extraction failed? ──Yes──► Retry x1 ──Fail──► Escalation
                       │ No
                       ▼
            ┌───────────────────────┐
            │ Step 2.5: Resolve     │
            │ Unspecified Params    │
            │ (content_type, layout │
            │  library example)     │
            └──────────┬────────────┘
                       │
                       ▼
            ┌───────────────────────┐
            │ Step 3: Analyze &     │
            │ Generate JSON         │
            │ [content-analyzer     │
            │  sub-agent]           │
            └──────────┬────────────┘
                       │
                       │ Schema validation fail? ──► Retry x2
                       │ No
                       ▼
            ┌───────────────────────┐
            │ Step 4: Generate      │
            │ Dashboard             │
            │ [web-content-designer │
            │  skill invocation]    │
            └──────────┬────────────┘
                       │
                       ▼
            ┌───────────────────────┐
            │ Step 5: Revision Loop │◄──────────┐
            │ (present to user)     │            │
            └──────────┬────────────┘            │
                       │                         │
                       │ Revision requested? ────┘
                       │ No (Satisfied)
                       ▼
                  ┌──────────┐
                  │   Done    │
                  └──────────┘
```

---

## 3. Implementation Spec (Structural Overview)

### 3.1 Folder Structure

```
/project-root
├── CLAUDE.md                              # Main agent instructions (orchestrator)
├── /.claude
│   ├── /skills
│   │   └── /content-ingestion
│   │       ├── SKILL.md                   # Content extraction skill instructions
│   │       ├── /scripts
│   │       │   ├── extract_pdf.py         # PDF text extraction
│   │       │   ├── extract_youtube.py     # YouTube transcript + timestamps extraction
│   │       │   ├── extract_webpage.py     # Webpage body text extraction
│   │       │   └── validate_extraction.py # Extraction result validation
│   │       └── /references
│   │           └── json_schemas.md        # All 5 content_type schemas in one file
│   └── /agents
│       └── /content-analyzer
│           └── AGENT.md                   # Sub-agent: JSON generation from source text
├── /library                               # Dashboard reference examples (progressively accumulated)
│   ├── README.md                          # Library index with metadata for each file
│   ├── example-document-01.html           # document type example
│   ├── example-book-01.html               # book type example
│   └── ...                                # High-quality outputs are added over time
├── /output                                # All outputs (per-content subfolders)
│   └── /<title>                           # One folder per content
│       ├── raw_text.md                    # Extracted source text
│       ├── timestamps.json                # (YouTube only) Subtitle timestamp data
│       ├── source_metadata.json           # (YouTube only) Video metadata (title, channel, duration)
│       ├── content_analysis.json          # Structured analysis JSON
│       └── <title>-dashboard.html         # Final dashboard
└── /docs                                  # (optional) Reference documents
    └── prompts.md                         # Archive of original prompts (for reference)
```

### 3.2 Agent Architecture: Main Agent + Sub-agent + Skills

**Main agent** (CLAUDE.md) orchestrates the pipeline. **content-analyzer** sub-agent handles JSON generation.

```
CLAUDE.md (orchestrator)
  ├── invokes: content-ingestion skill (Step 2)
  ├── invokes: content-analyzer sub-agent (Step 3, Step 5 content revisions)
  ├── invokes: web-content-designer skill (Step 4)
  └── directly handles: Step 0, Step 1, Step 5 design revisions, library management
```

**Rationale for sub-agent split:**
- 5 separate JSON schemas + timestamp handling + long-content chunking make the analysis instructions substantial
- Isolating analysis logic into a dedicated sub-agent keeps CLAUDE.md focused on orchestration
- The sub-agent loads schema definitions from `json_schemas.md` only when invoked, optimizing context window usage
- Revision loop requires re-invoking analysis selectively; a dedicated sub-agent makes this clean

### 3.3 CLAUDE.md Key Sections

| Section | Role |
|---------|------|
| **Project overview** | Agent purpose, overall workflow summary |
| **Input handling rules** | Source type classification logic, supported input formats |
| **Preference collection protocol** | What to ask in Step 0, how to present options |
| **Parameter resolution protocol** | Step 2.5 auto-resolution rules for unspecified values (after content extraction) |
| **Library reference rules** | `/library/` example selection criteria, reference principles (absorb structure only, no content copying) |
| **Skill invocation rules** | Conditions and methods for invoking the content-ingestion skill and web-content-designer skill |
| **Sub-agent invocation rules** | When and how to invoke content-analyzer, data to pass, result handling |
| **Revision loop protocol** | Revision type classification, routing logic, design override extraction and preservation |
| **Output management** | File naming conventions, per-content folder structure, intermediate output retention |
| **Library management** | Example registration/update procedures, README.md update rules |

### 3.4 content-analyzer AGENT.md Key Sections

| Section | Role |
|---------|------|
| **Role definition** | JSON generation specialist for 5 content types |
| **Schema reference** | Points to `json_schemas.md`; instructions to select schema based on content_type |
| **Field optionality rules** | Only core fields required; optional fields omitted when source lacks content (anti-hallucination) |
| **Analysis instructions** | Quality criteria per schema, field-by-field guidance |
| **Timestamp handling** | How to use `timestamps.json` for media segment boundary detection |
| **Metadata handling** | How to use `source_metadata.json` for media_meta fields (never infer these from LLM) |
| **Long-content strategy** | Deterministic threshold-based chunking: outline-first when >80K chars |
| **Revision mode** | How to handle partial JSON updates when called for revisions |

### 3.5 Skill File List

| Skill | File | Role | Trigger condition |
|-------|------|------|-------------------|
| **content-ingestion** | `/.claude/skills/content-ingestion/SKILL.md` | Extract text from content sources | On entering Step 2 — after source_type is determined |
| **web-content-designer** (existing) | `/mnt/skills/user/web-content-designer/SKILL.md` | Generate HTML dashboard from JSON + source text | On entering Step 4 — after analysis JSON is generated |

### 3.6 Script File List

| Script | Role | Input | Output |
|--------|------|-------|--------|
| `extract_pdf.py` | Extract text from PDF | PDF file path | `raw_text.md` |
| `extract_youtube.py` | Extract subtitles + timestamps + video metadata from YouTube URL | YouTube URL | `raw_text.md` + `timestamps.json` + `source_metadata.json` |
| `extract_webpage.py` | Extract body text from webpage | Webpage URL | `raw_text.md` |
| `validate_extraction.py` | Validate extraction result | Text file path | Validation result (pass/fail + character count) |

### 3.7 Processing Method Summary by Step

| Step | Executor | Key action |
|------|----------|------------|
| 0. Preference collection | Main agent | Ask layout + theme + library example in one prompt |
| 1. Type classification | Main agent + rules | Determine source_type from URL/extension; content_type set if clear default, otherwise deferred to Step 2.5 |
| 2. Content extraction | Script (skill) | Run extraction script; YouTube produces timestamps.json + source_metadata.json |
| 2.5. Parameter resolution | Main agent | Auto-resolve unspecified content_type, layout, library example based on extracted content |
| 3. Analysis & JSON | Sub-agent (content-analyzer) | Read source text + schema → generate JSON; validated against JSON Schema |
| 4. Dashboard generation | Skill (web-content-designer) | Library example + JSON + source text → HTML dashboard |
| 5. Revision loop | Main agent (orchestrator) | Auto-classify revision type → route to sub-agent or direct HTML edit; preserve design overrides |

### 3.8 Data Transfer Patterns

All intermediate outputs are transferred **file-based**, organized in per-content subfolders under `/output/<title>/`.

| Transfer segment | Method | File(s) |
|-----------------|--------|---------|
| Step 2 → Step 2.5 | File-based | `raw_text.md` (agent inspects content to resolve parameters) |
| Step 2 → Step 3 | File-based | `raw_text.md` + (YouTube) `timestamps.json` + `source_metadata.json` |
| Step 3 → Step 4 | File-based | `content_analysis.json` + `raw_text.md` |
| Step 5 (content revision) | File-based | Source text + existing JSON + revision request → updated JSON → regenerated HTML (with design overrides) |
| Step 5 (design revision) | Inline | Agent edits HTML directly based on user request |

### 3.9 Output File Formats

| Output | Format | Notes |
|--------|--------|-------|
| Extracted text | Markdown (.md) | Preserves source structure via headings; no timestamps |
| Timestamps | JSON (.json) | YouTube only; array of `{text, start, duration}` objects |
| Source metadata | JSON (.json) | YouTube only; video title, channel, duration, publish date from `yt-dlp` |
| Analysis JSON | JSON (.json) | Conforms to content_type-specific schema (1 of 5); validated against JSON Schema |
| Dashboard | HTML (.html) | Single file, CSS/JS embedded (depends on CDN for Tailwind/Chart.js/Paperlogy) |

### 3.10 Library Management

The `/library/` folder serves as a reference repository for high-quality dashboard outputs. As examples accumulate over time, the agent's output quality baseline rises.

**Registration procedure:**
1. User explicitly requests "add to library" after reviewing a completed dashboard
2. Copy `/output/<title>/<title>-dashboard.html` → `/library/<naming-convention>.html`
3. Add metadata to `/library/README.md` (content_type, layout, source content description, date, notes)
4. The agent never auto-registers — registration occurs only by explicit user request

**Naming convention:**
```
example-<content_type>-<sequence>.html
```
Examples: `example-document-01.html`, `example-media-02.html`

**Reference considerations:**
- Library files can be large, so the full file is not loaded into context
- Only the portions needed for structural understanding (HTML skeleton, CSS variables, key component patterns) are selectively scanned
- When user specifies "like example-book-01", that specific file is referenced regardless of content_type match
- When both the `web-content-designer` skill's built-in examples and library examples are available, library examples take priority

---

## 4. Tech Stack & Dependencies

### 4.1 Python Packages

| Package | Purpose | Installation |
|---------|---------|-------------|
| `youtube-transcript-api` | YouTube subtitle + timestamp extraction | `pip install youtube-transcript-api` |
| `yt-dlp` | YouTube video metadata extraction (title, channel, duration, publish date) | `pip install yt-dlp` |
| `pdfplumber` | PDF text extraction | `pip install pdfplumber` |
| `trafilatura` | Webpage body text extraction | `pip install trafilatura` |
| `beautifulsoup4` | HTML parsing (fallback) | `pip install beautifulsoup4` |
| `requests` | HTTP requests | `pip install requests` |

### 4.2 System Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `pdftotext` (poppler) | PDF text extraction (alternative) | System package |

### 4.3 Existing Skill Dependencies

| Skill | Location | External CDN dependencies |
|-------|----------|--------------------------|
| `web-content-designer` | `/mnt/skills/user/web-content-designer/` | Tailwind CSS, Chart.js, Paperlogy font |

---

## 5. Expansion Roadmap

### v2 Considerations (out of v1 scope)
- **dashboard_spec.json normalization layer**: Introduce a canonical renderer input schema that normalizes all 5 content_type schemas into a single structure, decoupling analysis from rendering
- **Multi-source merging**: Combine multiple YouTube videos or documents into a single dashboard
- **Custom schemas**: Allow users to define their own JSON schemas for dashboard structure customization
- **Diagram extraction from PDFs/images**: Extract figures and tables from papers as images and embed them in dashboards
- **Execution logging**: Track pipeline execution time, token usage, and revision count per content

### v3 Considerations
- **Template library**: Allow users to register and reuse dashboard design themes/templates (separate from content examples)
- **Automatic deployment**: Auto-deploy generated dashboards to static hosting
- **Bilingual dashboards**: Display source text and translations side by side in a dual-language dashboard
