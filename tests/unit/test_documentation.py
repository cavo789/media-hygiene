"""The READMEs and the documentation: no broken link, both languages kept in step."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION = ROOT / "documentation"
LOCALES = ("en", "fr")
PAGES = sorted(
    [ROOT / "README.md", ROOT / "README_FR.md", *DOCUMENTATION.rglob("*.md")]
)
LINK = re.compile(r"\[[^\]]*\]\((?P<target>[^)\s]+)\)")
HEADING = re.compile(r"^#{1,6} (?P<title>.+)$")
FENCE = "```"
EXTERNAL = ("http://", "https://", "mailto:")


def prose(page: Path) -> list[str]:
    """The lines of a page outside its fenced code blocks."""
    lines, fenced = [], False
    for line in page.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(FENCE):
            fenced = not fenced
        elif not fenced:
            lines.append(line)
    return lines


def anchors(page: Path) -> set[str]:
    """The anchors GitHub gives the headings of a page (`-1` for a repeated one)."""
    seen: Counter[str] = Counter()
    found = set()
    for line in prose(page):
        heading = HEADING.match(line)
        if heading is None:
            continue
        slug = re.sub(r"[^\w\- ]", "", heading["title"].strip().lower()).replace(
            " ", "-"
        )
        found.add(f"{slug}-{seen[slug]}" if seen[slug] else slug)
        seen[slug] += 1
    return found


def local_links(page: Path) -> list[str]:
    """Every link and image of a page that points inside the repository."""
    return [
        link["target"]
        for line in prose(page)
        for link in LINK.finditer(line)
        if not link["target"].startswith(EXTERNAL)
    ]


@pytest.mark.parametrize("page", PAGES, ids=lambda page: str(page.relative_to(ROOT)))
def test_links_and_anchors_exist(page: Path) -> None:
    """Every relative link reaches a file, and every `#anchor` a heading of it."""
    broken = []
    for target in local_links(page):
        path, _, anchor = target.partition("#")
        destination = (page.parent / path).resolve() if path else page
        if not destination.exists() or (
            anchor
            and destination.suffix == ".md"
            and anchor not in anchors(destination)
        ):
            broken.append(target)
    assert not broken, f"{page.relative_to(ROOT)}: {broken}"


def test_both_languages_have_the_same_files() -> None:
    """A page or a screenshot added in one language exists in the other one too."""
    english, french = (
        {
            path.relative_to(DOCUMENTATION / locale)
            for path in (DOCUMENTATION / locale).rglob("*")
        }
        for locale in LOCALES
    )
    assert english == french


@pytest.mark.parametrize("locale", LOCALES)
def test_every_screenshot_is_used(locale: str) -> None:
    """No image lies in the repository without a page showing it."""
    shown = {
        (page.parent / target).resolve()
        for page in PAGES
        for target in local_links(page)
    }
    images = set((DOCUMENTATION / locale / "images").iterdir())
    assert {image.resolve() for image in images} <= shown
