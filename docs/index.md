---
layout: default
title: vecssy-slim
---

# vecssy-slim

Crawl one or more URLs and find out which fonts are **actually rendered** — then rank them by how much of the page they occupy, so you can slim down a bloated `@font-face` stack with confidence.

## Install

```bash
uv venv --python 3.12
uv pip install vecssy-slim
playwright install chromium
```

## Quick start

```bash
# Analyze one page and write both reports
vecssy-slim --url https://example.com --json_report report.json --md_report report.md

# Analyze many URLs from a file
vecssy-slim --list_urls urls.txt --md_report site-fonts.md
```

## How it works

`vecssy-slim` uses Playwright + Chrome DevTools Protocol to:

1. Load each URL in a headless Chromium page.
2. Walk the full DOM (including iframes and shadow roots).
3. Call `CSS.getPlatformFontsForNode` for the resolved family and glyph count per text node.
4. Call `CSS.getComputedStyleForNode` on parent elements for `font-size`, `weight`, `style`, and `stretch`.
5. Compute **coverage** = glyphs × font-size (px), then aggregate and rank.

## Coverage metric

```
coverage(font) = Σ over every rendered run [ rendered glyphs × font-size in px ]
```

A font used once in a `72px` headline outranks one buried in a `10px` footnote repeated everywhere. Any `@font-face` family or weight that never appears as a resolved font is a safe candidate for removal or subsetting.

## CLI options

| Flag | Default | Meaning |
|---|---|---|
| `--url` | – | A single URL to analyze. |
| `--list_urls` | – | Path to a file with one URL per line (`#` comments allowed). |
| `--json_report` | – | Write the full JSON report here. |
| `--md_report` | – | Write a Markdown report here. |
| `--timeout` | `30.0` | Per-page navigation timeout, seconds. |
| `--wait_until` | `networkidle` | Playwright load state: `load`, `domcontentloaded`, or `networkidle`. |
| `--headless` | `True` | Run Chromium headless; `--noheadless` to watch. |
| `--top` | `15` | Families shown in the terminal summary. |
| `--verbose` | `False` | Debug logging. |

## Output shape

```json
{
  "urls": [
    {
      "url": "https://example.com",
      "error": null,
      "total_chars": 12345,
      "total_coverage": 234567.0,
      "styles": [
        {"family": "Inter", "weight": "400", "style": "n",
         "stretch": "100%", "chars": 6000, "coverage": 120000.0}
      ]
    }
  ],
  "aggregate": {
    "url": "ALL URLS",
    "styles": [...],
    "families": [
      {"family": "Inter", "chars": 8000, "coverage": 180000.0}
    ]
  }
}
```

`font-style` is reported as `n` (normal) or `i` (italic/oblique).

## License

MIT — [Adam Twardoch](https://github.com/twardoch)
