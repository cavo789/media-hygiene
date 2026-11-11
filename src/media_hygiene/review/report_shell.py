"""A report served by the home page's server, inside the home page's real frame (0639).

A report is a file readable alone: on the disk it keeps its own sidebar, nothing of the
home page. Served, its frame is replaced by the shell of every page: the spaces,
*Reports* highlighted, the way back. The report's own pages and its date stay, in a
line above it. A report of an older version wears a thin bar instead: replaced too. A
file without either is served as it lies. The file itself is never written.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, replace
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from markupsafe import Markup, escape

from media_hygiene.cli.menu_catalog import catalog
from media_hygiene.constants import Locale
from media_hygiene.docs.served import served_url
from media_hygiene.i18n import _, active_locale
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.report.report_header import REPORT_STEPS
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.nonce import REVIEW_POLICY, hashed_policy
from media_hygiene.review.page_header import PageHeader, page_header
from media_hygiene.review.report_files import report_response

if TYPE_CHECKING:
    from pathlib import Path

_PACKAGE: Final = "media_hygiene.review"
_TEMPLATE: Final = "report_shell.html.j2"
# The page of the frame that lists the reports: its space, its folders.
_REPORTS_PAGE: Final = "console_reports.html.j2"
_INDEX_KIND: Final = "index"
# The frame on top of a report: the first match, before any of its content.
_FRAME: Final = re.compile(
    rb"<!-- mh-frame (?P<kind>\w+) -->.*?<!-- /mh-frame -->"
    rb'|<nav class="mh-bar".*?</nav>',
    re.DOTALL,
)
# What is kept of it, as the report wrote it, already escaped; a thin bar's separator
# (U+203A, UTF-8) is no name.
_NAME: Final = re.compile(rb'class="mh-page">(?!\xe2\x80\xba)(?P<text>[^<]+)<')
_OWN_PAGES: Final = re.compile(rb'<ul class="mh-own">.*?</ul>', re.DOTALL)
_WHEN: Final = re.compile(rb'<span class="mh-crumb">\xc2\xb7.*?</span>', re.DOTALL)


@dataclass(frozen=True, slots=True)
class _Kept:
    """What a report's frame said, to show again in the real one."""

    kind: str
    name: Markup
    own: Markup
    when: Markup


async def shelled_report(reports_dir: Path, path: str) -> Response:
    """Serve a file of the reports folder; a report in the home page's frame.

    Args:
        reports_dir: The reports folder, in the container.
        path: The path asked for.

    Returns:
        What `report_response` answers, its HTML pages framed.
    """
    response = await report_response(reports_dir, path)
    if response.status != HTTPStatus.OK or response.content_type != ContentType.HTML:
        return response
    body = await asyncio.to_thread(in_shell, response.body)
    # The report's scripts by their hash, the shell's by the answer's nonce (0671).
    return replace(response, body=body, policy=hashed_policy(REVIEW_POLICY, body))


def in_shell(report: bytes) -> bytes:
    """Replace the frame of a report by the home page's.

    Args:
        report: The report, as it lies on the disk.

    Returns:
        The page to serve; the same bytes when it has no frame.
    """
    frame = _FRAME.search(report)
    if frame is None:
        return report
    kept = _kept(frame)
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _TEMPLATE
    )
    shell = template.render(
        header=_header(kept.kind), page_name=kept.name, own=kept.own, when=kept.when
    )
    return report[: frame.start()] + shell.encode() + report[frame.end() :]


def _kept(frame: re.Match[bytes]) -> _Kept:
    """Read what stays of a report's frame.

    Args:
        frame: The frame found.

    Returns:
        Its kind, name, own pages (none for the index: it is alone) and date.
    """
    found = frame.group()
    kind = (frame.group("kind") or b"").decode()
    kind = kind if kind in REPORT_STEPS else _INDEX_KIND
    name = _NAME.search(found)
    own = _OWN_PAGES.search(found) if kind != _INDEX_KIND else None
    when = _WHEN.search(found)
    return _Kept(
        kind,
        _trusted(name.group("text")) if name else escape(_("Reports")),
        _trusted(own.group()) if own else Markup(),
        _trusted(when.group()) if when else Markup(),
    )


def _trusted(written: bytes) -> Markup:
    """Mark HTML a report's template wrote and escaped.

    Args:
        written: A part of its frame.

    Returns:
        It, shown as it is.
    """
    return Markup(written.decode())  # noqa: S704  # escaped when the report was written


def _header(kind: str) -> PageHeader:
    """The top bar and sidebar of a kind of report.

    Args:
        kind: A key of `REPORT_STEPS`.

    Returns:
        The frame of the reports' space, with the report's own chapter. This server
        serves the page: its links are plain ones.
    """
    header = replace(page_header(_REPORTS_PAGE), shared=True)
    doc = catalog().step(REPORT_STEPS[kind]).doc
    if doc is None:  # pragma: no cover - test_report_look checks every kind has one
        return header
    twin = Locale.EN if active_locale() is Locale.FR else Locale.FR
    return replace(
        header, doc=served_url(doc, active_locale()), twin=served_url(doc, twin)
    )
