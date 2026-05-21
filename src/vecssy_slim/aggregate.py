# this_file: src/vecssy_slim/aggregate.py
"""Aggregate raw font records into coverage-ranked per-URL reports.

Coverage is the core metric: for every stretch of rendered text it is the
number of characters rendered with a given font multiplied by that text's
font size. It approximates how much visual area a font occupies, so a font
used for a few large headings can outrank one used for a lot of fine print.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from vecssy_slim.models import FamilyStat, FontRecord, StyleStat, UrlReport

# (family, weight, style, stretch) -> accumulated [chars, coverage]
_StyleKey = tuple[str, str, str, str]


def _assemble(url: str, acc: dict[_StyleKey, list]) -> UrlReport:
    """Turn a {style_key: [chars, coverage]} accumulator into a sorted report."""
    family_acc: dict[str, FamilyStat] = defaultdict(lambda: FamilyStat(family=""))
    for (family, weight, style, stretch), (chars, coverage) in acc.items():
        st = StyleStat(family, weight, style, stretch, int(chars), coverage)
        fam = family_acc[family]
        fam.family = family
        fam.chars += st.chars
        fam.coverage += st.coverage
        fam.styles.append(st)

    families = sorted(family_acc.values(), key=lambda f: f.coverage, reverse=True)
    for fam in families:
        fam.styles.sort(key=lambda s: s.coverage, reverse=True)

    return UrlReport(
        url=url,
        families=families,
        total_chars=sum(f.chars for f in families),
        total_coverage=sum(f.coverage for f in families),
    )


def build_url_report(url: str, records: Iterable[FontRecord]) -> UrlReport:
    """Fold raw font records into a report sorted by coverage (descending)."""
    acc: dict[_StyleKey, list] = {}
    for rec in records:
        key = (rec.family, rec.weight, rec.style, rec.stretch)
        cur = acc.setdefault(key, [0, 0.0])
        cur[0] += rec.chars
        cur[1] += rec.coverage
    return _assemble(url, acc)


def merge_reports(reports: Iterable[UrlReport], url: str = "ALL URLS") -> UrlReport:
    """Combine several per-URL reports into one site-wide aggregate."""
    acc: dict[_StyleKey, list] = {}
    for rep in reports:
        if rep.error:
            continue
        for fam in rep.families:
            for st in fam.styles:
                key = (st.family, st.weight, st.style, st.stretch)
                cur = acc.setdefault(key, [0, 0.0])
                cur[0] += st.chars
                cur[1] += st.coverage
    return _assemble(url, acc)
