# this_file: src/vecssy_slim/analyzer.py
"""Crawl URLs with headless Chromium and collect rendered-font records.

The browser, not the stylesheet, is the source of truth here: for every text
node we ask the Chrome DevTools Protocol which font it *actually* resolved
(`CSS.getPlatformFontsForNode`, with per-family glyph counts) and pair that
with the node's computed `font-size`/`weight`/`style`/`stretch`
(`CSS.getComputedStyleForNode`). Declared `@font-face` rules that never show
up as a resolved family are dead weight.
"""

from __future__ import annotations

from loguru import logger

from vecssy_slim.aggregate import build_url_report
from vecssy_slim.models import FontRecord, UrlReport

_TEXT_NODE = 3


def _parse_px(value: str) -> float:
    """Computed `font-size` is always reported in px, e.g. '16px'."""
    try:
        return float(value.removesuffix("px").strip())
    except (ValueError, AttributeError):
        return 0.0


def analyze_urls(
    urls: list[str],
    *,
    timeout_ms: int = 30_000,
    wait_until: str = "networkidle",
    headless: bool = True,
) -> list[UrlReport]:
    """Analyze each URL in its own page; failures are captured, not raised."""
    # Imported lazily so unit tests and `--help` don't require a browser.
    from playwright.sync_api import sync_playwright

    reports: list[UrlReport] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        try:
            for url in urls:
                logger.info("Analyzing {}", url)
                page = browser.new_page()
                try:
                    records = _collect_records(page, url, timeout_ms, wait_until)
                    reports.append(build_url_report(url, records))
                except Exception as exc:  # one bad URL must not sink the run
                    logger.error("Failed on {}: {}", url, exc)
                    reports.append(UrlReport(url=url, error=str(exc)))
                finally:
                    page.close()
        finally:
            browser.close()
    return reports


def _collect_records(page, url: str, timeout_ms: int, wait_until: str) -> list[FontRecord]:
    page.goto(url, wait_until=wait_until, timeout=timeout_ms)
    client = page.context.new_cdp_session(page)
    try:
        client.send("DOM.enable")
        client.send("CSS.enable")
        doc = client.send("DOM.getDocument", {"depth": -1, "pierce": True})
        records: list[FontRecord] = []
        style_cache: dict[int, tuple[float, str, str, str]] = {}
        _walk(client, doc["root"], parent_element_id=None, records=records, cache=style_cache)
        logger.debug("{}: {} font records", url, len(records))
        return records
    finally:
        client.detach()


def _walk(client, node: dict, parent_element_id: int | None, records: list, cache: dict) -> None:
    node_type = node.get("nodeType")
    node_id = node.get("nodeId")

    if node_type == _TEXT_NODE:
        text = node.get("nodeValue") or ""
        if text.strip() and parent_element_id is not None:
            _record_text_node(client, node_id, parent_element_id, records, cache)
        return

    # Element (or document/shadow root): recurse, tracking nearest element parent.
    next_parent = node_id if node_type == 1 else parent_element_id
    for child in node.get("children", []) or []:
        _walk(client, child, next_parent, records, cache)
    # Pierce into iframes and shadow trees so we don't miss their text.
    content_doc = node.get("contentDocument")
    if content_doc:
        _walk(client, content_doc, None, records, cache)
    for root in node.get("shadowRoots", []) or []:
        _walk(client, root, next_parent, records, cache)


def _record_text_node(client, text_node_id, parent_element_id, records, cache) -> None:
    size, weight, style, stretch = _computed_style(client, parent_element_id, cache)
    for font in _platform_fonts(client, text_node_id):
        glyphs = int(font.get("glyphCount", 0) or 0)
        family = font.get("familyName") or ""
        if glyphs > 0 and family:
            records.append(FontRecord(family, size, weight, style, stretch, glyphs))


def _computed_style(client, element_id, cache) -> tuple[float, str, str, str]:
    if element_id in cache:
        return cache[element_id]
    resp = client.send("CSS.getComputedStyleForNode", {"nodeId": element_id})
    props = {p["name"]: p["value"] for p in resp.get("computedStyle", [])}
    result = (
        _parse_px(props.get("font-size", "16px")),
        props.get("font-weight", "400"),
        props.get("font-style", "normal"),
        props.get("font-stretch", "100%"),
    )
    cache[element_id] = result
    return result


def _platform_fonts(client, node_id) -> list[dict]:
    resp = client.send("CSS.getPlatformFontsForNode", {"nodeId": node_id})
    return resp.get("fonts", []) or []
