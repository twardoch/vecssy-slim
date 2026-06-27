# this_file: tests/test_report.py
"""Tests for JSON/Markdown report rendering."""

import json

from vecssy_slim.aggregate import build_url_report, merge_reports
from vecssy_slim.models import FontRecord, UrlReport
from vecssy_slim.report import build_payload, render_markdown, write_json, write_markdown


def _sample():
    per_url = [
        build_url_report("http://x", [FontRecord("Inter", 16.0, "400", "normal", "100%", 10)])
    ]
    return per_url, merge_reports(per_url)


def test_build_payload_has_aggregate_and_urls():
    per_url, aggregate = _sample()
    payload = build_payload(per_url, aggregate)
    assert payload["aggregate"]["families"][0]["family"] == "Inter"
    assert payload["aggregate"]["styles"][0]["family"] == "Inter"
    assert payload["urls"][0]["url"] == "http://x"


def test_per_url_has_styles_not_families_and_uses_n_i():
    per_url, _ = _sample()
    d = per_url[0].to_dict()
    assert "families" not in d  # per-URL reports surface styles only
    assert d["styles"][0]["style"] == "n"


def test_write_json_roundtrips(tmp_path):
    per_url, aggregate = _sample()
    out = tmp_path / "r.json"
    write_json(out, per_url, aggregate)
    data = json.loads(out.read_text())
    assert data["aggregate"]["families"][0]["coverage"] == 160.0


def test_markdown_contains_tables_and_error(tmp_path):
    per_url, aggregate = _sample()
    per_url.append(UrlReport(url="bad", error="nope"))
    out = tmp_path / "r.md"
    write_markdown(out, per_url, aggregate)
    text = out.read_text()
    assert "# Font coverage report" in text
    assert "| Family |" in text
    assert "Inter" in text
    assert "**Error:** nope" in text


def test_render_markdown_is_string():
    per_url, aggregate = _sample()
    assert isinstance(render_markdown(per_url, aggregate), str)
