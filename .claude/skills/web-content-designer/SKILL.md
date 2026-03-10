# Web Content Designer Skill

> Generates professional, interactive HTML dashboards from structured JSON content analysis data.

## Purpose

This skill handles Step 4 (Dashboard Generation) of the content dashboard pipeline. It takes a content analysis JSON and source text, then produces a single-file HTML dashboard.

## Input

| Parameter | Description | Required |
|-----------|-------------|----------|
| `content_analysis.json` | Structured JSON conforming to one of 5 content type schemas | Yes |
| `raw_text.md` | Source text for theme analysis | Yes |
| Layout | `dashboard` / `infographic` / `summary` | Yes |
| Theme | Color theme preference or "auto" | No |
| Library example HTML | Reference example for structural patterns | No |
| Design overrides | CSS overrides from previous revision (if content regeneration) | No |

## Output

Single HTML file: `<title>-dashboard.html`
- All CSS embedded in `<style>` tags
- All JS embedded in `<script>` tags
- External CDN dependencies only: Tailwind CSS, Chart.js, Paperlogy font

## Layout Types

### Interactive Dashboard
- Best for: 5+ sections/chapters/segments
- Features: Sidebar navigation, section cards, expandable content, keyword tags, search/filter
- Schema-specific rendering per content type

### Visual Infographic
- Best for: Strong narrative flow, visual storytelling
- Features: Vertical scroll-based layout, visual hierarchy, key stats highlighted, minimal interactivity

### One-Page Executive Summary
- Best for: Short content, key-points focus
- Features: Single page, key findings prominently displayed, compact layout

## Content Type Rendering

Each content type should be rendered with appropriate differentiation:

### document
- Standard section-based navigation
- Sidebar with section list
- Each section card shows: summary, key arguments, takeaways, notable quote, keywords

### book
- Chapter navigation (numbered chapters in sidebar)
- Cover image at top of sidebar (if `cover_image_url` available)
- Each chapter card shows: summary, key arguments, takeaways, notable quote, keywords

### paper
- Academic layout
- Methodology, results, discussion sections get special highlighted panels
- References summary section
- Sidebar with section list + special sections

### article
- Lighter, cleaner layout
- Core takeaway prominently displayed at top or as a highlighted callout
- Fewer decorative elements, focus on readability

### media
- Timeline visualization (horizontal or vertical timeline with time markers)
- Segment-based navigation with start_time/end_time displayed
- Source URL linked for easy access to original video
- Total duration displayed in header

## Theme System

### Auto theme (default):
Analyze the source text content and select an appropriate color palette:
- Academic/technical → Cool blues and grays
- Creative/design → Vibrant, modern palette
- Business/finance → Professional dark theme
- Science/nature → Green/teal tones
- Technology → Dark theme with accent colors

### User-specified theme:
Apply the user's stated theme preference (e.g., "dark mode", "blue and white", "warm colors").

## CDN Dependencies

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Chart.js (if data visualization needed) -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Paperlogy Font (Korean support) -->
<link href="https://cdn.jsdelivr.net/gh/nicepayments/nicepay-paperlogy@main/paperlogy.css" rel="stylesheet">
```

## HTML Generation Guidelines

### Structure
```html
<!DOCTYPE html>
<html lang="[source-language]">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[content title] — Dashboard</title>
    <!-- CDN links -->
    <style>/* All custom CSS here */</style>
</head>
<body>
    <!-- Sidebar/Navigation -->
    <!-- Main Content Area -->
    <!-- Footer -->
    <script>/* All JS here */</script>
</body>
</html>
```

### Quality Checklist
- [ ] Valid HTML5 structure
- [ ] Mobile-responsive (works on mobile, tablet, desktop)
- [ ] No console errors
- [ ] All sections from JSON rendered
- [ ] Source language preserved in all text content
- [ ] Smooth scroll navigation between sections
- [ ] Sidebar highlights active section on scroll
- [ ] All interactive elements have hover/focus states
- [ ] Color contrast meets WCAG AA standards
- [ ] Print-friendly styles (optional)

### Anti-patterns to avoid
- Do NOT hardcode content from library examples — only absorb structure/style
- Do NOT use inline styles when Tailwind classes suffice
- Do NOT create multiple HTML files — everything in one file
- Do NOT omit sections from the JSON — render all content
- Do NOT change the language of the content

## Library Example Reference

When a library example is provided:
1. Scan the example HTML for structural patterns (layout, component arrangement)
2. Note CSS styling approach (custom properties, color scheme structure)
3. Identify interaction patterns (navigation, expand/collapse, scroll behavior)
4. Apply these patterns to the new dashboard with fresh content and theme
5. **Never copy text content, data, or quotes from the example**

## Design Overrides (Revision Support)

When `design_overrides` are provided (from a content revision that triggers regeneration):
1. Generate the dashboard fresh from the updated JSON
2. Apply the design overrides on top:
   - CSS custom properties (--primary-color, --bg-color, etc.)
   - Font family changes
   - Layout modifications
   - Any user-requested visual changes from previous revisions
3. This preserves design continuity across content regeneration cycles
