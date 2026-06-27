# this_file: src/vecssy_slim/report.py
"""Render coverage reports as JSON and Markdown."""

from __future__ import annotations

import json
from pathlib import Path

from vecssy_slim.models import UrlReport, style_label


def build_payload(per_url: list[UrlReport], aggregate: UrlReport) -> dict:
    """Assemble the full result document (used for the JSON report).

    Per-URL reports carry their `styles`; the aggregate also carries `families`.
    """
    return {
        "urls": [r.to_dict() for r in per_url],
        "aggregate": aggregate.to_dict(include_families=True),
    }


def write_json(path: str | Path, per_url: list[UrlReport], aggregate: UrlReport) -> None:
    payload = build_payload(per_url, aggregate)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _totals(report: UrlReport) -> list[str]:
    return [
        f"- Total rendered glyphs: **{report.total_chars:,}**",
        f"- Total coverage (glyphs x px): **{report.total_coverage:,.0f}**",
        "",
    ]


def _style_table(report: UrlReport) -> list[str]:
    """A coverage-ranked table of (family, weight, style, stretch) rows."""
    if report.error:
        return [f"> **Error:** {report.error}", ""]
    lines = _totals(report)
    lines += [
        "| Family | Weight | Style | Stretch | Glyphs | Coverage |",
        "| --- | ---: | :-: | --- | ---: | ---: |",
    ]
    for st in report.styles:
        lines.append(
            f"| {st.family} | {st.weight} | {style_label(st.style)} | {st.stretch} "
            f"| {st.chars:,} | {st.coverage:,.0f} |"
        )
    lines.append("")
    return lines


def _family_table(report: UrlReport) -> list[str]:
    """A coverage-ranked table of families (styles summed)."""
    lines = [
        "| Family | Glyphs | Coverage |",
        "| --- | ---: | ---: |",
    ]
    for fam in report.families:
        lines.append(f"| {fam.family} | {fam.chars:,} | {fam.coverage:,.0f} |")
    lines.append("")
    return lines


def render_markdown(per_url: list[UrlReport], aggregate: UrlReport) -> str:
    lines = [
        "# Font coverage report",
        "",
        "_Coverage = rendered glyphs x font-size (px), summed per font. "
        "Higher coverage means the font occupies more visual area; low-coverage "
        "`@font-face` declarations are candidates for removal or subsetting. "
        "Style is `n` (normal) or `i` (italic)._",
        "",
    ]
    n = len(per_url)
    for report in per_url:
        lines.append(f"## {report.url}")
        lines.append("")
        lines += _style_table(report)
    lines.append(f"## Aggregate — styles ({n} URL(s))")
    lines.append("")
    lines += _style_table(aggregate)
    lines.append(f"## Aggregate — families ({n} URL(s))")
    lines.append("")
    lines += _family_table(aggregate)
    return "\n".join(lines)


def write_markdown(path: str | Path, per_url: list[UrlReport], aggregate: UrlReport) -> None:
    Path(path).write_text(render_markdown(per_url, aggregate), encoding="utf-8")
