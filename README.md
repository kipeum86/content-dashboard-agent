<div align="center">

# Content Dashboard Agent

**Turn any content source into a polished, interactive HTML dashboard.**

PDFs · Text files · YouTube videos · Webpages · NotebookLM notebooks

[한국어 README](README.ko.md)

<br>

<img src="https://img.shields.io/badge/powered_by-Claude_Code-blueviolet?style=for-the-badge" alt="Powered by Claude Code">
<img src="https://img.shields.io/badge/output-Single_File_HTML-orange?style=for-the-badge" alt="Single File HTML">
<img src="https://img.shields.io/badge/sources-5_types-green?style=for-the-badge" alt="5 Source Types">

</div>

<br>

> **Note:** This is not a standalone app or CLI. It is the working repository for a **Claude Code agent system** — orchestration instructions, extraction scripts, analysis rules, and dashboard generation references.

---

## Live Examples

See what Content Dashboard Agent produces. Each link opens a fully generated, single-file HTML dashboard.

<table>
<tr>
<th width="150">Content Type</th>
<th width="300">English</th>
<th width="300">한국어</th>
</tr>
<tr>
<td><strong>📖 Book Summary</strong></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/JoKJEYX">View Dashboard →</a></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/azvzbxE">대시보드 보기 →</a></td>
</tr>
<tr>
<td><strong>🎬 YouTube Video</strong></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/jEbErrj">View Dashboard →</a></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/ZYpEKRX">대시보드 보기 →</a></td>
</tr>
<tr>
<td><strong>📄 Research Paper</strong></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/MYwNmMb">View Dashboard →</a></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/emNqWwv">대시보드 보기 →</a></td>
</tr>
<tr>
<td><strong>📊 Comprehensive</strong></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/JodqRME">View Dashboard →</a></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/Eajzgoy">대시보드 보기 →</a></td>
</tr>
<tr>
<td><strong>⚖️ Case Law</strong></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/qEdgWgO">View Dashboard →</a></td>
<td><a href="https://codepen.io/Kipeum-Lee/full/xbGMKMb">대시보드 보기 →</a></td>
</tr>
</table>

---

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Content    │     │   Extract   │     │   Analyze   │     │  Generate   │
│   Source     │────▶│   Text      │────▶│   to JSON   │────▶│  Dashboard  │
│             │     │             │     │             │     │             │
│ PDF/YouTube │     │ raw_text.md │     │ Structured  │     │ Single-file │
│ Web/Text/NLM│     │ + metadata  │     │ analysis    │     │ HTML output │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ▼
                                                            ┌─────────────┐
                                                            │  Revision   │
                                                            │    Loop     │
                                                            │ "Make it    │
                                                            │  darker..." │
                                                            └─────────────┘
```

### The Pipeline

| Step | What happens | Who does it |
|:----:|--------------|-------------|
| **1** | You provide a source (file or URL) and pick a layout | You |
| **2** | Text is extracted and normalized | `content-ingestion` scripts |
| **3** | Content type, theme, and layout are auto-resolved | Orchestrator (`CLAUDE.md`) |
| **4** | Source is analyzed into structured JSON | `content-analyzer` sub-agent |
| **5** | JSON is rendered into an interactive dashboard | `web-content-designer` skill |
| **6** | You request changes in plain language | Revision loop (unlimited) |

---

## Supported Sources

| Source | Input | What gets extracted |
|--------|-------|---------------------|
| **PDF** | Local file in `input/` | Full text (best with embedded text layer) |
| **Text** | `.md` or `.txt` in `input/` | Direct content, language preserved |
| **YouTube** | URL | Transcript + timestamps + video metadata |
| **Webpage** | URL | Article body, boilerplate stripped |
| **NotebookLM** | Notebook URL | Source fulltexts + Study Guide via notebooklm-py |

---

## Content-Aware Output

The dashboard adapts its structure based on what you feed it:

| Content Type | Optimized For |
|:------------:|---------------|
| `book` | Chapter navigation, cover imagery, section-by-section analysis |
| `paper` | Abstract, methodology, results, discussion structure |
| `media` | Timestamped segments, video metadata, "Watch Original" button |
| `article` | Editorial flow, lighter structure |
| `document` | Flexible general-purpose layout |

Three layout options: **Interactive Dashboard** (sectioned navigation) · **Visual Infographic** (scroll-based storytelling) · **One-Page Executive Summary** (compact key points)

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) access

### Install

```bash
git clone https://github.com/your-username/content-dashboard-agent.git
cd content-dashboard-agent

python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### Run

1. Place a source file in `input/`, or have a URL ready
2. Open the project in Claude Code
3. Ask the agent:

```
Make a dashboard from input/my-report.pdf
```
```
Create a dashboard from this YouTube video: https://www.youtube.com/watch?v=...
```
```
Make a dashboard from my NotebookLM notebook: https://notebooklm.google.com/notebook/...
```

4. Pick a layout when prompted
5. Review the output in `output/<title>/`
6. Request revisions in natural language — no limit

### NotebookLM Setup (optional)

Only needed if you use NotebookLM notebooks as a source:

```bash
pip install "notebooklm-py[browser]"
python -m playwright install chromium
notebooklm login
```

> **Windows:** If `notebooklm` is not recognized, use the full path:
> `C:\Users\<you>\AppData\Local\Python\pythoncore-3.14-64\Scripts\notebooklm.exe login`

---

## Output Structure

Each processed source generates a folder under `output/`:

```
output/<title>/
├── raw_text.md               # Extracted source text
├── timestamps.json           # YouTube only
├── source_metadata.json      # YouTube / NotebookLM
├── notebooklm_report.md      # NotebookLM only
├── content_analysis.json     # Structured analysis
└── <title>-dashboard.html    # Final dashboard
```

---

## Repository Structure

```
.
├── CLAUDE.md                           # Orchestrator instructions
├── README.md
├── requirements.txt
├── input/                              # Drop source files here
├── output/                             # Generated artifacts
├── library/                            # Reference dashboard examples
│   ├── README.md
│   └── *.html
└── .claude/
    ├── agents/
    │   └── content-analyzer/AGENT.md   # Analysis sub-agent spec
    └── skills/
        ├── content-ingestion/          # Extraction scripts
        │   ├── SKILL.md
        │   ├── references/json_schemas.md
        │   └── scripts/
        ├── notebooklm-ingestion/       # NotebookLM extraction
        │   ├── SKILL.md
        │   └── scripts/
        └── web-content-designer/       # Dashboard rendering
            └── SKILL.md
```

---

## Library System

The `library/` folder stores approved dashboard examples. Future runs reference these for layout and styling patterns — not content.

- Registration is **user-initiated** only ("add to library")
- The agent absorbs structure and interaction patterns, never content
- Media dashboards prefer media-type references when available

See [library/README.md](library/README.md) for the full catalog and naming convention.

---

## Limitations

- Agent-driven workflow — no standalone CLI for the full pipeline
- One source at a time (v1)
- PDF quality depends on embedded text layers
- YouTube requires available transcripts
- Dashboards may load frontend assets from external CDNs
- `input/` and `output/` are gitignored

---

## Why This Exists

Content-heavy work often breaks down because source material, analysis, and presentation live in different tools. Content Dashboard Agent collapses that into one repeatable workflow — extract, analyze, render, revise — all inside Claude Code.

---

<div align="center">

**[See Live Examples](#live-examples)** · **[한국어 README](README.ko.md)**

</div>
