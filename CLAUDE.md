# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`vecssy-slim` is a Python Fire CLI that crawls URLs with headless Chromium and ranks fonts by how much they are **actually rendered**, so an oversized `@font-face` stack can be trimmed. It reports what the browser *resolved* (via CDP), not what CSS declared. See `README.md` for user-facing docs.

## Commands

```bash
uv venv --python 3.12 --clear            # create env
uv pip install -e ".[test]"              # editable install + test deps
.venv/bin/playwright install chromium    # one-time browser download (required for crawling)

.venv/bin/python -m pytest               # run all tests
.venv/bin/python -m pytest tests/test_aggregate.py::test_coverage_is_chars_times_size  # single test
uvx hatch test                           # alt test runner

# run the CLI
.venv/bin/vecssy-slim --url https://example.com --json_report r.json --md_report r.md
.venv/bin/vecssy-slim --list_urls examples/urls.txt --md_report site.md
```

Versioning is `hatch-vcs` from git tags (e.g. `v0.1.0`) → generates `src/vecssy_slim/__version__.py` (gitignored). The package needs a git repo and at least one tag to build cleanly. `./publish.sh` runs `uvx hatch clean; uvx gitnextver .; uv build; uv publish` (the tag bump must precede the build since the version derives from it).

## Architecture

The data flow is a one-way pipeline; each module is pure except `analyzer`, which is the only part that touches a browser:

- **`models.py`** — `FontRecord` (one rendered text run: family, size, weight, style, stretch, chars; `.coverage = chars × size`), and the aggregated `StyleStat` / `FamilyStat` / `UrlReport` dataclasses with `to_dict()` for JSON.
- **`analyzer.py`** — Playwright + CDP. Per URL: `DOM.getDocument` (depth -1, pierce) → recursive `_walk` over text nodes (incl. iframes/shadow roots) → per text node `CSS.getPlatformFontsForNode` (resolved family + glyph count) paired with the parent element's `CSS.getComputedStyleForNode` (size/weight/style/stretch, cached per element). Emits `FontRecord`s. Playwright is imported lazily inside the function so tests and `--help` don't need a browser. One failing URL is captured as `UrlReport.error`, never raised.
- **`aggregate.py`** — pure folding. `build_url_report` groups records by `(family, weight, style, stretch)` accumulating chars + coverage, attaches styles to families, sorts everything by coverage desc. `merge_reports` re-folds per-URL `StyleStat`s into the site-wide aggregate (skipping errored URLs).
- **`report.py`** — `build_payload` (assembles the `{aggregate, urls}` document), `write_json` / `write_markdown` / `render_markdown`. Output always has an `aggregate` plus per-URL breakdowns.
- **`__main__.py`** — Fire CLI + console entry point. Fire target `analyze(...)`; `_resolve_urls` merges `--url` + `--list_urls` (de-duped, `#` comments stripped). Validation raises `fire.core.FireError` (not plain exceptions) so Fire prints its own usage string and exits cleanly — don't add custom help/usage text. When `--list_urls` is given without `--json_report`/`--md_report`, reports default to the list file's path with `.json`/`.md` extensions. This module *is* the `vecssy-slim` console entry point (`main` → `fire.Fire(analyze)`) and runs via `python -m vecssy_slim`.

**Coverage is the core invariant:** `coverage = Σ (rendered glyphs × font-size px)`. Glyph counts come from CDP (real rendered glyphs), not `text.length`. When changing aggregation, keep `aggregate.py` pure and browser-free — the test suite covers it without Chromium; only live crawling needs the browser.

## CodeGraph

`.codegraph/` exists. Prefer `codegraph_search`, `codegraph_callers`/`codegraph_callees`, and `codegraph_impact` over raw file scans for exploration.
