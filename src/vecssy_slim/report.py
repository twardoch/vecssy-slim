# this_file: src/vecssy_slim/report.py
"""Render coverage reports as JSON and Markdown."""

from __future__ import annotations

import json
from pathlib import Path

from vecssy_slim.models import UrlReport


def build_payload(per_url: list[UrlReport], aggregate: UrlReport) -> dict:
    """Assemble the full result document (used for the JSON report)."""
    return {
        "aggregate": aggregate.to_dict(),
        "urls": [r.to_dict() for r in per_url],
    }


def write_json(path: str | Path, per_url: list[UrlReport], aggregate: UrlReport) -> None:
    payload = build_payload(per_url, aggregate)
    Path(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _render_report(report: UrlReport, heading: str) -> list[str]:
    lines = [f"## {heading}", ""]
    if report.error:
        lines += [f"> **Error:** {report.error}", ""]
        return lines
    lines += [
        f"- Total rendered glyphs: **{report.total_chars:,}**",
        f"- Total coverage (glyphs x px): **{report.total_coverage:,.0f}**",
        "",
        "| Family | Weight | Style | Stretch | Glyphs | Coverage |",
        "| --- | ---: | --- | --- | ---: | ---: |",
    ]
    for fam in report.families:
        lines.append(
            f"| **{fam.family}** | | | | **{fam.chars:,}** | **{fam.coverage:,.0f}** |"
        )
        for st in fam.styles:
            lines.append(
                f"| {st.family} | {st.weight} | {st.style} | {st.stretch} "
                f"| {st.chars:,} | {st.coverage:,.0f} |"
            )
    lines.append("")
    return lines


def render_markdown(per_url: list[UrlReport], aggregate: UrlReport) -> str:
    lines = [
        "# Font coverage report",
        "",
        "_Coverage = rendered glyphs x font-size (px), summed per font. "
        "Higher coverage means the font occupies more visual area; low-coverage "
        "`@font-face` declarations are candidates for removal or subsetting._",
        "",
    ]
    lines += _render_report(aggregate, f"Aggregate ({len(per_url)} URL(s))")
    for report in per_url:
        lines += _render_report(report, report.url)
    return "\n".join(lines)


def write_markdown(path: str | Path, per_url: list[UrlReport], aggregate: UrlReport) -> None:
    Path(path).write_text(render_markdown(per_url, aggregate), encoding="utf-8")
