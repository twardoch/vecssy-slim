# Changelog

All notable changes to `vecssy-slim` are documented here.

## [Unreleased]

### Added
- Ruff and mypy configuration in `pyproject.toml` for linting, formatting, and type checking.
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) testing Python 3.10–3.12 with ruff, mypy, and pytest.
- Jekyll docs site (`docs/`) with install guide, CLI reference, output schema, and coverage metric explanation.

## [1.0.0] — 2026-01-01

### Added
- Initial release.
- Playwright + CDP crawler: walks the full DOM (iframes, shadow roots) and collects resolved font family, glyph count, size, weight, style, and stretch per text node.
- Coverage metric: `glyphs × font-size (px)` aggregated per `(family, weight, style, stretch)` style group and rolled up per family.
- JSON and Markdown report output with per-URL tables and a site-wide aggregate.
- Rich terminal summary of top families by coverage.
- Fire CLI (`vecssy-slim`) with `--url`, `--list_urls`, `--json_report`, `--md_report`, `--timeout`, `--wait_until`, `--headless`, `--top`, `--verbose`.
- Pure aggregation layer (`aggregate.py`, `models.py`, `report.py`) with full unit test coverage — no browser required for tests.
