# this_file: src/vecssy_slim/models.py
"""Data models for font usage records, aggregated stats, and per-URL reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple


class FontRecord(NamedTuple):
    """One stretch of text rendered by a single resolved font on a page.

    `chars` is the glyph count the browser actually rendered with `family`
    (from CDP `CSS.getPlatformFontsForNode`); `size` is the computed
    `font-size` in CSS pixels for the text node's parent element.
    """

    family: str
    size: float
    weight: str
    style: str
    stretch: str
    chars: int

    @property
    def coverage(self) -> float:
        """Visual footprint of this record: rendered glyphs x font size."""
        return self.chars * self.size


@dataclass
class StyleStat:
    """Coverage aggregated per (family, weight, style, stretch)."""

    family: str
    weight: str
    style: str
    stretch: str
    chars: int = 0
    coverage: float = 0.0

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "weight": self.weight,
            "style": self.style,
            "stretch": self.stretch,
            "chars": self.chars,
            "coverage": round(self.coverage, 2),
        }


@dataclass
class FamilyStat:
    """Coverage aggregated per family, with its per-style breakdown."""

    family: str
    chars: int = 0
    coverage: float = 0.0
    styles: list[StyleStat] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "chars": self.chars,
            "coverage": round(self.coverage, 2),
            "styles": [s.to_dict() for s in self.styles],
        }


@dataclass
class UrlReport:
    """Font-coverage report for a single URL (or an aggregate of URLs)."""

    url: str
    families: list[FamilyStat] = field(default_factory=list)
    total_chars: int = 0
    total_coverage: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "error": self.error,
            "total_chars": self.total_chars,
            "total_coverage": round(self.total_coverage, 2),
            "families": [f.to_dict() for f in self.families],
        }
