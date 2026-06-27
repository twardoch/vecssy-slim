# this_file: tests/test_aggregate.py
"""Tests for coverage aggregation, sorting, and report merging."""

from vecssy_slim.aggregate import build_url_report, merge_reports
from vecssy_slim.models import FontRecord, UrlReport, style_label


def test_style_label_maps_to_n_and_i():
    assert style_label("normal") == "n"
    assert style_label("italic") == "i"
    assert style_label("oblique 10deg") == "i"
    assert style_label("") == "n"


def test_coverage_is_chars_times_size():
    rec = FontRecord("Inter", 16.0, "400", "normal", "100%", 10)
    assert rec.coverage == 160.0


def test_build_url_report_aggregates_per_style_and_family():
    records = [
        FontRecord("Inter", 16.0, "400", "normal", "100%", 10),  # 160
        FontRecord("Inter", 16.0, "400", "normal", "100%", 5),   # 80  -> same style group
        FontRecord("Inter", 32.0, "700", "normal", "100%", 4),   # 128 -> bold style group
    ]
    report = build_url_report("http://x", records)

    assert len(report.families) == 1
    fam = report.families[0]
    assert fam.family == "Inter"
    assert fam.chars == 19
    assert fam.coverage == 160 + 80 + 128

    # Two distinct style groups (400 and 700), sorted by coverage desc.
    assert len(report.styles) == 2
    assert report.styles[0].coverage == 240  # the 400 group (160+80)
    assert report.styles[0].weight == "400"
    assert report.styles[0].chars == 15
    assert report.styles[1].coverage == 128


def test_families_sorted_by_coverage_descending():
    records = [
        FontRecord("Small", 10.0, "400", "normal", "100%", 100),   # 1000
        FontRecord("Huge", 90.0, "400", "normal", "100%", 50),     # 4500
    ]
    report = build_url_report("http://x", records)
    assert [f.family for f in report.families] == ["Huge", "Small"]


def test_stretch_and_style_are_distinct_keys():
    records = [
        FontRecord("F", 10.0, "400", "italic", "100%", 1),
        FontRecord("F", 10.0, "400", "normal", "75%", 1),
        FontRecord("F", 10.0, "400", "normal", "100%", 1),
    ]
    report = build_url_report("http://x", records)
    assert len(report.families) == 1
    assert len(report.styles) == 3


def test_merge_reports_sums_across_urls_and_skips_errors():
    r1 = build_url_report("a", [FontRecord("Inter", 16.0, "400", "normal", "100%", 10)])
    r2 = build_url_report("b", [FontRecord("Inter", 16.0, "400", "normal", "100%", 5)])
    err = UrlReport(url="c", error="boom")

    merged = merge_reports([r1, r2, err])
    assert len(merged.families) == 1
    assert merged.families[0].chars == 15
    assert merged.families[0].coverage == 240
    assert merged.total_coverage == 240


def test_empty_records_yield_empty_report():
    report = build_url_report("http://x", [])
    assert report.families == []
    assert report.total_chars == 0
    assert report.total_coverage == 0.0
