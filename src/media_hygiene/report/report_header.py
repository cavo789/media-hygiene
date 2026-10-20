"""The bar on top of a report: its chapter, in both languages (0273).

A report is a file opened from disk: no server answers `/docs/`, so the links go to the
public site (`Doc.url`), in the report's language and in the other one.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from media_hygiene.cli.menu_catalog import catalog
from media_hygiene.constants import Locale
from media_hygiene.i18n import active_locale

# Each kind of report, and the action of the catalog whose chapter explains it.
REPORT_STEPS: Final = MappingProxyType(
    {
        "audit": "audit",
        "clean": "clean",
        "pair": "review-pairs",
        "near": "review-near",
        "classify": "classify",
        "index": "reports",
    }
)
# The other language's link, written in that language: never translated.
_TWIN_LABELS: Final = MappingProxyType(
    {Locale.EN: "In English", Locale.FR: "En français"}
)


@dataclass(frozen=True, slots=True)
class ReportHeader:
    """The links of a report's bar."""

    doc: str
    twin: str
    twin_lang: str
    twin_label: str


def report_header(kind: str) -> ReportHeader:
    """The links of a kind of report.

    Args:
        kind: A key of `REPORT_STEPS`.

    Returns:
        Its chapter in the language in use and in the other one.

    Raises:
        KeyError: The kind has no chapter (test_report_look checks each).
    """
    doc = catalog().step(REPORT_STEPS[kind]).doc
    if doc is None:  # pragma: no cover - test_report_look checks every kind has one
        raise KeyError(kind)
    here = active_locale()
    twin = Locale.EN if here is Locale.FR else Locale.FR
    return ReportHeader(
        doc=doc.url(here),
        twin=doc.url(twin),
        twin_lang=twin.value,
        twin_label=_TWIN_LABELS[twin],
    )
