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
from media_hygiene.review.report_shell import in_shell
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
    assert 'class="mh-rtop"' in html  # the home page's frame (0498)
    assert 'class="mh-rside"' in html
    assert 'aria-current="page"' in html
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


def test_the_sidebar_lists_the_reports_own_pages_and_nothing_of_the_home_page(
    locations: Locations, media: MediaFactory
) -> None:
    """A file from disk lists its own pages, nothing of the home page (0639)."""
    report = _reports(locations, media)
    html = report.read_text()
    assert '<a href="../index.html">' in html
    assert "mh-served" not in html
    assert 'href="/' not in html
    assert "mh-shell" not in html
    pair = (report.parent / "pairs/pair-0001.html").read_text()
    assert '<a href="../../index.html">' in pair
    assert '<a href="../report.html">' in pair
    index = write_index(locations.reports_dir).read_text()
    assert '<a href="index.html" aria-current="page">' in index


def test_a_served_report_wears_the_home_pages_frame(
    locations: Locations, media: MediaFactory
) -> None:
    """Served: the real sidebar, Reports highlighted, own pages and date kept (0639)."""
    report = _reports(locations, media)
    on_disk = report.read_bytes()
    html = in_shell(on_disk).decode()
    assert '<aside class="mh-rside"' not in html
    assert 'class="mh-shell-side"' in html
    assert 'href="/#reports" data-space="reports" aria-current="page"' in html
    assert 'href="report.html" aria-current="page"' in html
    assert 'id="homeLink" href="/" data-shared="1"' in html
    assert '<ul class="mh-own">' in html
    assert '<span class="mh-crumb">·' in html
    assert '<h1 class="mh-page">Audit report</h1>' in html
    assert "<!-- mh-frame" not in html
    assert report.read_bytes() == on_disk


def test_the_served_index_has_no_list_of_own_pages(locations: Locations) -> None:
    """The reports index is alone: no line of its own pages under the top bar."""
    html = in_shell(write_index(locations.reports_dir).read_bytes()).decode()
    assert 'class="mh-shell-side"' in html
    assert 'class="mh-rown"' not in html


def test_a_report_of_an_older_version_loses_its_thin_bar() -> None:
    """A report written before 0498: its thin bar replaced, its name kept."""
    old = (
        '<html lang="en"><body><nav class="mh-bar" aria-label="x">'
        '<span class="mh-page" aria-hidden="true">\u203a</span>'
        '<span class="mh-page">Audit &amp; more</span></nav>'
        "<main>kept</main></body></html>"
    ).encode()
    html = in_shell(old).decode()
    assert "mh-bar" not in html
    assert '<h1 class="mh-page">Audit &amp; more</h1>' in html
    assert "<main>kept</main>" in html


def test_a_file_without_a_frame_is_served_as_it_lies() -> None:
    """Any other HTML under the reports folder is not touched."""
    assert in_shell(b"<html><body>mine</body></html>") == (
        b"<html><body>mine</body></html>"
    )
