"""The reports wear the home page's look (0273): theme, bar, avatar, no network."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import DOC_PAGES, Locale, RunKind
from media_hygiene.i18n import using
from media_hygiene.report.index_page import write_index
from media_hygiene.report.report_header import REPORT_STEPS, report_header
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.reporting import write_report
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.media import MediaFactory

_LOADED: Final = re.compile(
    r"""src=["']https?://|url\(\s*["']?https?://|@import|<link\b"""
)


def _assert_look(html: str, kind: str) -> None:
    """The bar, both themes' tokens, the inlined avatar, the chapter links."""
    assert 'class="mh-bar"' in html
    assert "--mk-bg:" in html
    assert 'data-theme="dark"' in html
    assert "prefers-color-scheme: dark" in html
    assert 'src="data:image/webp;base64,' in html
    assert "@font-face" not in html  # the system fonts: a file loads none
    assert "--bg: #" not in html
    links = re.findall(r'<a class="mh-doc" href="([^"]+)"', html)
    assert len(links) == 2
    header = report_header(kind)
    assert links == [header.doc, header.twin]
    assert not _LOADED.search(html), "a report must load nothing from outside"


def _reports(locations: Locations, media: MediaFactory) -> Path:
    for seed in range(2):
        original = media.image(f"c/Photos/IMG_{seed}.jpg", seed)
        media.copy(original, f"d/Backup/IMG_{seed} (1).jpg")
    runtime = make_runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    report = write_report(runtime, ReportRecord(RunKind.AUDIT, findings))
    assert report is not None
    return report


def test_the_audit_report_its_pairs_and_the_index(
    locations: Locations, media: MediaFactory
) -> None:
    """Three kinds of page, one look."""
    report = _reports(locations, media)
    _assert_look(report.read_text(), "audit")
    _assert_look((report.parent / "pairs/pair-0001.html").read_text(), "pair")
    _assert_look(write_index(locations.reports_dir).read_text(), "index")


def test_the_classify_report_and_its_years(
    cli: CliRunner, locations: Locations, media: MediaFactory
) -> None:
    """The proposal and a year page."""
    media.image("c/Photos/IMG_1.jpg", seed=1)
    assert run(cli, "classify").exit_code == 0
    folder = next(locations.reports_dir.glob("*-classify"))
    _assert_look((folder / "report.html").read_text(), "classify")
    years = [page for page in folder.glob("*.html") if page.name != "report.html"]
    for page in years:
        _assert_look(page.read_text(), "classify")


@pytest.mark.parametrize("kind", sorted(REPORT_STEPS))
@pytest.mark.parametrize("locale", list(Locale))
def test_each_kind_links_its_chapter_in_both_languages(
    kind: str, locale: Locale
) -> None:
    """The public site, the report's language first."""
    with using(locale):
        header = report_header(kind)
    assert header.doc.startswith(DOC_PAGES)
    assert header.twin.startswith(DOC_PAGES)
    assert ("/fr/" in header.doc) is (locale is Locale.FR)
    assert ("/fr/" in header.twin) is (locale is Locale.EN)
