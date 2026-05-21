# vecssy-slim

Crawl one or more URLs and find out which fonts are **actually rendered** — then rank them by how much of the page they occupy, so you can slim down a bloated `@font-face` stack with confidence.

Most font tools report what your CSS *declares*. `vecssy-slim` reports what the browser *resolved*: for every text node on the page it asks Chromium (via the DevTools Protocol) which font family was really used and how many glyphs it drew, then pairs that with the text's computed size, weight, style, and stretch.

## Why coverage, not just counts

A font used once in a giant `72px` headline matters more than one buried in a `10px` footnote repeated everywhere. So the ranking metric is **coverage**:

```
coverage(font) = Σ over every rendered run [ rendered glyphs × font-size in px ]
```

It approximates the visual area a font occupies. Stats are reported per **font-weight / font-style / font-stretch** group, and then aggregated **per family**. Any `@font-face` family or weight that never shows up as a *rendered* font is dead weight — a safe candidate for removal or subsetting.

## Install

```bash
uv venv --python 3.12
uv pip install -e ".[test]"
playwright install chromium   # one-time: download the headless browser
```

## Usage

`vecssy-slim` is a [Fire](https://github.com/google/python-fire) CLI. Give it either a single `--url` or a `--list_urls` file (one URL per line; `#` comments allowed). Both report outputs are optional — without them you still get a terminal summary.

```bash
# Single URL, write both reports
vecssy-slim --url https://example.com \
    --json_report report.json \
    --md_report report.md

# Many URLs from a file
vecssy-slim --list_urls urls.txt --md_report site-fonts.md

# With --list_urls and no report flags, reports are written next to the
# list file: urls.txt -> urls.json + urls.md
vecssy-slim --list_urls urls.txt

# Combine: a single URL plus a list
vecssy-slim --url https://example.com --list_urls more.txt
```

Run `vecssy-slim --help` for the full, Fire-generated usage.

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--url` | – | A single URL to analyze. |
| `--list_urls` | – | Path to a file with one URL per line (`#` comments allowed). |
| `--json_report` | – | Write the full JSON report here. With `--list_urls` and no value, defaults to the list file with a `.json` extension. |
| `--md_report` | – | Write a Markdown report here. With `--list_urls` and no value, defaults to the list file with a `.md` extension. |
| `--timeout` | `30.0` | Per-page navigation timeout, seconds. |
| `--wait_until` | `networkidle` | Playwright load state: `load`, `domcontentloaded`, or `networkidle`. |
| `--headless` | `True` | Run Chromium headless; `--noheadless` to watch it. |
| `--top` | `15` | Families shown in the terminal summary. |
| `--verbose` | `False` | Debug logging. |

You can provide `--url` and `--list_urls` together; URLs are de-duplicated in order.

## Output

Both reports contain an **aggregate** (all URLs combined) and a **per-URL** breakdown. Each breakdown lists families sorted by coverage descending, and within each family the per-style rows (weight / style / stretch), also sorted by coverage.

JSON shape:

```json
{
  "aggregate": {
    "url": "ALL URLS",
    "error": null,
    "total_chars": 12345,
    "total_coverage": 234567.0,
    "families": [
      {
        "family": "Inter",
        "chars": 8000,
        "coverage": 180000.0,
        "styles": [
          {"family": "Inter", "weight": "400", "style": "normal",
           "stretch": "100%", "chars": 6000, "coverage": 120000.0}
        ]
      }
    ]
  },
  "urls": [ { "url": "https://example.com", "...": "..." } ]
}
```

URLs that fail to load are captured (not fatal): the run continues and the failed URL appears with an `error` field.

## How it works

1. **Crawl** each URL in a headless Chromium page (Playwright).
2. **Walk the DOM** — including iframes and shadow roots — for non-empty text nodes.
3. For each text node, call CDP `CSS.getPlatformFontsForNode` for the **resolved** family and glyph count, and `CSS.getComputedStyleForNode` on its parent for **size / weight / style / stretch**.
4. **Aggregate** into coverage = `glyphs × size`, grouped per style and per family, sorted descending.
5. **Report** as JSON and/or Markdown, plus a terminal summary.

This catches fonts loaded dynamically (Adobe Fonts, async Google Fonts) that static CSS parsers miss, because it reads what the browser drew rather than what the stylesheet declared.

## Development

```bash
uvx hatch test          # or: .venv/bin/python -m pytest
```

The aggregation and reporting logic is pure and fully unit-tested without a browser; only live crawling needs Chromium.

## License

MIT
