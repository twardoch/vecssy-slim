# this_file: src/vecssy_slim/__main__.py
"""Fire CLI for vecssy-slim (`vecssy-slim` and `python -m vecssy_slim`)."""

from __future__ import annotations

import sys
from pathlib import Path

from fire.core import FireError
from loguru import logger
from rich.console import Console
from rich.table import Table

from vecssy_slim.aggregate import merge_reports
from vecssy_slim.analyzer import analyze_urls
from vecssy_slim.models import UrlReport
from vecssy_slim.report import write_json, write_markdown

console = Console()


def _resolve_urls(url: str | None, list_urls: str | None) -> list[str]:
    urls: list[str] = []
    if url:
        urls.append(url.strip())
    if list_urls:
        path = Path(list_urls)
        if not path.is_file():
            raise FireError(f"--list_urls file not found: {list_urls}")
        urls += [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    if not urls:
        raise FireError("Provide --url or --list_urls (a file with one URL per line).")
    # De-dupe while preserving order.
    return list(dict.fromkeys(urls))


def _print_summary(aggregate: UrlReport, top: int) -> None:
    table = Table(title="Font coverage (aggregate, top families)")
    table.add_column("Family", style="cyan")
    table.add_column("Glyphs", justify="right")
    table.add_column("Coverage", justify="right", style="green")
    for fam in aggregate.families[:top]:
        table.add_row(fam.family, f"{fam.chars:,}", f"{fam.coverage:,.0f}")
    console.print(table)


def analyze(
    url: str | None = None,
    list_urls: str | None = None,
    json_report: str | None = None,
    md_report: str | None = None,
    timeout: float = 30.0,
    wait_until: str = "networkidle",
    headless: bool = True,
    top: int = 15,
    verbose: bool = False,
) -> None:
    """Crawl URL(s), rank fonts by rendered coverage, and write reports.

    Args:
        url: A single URL to analyze.
        list_urls: Path to a file with one URL per line (# comments allowed).
        json_report: Path to write the full JSON report. If omitted and
            --list_urls is given, defaults to that file with a .json extension.
        md_report: Path to write a Markdown report. If omitted and --list_urls
            is given, defaults to that file with a .md extension.
        timeout: Per-page navigation timeout in seconds.
        wait_until: Playwright load state: load | domcontentloaded | networkidle.
        headless: Run Chromium headless (set False to watch the browser).
        top: How many families to show in the terminal summary.
        verbose: Enable debug logging.
    """
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if verbose else "INFO")

    urls = _resolve_urls(url, list_urls)
    logger.info("Analyzing {} URL(s)", len(urls))

    per_url = analyze_urls(
        urls,
        timeout_ms=int(timeout * 1000),
        wait_until=wait_until,
        headless=headless,
    )
    aggregate = merge_reports(per_url)

    # If a --list_urls file was given but a report path was not, default the
    # report to that file's path with the matching extension.
    if list_urls:
        if json_report is None:
            json_report = str(Path(list_urls).with_suffix(".json"))
        if md_report is None:
            md_report = str(Path(list_urls).with_suffix(".md"))

    if json_report:
        write_json(json_report, per_url, aggregate)
        logger.info("Wrote JSON report to {}", json_report)
    if md_report:
        write_markdown(md_report, per_url, aggregate)
        logger.info("Wrote Markdown report to {}", md_report)

    _print_summary(aggregate, top)
    failures = [r.url for r in per_url if r.error]
    if failures:
        logger.warning("{} URL(s) failed: {}", len(failures), ", ".join(failures))


def main() -> None:
    import fire

    fire.Fire(analyze)


if __name__ == "__main__":
    main()
