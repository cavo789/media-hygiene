"""The bar on top of a report: its chapter, in both languages (0273).

A report is a file opened from disk: no server answers `/docs/`, so the links go to the
public site (`Doc.url`), in the report's language and in the other one.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from types import MappingProxyType
from typing import Final

from media_hygiene.cli.menu_catalog import catalog
from media_hygiene.constants import APP_NAME, Locale
from media_hygiene.i18n import _, active_locale

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


# Where each kind of page lies, relative to itself: the reports index, the run's report.
_INDEX_HREF: Final = MappingProxyType(
    {
        "audit": "../index.html",
        "clean": "../index.html",
        "near": "../index.html",
        "classify": "../index.html",
        "pair": "../../index.html",
        "index": "index.html",
    }
)
_REPORT_HREF: Final = MappingProxyType({"pair": "../report.html"})


@dataclass(frozen=True, slots=True)
class ReportPage:
    """An entry of the sidebar: one page of the reports."""

    label: str
    href: str
    current: bool = False


@dataclass(frozen=True, slots=True)
class ReportHeader:
    """The links of a report's bar, and the sidebar of its own pages (0498)."""

    doc: str
    twin: str
    twin_lang: str
    twin_label: str
    pages: tuple[ReportPage, ...] = ()
    version: str = ""


def report_pages(kind: str, *, near: bool) -> tuple[ReportPage, ...]:
    """The report's own pages, for the sidebar of a file opened without a server.

    Args:
        kind: A key of `REPORT_STEPS`.
        near: The run has a page of near duplicates.

    Returns:
        The reports index, the run's report and its near duplicates page.
    """
    pages = [ReportPage(_("Reports"), _INDEX_HREF[kind], kind == "index")]
    if kind == "index":
        return tuple(pages)
    here = kind in {"audit", "clean", "classify"}
    pages.append(ReportPage(_("Report"), _REPORT_HREF.get(kind, "report.html"), here))
    if near or kind == "near":
        pages.append(ReportPage(_("Near duplicates"), "near.html", kind == "near"))
    return tuple(pages)


def report_header(kind: str, *, near: bool = False) -> ReportHeader:
    """The links of a kind of report.

    Args:
        kind: A key of `REPORT_STEPS`.
        near: The run has a page of near duplicates.

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
        pages=report_pages(kind, near=near),
        version=version(APP_NAME),
    )
