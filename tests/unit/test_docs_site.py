"""The documentation site: every page in its menu, every link the tool prints alive."""

from __future__ import annotations

import re
from pathlib import Path

import polib
import pytest

from media_hygiene.constants import DOC_PAGES

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION = ROOT / "documentation"
MKDOCS = ROOT / ".config" / "mkdocs" / "mkdocs.yml"
CATALOG = ROOT / "src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po"
NAV_PAGE = re.compile(r"^\s*- (?:[^:]+: )?(?P<page>[\w./-]+\.md)$")
# `f"{DOC_PAGES}/{_('start/01-first-audit/')}"`: a page of the site, translated.
SITE_LINK = re.compile(r"\{DOC_PAGES\}/\{_\(\s*['\"](?P<path>[^'\"]*)['\"]\s*\)\}")


def nav_pages() -> set[str]:
    """The pages the `nav` of mkdocs.yml lists, relative to a language folder."""
    lines = MKDOCS.read_text(encoding="utf-8").split("\nnav:\n", 1)[1].splitlines()
    return {match["page"] for line in lines if (match := NAV_PAGE.match(line))}


def site_links() -> set[str]:
    """Every page path of the site the sources print, in English."""
    return {
        match["path"]
        for source in (ROOT / "src").rglob("*.py")
        for match in SITE_LINK.finditer(source.read_text(encoding="utf-8"))
    }


def page_file(path: str) -> Path:
    """The file of documentation/ behind a page path of the site.

    `fr/start/01-first-audit/` is `fr/start/01-first-audit.md`; English is at the root.
    """
    parts = path.strip("/").split("/") if path.strip("/") else []
    locale = parts.pop(0) if parts[:1] == ["fr"] else "en"
    if not parts:
        return DOCUMENTATION / locale / "README.md"
    return DOCUMENTATION / locale / Path(*parts).with_suffix(".md")


def test_every_page_is_in_the_navigation() -> None:
    """A new page (a new verb's) must be added to `nav`, or the site hides it."""
    pages = {
        page.relative_to(DOCUMENTATION / "en").as_posix()
        for page in (DOCUMENTATION / "en").rglob("*.md")
    }
    listed = nav_pages()
    assert pages - listed == set(), (
        "add these pages to nav in .config/mkdocs/mkdocs.yml"
    )
    assert listed - pages == set(), "nav lists pages that do not exist"


def test_the_tool_prints_site_links() -> None:
    """The guide links of the console go to the site, not to GitHub's file view."""
    assert DOC_PAGES.startswith("https://cavo789.github.io/")
    assert len(site_links()) >= 2


@pytest.mark.parametrize("path", sorted(site_links()))
def test_every_printed_link_has_its_page_in_both_languages(path: str) -> None:
    """The English path and its French translation both name an existing page."""
    translated = {entry.msgid: entry.msgstr for entry in polib.pofile(str(CATALOG))}
    assert translated.get(path), f"{path!r} has no French translation"
    assert page_file(path).is_file()
    assert page_file(translated[path]).is_file()
