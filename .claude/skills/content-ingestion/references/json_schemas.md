# Content Analysis JSON Schemas

> Defines the 5 content type schemas used by the content-analyzer sub-agent.

## Field Optionality Principle

Only these fields are **required**:
- `<type>_meta.title`, `<type>_meta.author`, `<type>_meta.main_theme`
- `overall_summary.abstract`
- The primary unit array (`sections`, `chapters`, or `segments`)

All other fields are **optional**. If the source material does not contain the corresponding information, the field **must be omitted** rather than fabricated. This prevents hallucination.

---

## Common Fields (All Schemas)

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
    "keywords": ["string"]  // optional, 5-7 items if present
  }
}
```

---

## 1. Document Schema (`content_type: document`)

```json
{
  "document_meta": {
    "title": "string (REQUIRED)",
    "author": "string (REQUIRED)",
    "publication_year": "string (optional)",
    "main_theme": "string (REQUIRED)"
  },
  "overall_summary": {
    "abstract": "string (REQUIRED)",
    "keywords": ["string"]  // optional, 5-7 items
  },
  "sections": [
    {
      "section_number": "integer (REQUIRED)",
      "section_title": "string (REQUIRED)",
      "summary": "string — 5-6 sentences (REQUIRED)",
      "key_arguments": ["string"],              // optional
      "key_takeaways_or_insights": ["string"],  // optional
      "notable_quote": "string",                // optional — omit if no suitable quote exists
      "keywords": ["string"]                    // optional
    }
  ],
  "limitations_and_future_directions": {        // optional — omit if not discussed in source
    "acknowledged_constraints": ["string"],
    "future_research": ["string"]
  },
  "context_and_significance": {                 // optional
    "statement": "string — 5-6 sentences"
  }
}
```

---

## 2. Book Schema (`content_type: book`)

```json
{
  "book_meta": {
    "title": "string (REQUIRED)",
    "author": "string (REQUIRED)",
    "publication_year": "string (optional)",
    "main_theme": "string (REQUIRED)",
    "cover_image_url": "string (optional)"
  },
  "overall_summary": {
    "abstract": "string (REQUIRED)",
    "keywords": ["string"]  // optional, 5-7 items
  },
  "chapters": [
    {
      "chapter_number": "integer (REQUIRED)",
      "chapter_title": "string (REQUIRED)",
      "summary": "string — 5-6 sentences (REQUIRED)",
      "key_arguments": ["string"],              // optional
      "key_takeaways_or_insights": ["string"],  // optional
      "notable_quote": "string",                // optional — omit if no suitable quote exists
      "keywords": ["string"]                    // optional
    }
  ],
  "limitations_and_future_directions": {        // optional — omit for fiction, narratives, etc.
    "acknowledged_constraints": ["string"],
    "future_research": ["string"]
  },
  "field_context": {                            // optional
    "statement": "string — 5-6 sentences"
  }
}
```

---

## 3. Paper Schema (`content_type: paper`)

```json
{
  "paper_meta": {
    "title": "string (REQUIRED)",
    "author": "string (REQUIRED)",
    "publication_year": "string (optional)",
    "main_theme": "string (REQUIRED)",
    "journal": "string (optional)",
    "doi": "string (optional)"
  },
  "overall_summary": {
    "abstract": "string (REQUIRED)",
    "keywords": ["string"]  // optional, 5-7 items
  },
  "sections": [
    {
      "section_number": "integer (REQUIRED)",
      "section_title": "string (REQUIRED)",
      "summary": "string — 5-6 sentences (REQUIRED)",
      "key_arguments": ["string"],              // optional
      "key_takeaways_or_insights": ["string"],  // optional
      "notable_quote": "string",                // optional
      "keywords": ["string"]                    // optional
    }
  ],
  "methodology": {                              // optional — include only if paper has explicit methodology
    "approach": "string",
    "data_sources": ["string"],
    "limitations": ["string"]
  },
  "results": {                                  // optional — include only if paper reports results
    "key_findings": ["string"],
    "statistical_highlights": ["string"]
  },
  "discussion": {                               // optional
    "interpretation": "string",
    "implications": ["string"]
  },
  "references_summary": {                       // optional
    "total_count": "integer",
    "key_references": ["string"]
  },
  "limitations_and_future_directions": {        // optional
    "acknowledged_constraints": ["string"],
    "future_research": ["string"]
  }
}
```

---

## 4. Article Schema (`content_type: article`)

```json
{
  "article_meta": {
    "title": "string (REQUIRED)",
    "author": "string (REQUIRED)",
    "publication_year": "string (optional)",
    "main_theme": "string (REQUIRED)",
    "source_url": "string (optional)"
  },
  "overall_summary": {
    "abstract": "string (REQUIRED)",
    "keywords": ["string"]  // optional, 5-7 items
  },
  "sections": [
    {
      "section_number": "integer (REQUIRED)",
      "section_title": "string (REQUIRED)",
      "summary": "string — 3-4 sentences (REQUIRED)",
      "key_arguments": ["string"],              // optional
      "keywords": ["string"]                    // optional
    }
  ],
  "core_takeaway": {                            // optional
    "statement": "string — 2-3 sentences",
    "action_items": ["string"]
  }
}
```

---

## 5. Media Schema (`content_type: media`)

```json
{
  "media_meta": {
    "title": "string (REQUIRED — from source_metadata.json)",
    "author": "string (REQUIRED — channel name from source_metadata.json)",
    "publication_year": "string (optional — from source_metadata.json)",
    "main_theme": "string (REQUIRED)",
    "source_url": "string (REQUIRED)",
    "total_duration": "string (REQUIRED — HH:MM:SS, from source_metadata.json)"
  },
  "overall_summary": {
    "abstract": "string (REQUIRED)",
    "keywords": ["string"]  // optional, 5-7 items
  },
  "segments": [
    {
      "segment_number": "integer (REQUIRED)",
      "segment_title": "string (REQUIRED — agent-generated topic label)",
      "start_time": "string (REQUIRED — MM:SS, approximate ±1-2 min)",
      "end_time": "string (REQUIRED — MM:SS, approximate ±1-2 min)",
      "summary": "string — 3-5 sentences (REQUIRED)",
      "key_arguments": ["string"],              // optional
      "keywords": ["string"]                    // optional
    }
  ],
  "core_takeaway": {                            // optional
    "statement": "string",
    "action_items": ["string"]
  }
}
```

### Media Schema Notes:
- Fields marked "from source_metadata.json" are populated from the metadata file extracted in Step 2, **not** inferred by the LLM
- `start_time` and `end_time` are approximate (±1-2 minutes tolerance)
- Segment titles are generated by the agent based on topic analysis
- `notable_quote` and `limitations_and_future_directions` are not part of the media schema
