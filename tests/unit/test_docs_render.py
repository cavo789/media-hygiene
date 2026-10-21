"""The documentation inside the image (0270): rendered once, served by every page."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
from html.parser import HTMLParser
from http import HTTPStatus
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import TYPE_CHECKING, override

import pytest

from media_hygiene.cli.home_actions import link as home_link
from media_hygiene.cli.menu_entry import Doc
from media_hygiene.constants import DOC_PAGES, Locale
from media_hygiene.docs import shelf
from media_hygiene.docs.links import LinkKind, LinkSource, resolve
from media_hygiene.docs.pages import DocIndex, route_of
from media_hygiene.docs.render import RenderJob, main, render_all
from media_hygiene.docs.rewrite import rewrite_html
from media_hygiene.docs.served import served_index, served_url
from media_hygiene.review.docs_app import docs_response
from media_hygiene.review.http import REVIEW_POLICY, Request, Response
from media_hygiene.review.shared_routes import asset_or_page
from tests.unit.test_docs_site import nav_pages

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTATION = ROOT / "documentation"
MKDOCS = ROOT / ".config" / "mkdocs" / "mkdocs.yml"
HOOKS = MKDOCS.with_name("hooks.py")
LOCAL = {"host": "127.0.0.1:8765"}
ID = re.compile(r'\sid="(?P<id>[^"]+)"')


class _Links(HTMLParser):
    """Every `href` and `src` of a page."""

    def __init__(self) -> None:
        super().__init__()
        self.found: list[str] = []

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Keep the address of a link or an image."""
        del tag
        self.found.extend(
            value for name, value in attrs if name in {"href", "src"} and value
        )


def links_of(html: str) -> list[str]:
    """The addresses a page links or loads."""
    parser = _Links()
    parser.feed(html)
    return parser.found


@pytest.fixture(scope="module")
def rendered(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, tuple[DocIndex, ...]]:
    """documentation/ rendered once, as the image's `docs` stage does."""
    out = tmp_path_factory.mktemp("docs")
    return out, render_all(RenderJob(DOCUMENTATION, MKDOCS, out))


@pytest.fixture
def served(
    rendered: tuple[Path, tuple[DocIndex, ...]], monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """The rendered docs, served: `MEDIA_HYGIENE_DOCS_DIR` names them."""
    out, _indexes = rendered
    monkeypatch.setenv(shelf.DOCS_VARIABLE, str(out))
    monkeypatch.setattr(shelf, "REPOSITORY", out / "no-sources")
    shelf.docs_root.cache_clear()
    shelf.doc_index.cache_clear()
    yield out
    shelf.docs_root.cache_clear()
    shelf.doc_index.cache_clear()


@pytest.fixture
def no_docs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """No rendered docs: neither the image's nor a developer's."""
    monkeypatch.delenv(shelf.DOCS_VARIABLE, raising=False)
    monkeypatch.setattr(shelf, "BUILT_DOCS", tmp_path / "none")
    shelf.docs_root.cache_clear()
    yield
    shelf.docs_root.cache_clear()


def get(path: str, method: str = "GET") -> Response:
    """Ask the docs route for a path, from the loopback."""
    return asyncio.run(docs_response(Request(method, path, LOCAL)))


def test_every_page_of_both_languages_renders(
    rendered: tuple[Path, tuple[DocIndex, ...]],
) -> None:
    """One fragment per page of documentation/, each with its title."""
    out, indexes = rendered
    for index in indexes:
        sources = {
            page.relative_to(DOCUMENTATION / index.locale).as_posix()
            for page in (DOCUMENTATION / index.locale).rglob("*.md")
        }
        assert {page.path for page in index.pages} == sources
        for page in index.pages:
            fragment = (out / index.locale / page.fragment).read_text(encoding="utf-8")
            assert fragment.startswith("<h1"), page.path
            assert page.title
            assert page.route == route_of(index.locale, page.path)


def test_the_index_lists_every_page_of_the_nav(
    rendered: tuple[Path, tuple[DocIndex, ...]],
) -> None:
    """The menu of the docs is `nav` of mkdocs.yml, in both languages."""
    _out, indexes = rendered
    for index in indexes:
        listed = {path for section in index.sections for path in section.pages}
        assert listed == nav_pages()
        assert tuple(page.path for page in index.pages) == tuple(
            path for section in index.sections for path in section.pages
        )
    french = {index.locale: index for index in indexes}["fr"]
    assert "Pour commencer" in {section.title for section in french.sections}


def test_every_internal_link_leads_to_a_route_and_an_anchor(
    rendered: tuple[Path, tuple[DocIndex, ...]],
) -> None:
    """A link of a rendered page names a page served, and an anchor of that page."""
    out, indexes = rendered
    routes = {page.route: page for index in indexes for page in index.pages}
    ids = {
        page.route: set(ID.findall((out / index.locale / page.fragment).read_text()))
        for index in indexes
        for page in index.pages
    }
    checked = 0
    for index in indexes:
        for page in index.pages:
            html = (out / index.locale / page.fragment).read_text(encoding="utf-8")
            for link in links_of(html):
                address, _hash, anchor = link.partition("#")
                if not address:
                    assert anchor in ids[page.route], (page.path, link)
                    continue
                if not address.startswith("/docs/"):
                    assert address.startswith(("https://", "http://", "mailto:"))
                    continue
                checked += 1
                if "/images/" in address:
                    assert (out / address.removeprefix("/docs/")).is_file(), link
                    continue
                assert address in routes, (page.path, link)
                assert not anchor or anchor in ids[address], (page.path, link)
    assert checked > 100


def test_a_page_asks_nothing_outside(served: Path) -> None:
    """The CSP allows `self` only, and no image or script comes from elsewhere."""
    del served
    reply = get("/docs/fr/start/02-keep-the-cache/")
    assert reply.status is HTTPStatus.OK
    assert reply.policy == REVIEW_POLICY
    assert "default-src 'none'" in reply.policy
    html = reply.body.decode()
    assert not re.search(r'\ssrc="(?!/)', html)
    assert 'lang="fr"' in html
    assert 'href="/docs/en/start/02-keep-the-cache/"' in html  # its twin
    assert 'rel="prev"' in html
    assert 'rel="next"' in html
    assert 'class="highlight capture"' in html
    assert 'id="backToTool" href="/"' in html  # closes its tab, else leads to the tool
    assert "window.close()" in html


def test_the_routes_of_the_docs(served: Path) -> None:
    """Pages, screenshots and the index; anything else is 404 or refused."""
    del served
    assert get("/docs/en/").status is HTTPStatus.OK
    assert get("/docs/en/commands/audit").status is HTTPStatus.OK
    image = get("/docs/en/images/home.webp")
    assert image.status is HTTPStatus.OK
    assert image.max_age > 0
    index = json.loads(get("/docs/fr/index.json").body)
    assert index["locale"] == "fr"
    missing = get("/docs/en/no-such-page/")
    assert missing.status is HTTPStatus.NOT_FOUND
    assert "meerkat" in missing.body.decode()
    assert get("/docs/de/").status is HTTPStatus.NOT_FOUND
    assert get("/docs/en/images/../index.json").status is HTTPStatus.NOT_FOUND
    assert get("/docs/en/images/nothing.webp").status is HTTPStatus.NOT_FOUND
    assert get("/docs/en/", "POST").status is HTTPStatus.METHOD_NOT_ALLOWED


def test_every_page_server_answers_the_docs(served: Path) -> None:
    """The door every page shares serves `/docs/` to the loopback only."""
    del served

    async def page(request: Request) -> Response:
        del request
        return Response(HTTPStatus.IM_A_TEAPOT)

    local = asyncio.run(asset_or_page(Request("GET", "/docs/en/", LOCAL), page))
    assert local.status is HTTPStatus.OK
    outside = Request("GET", "/docs/en/", {"host": "example.com"})
    assert asyncio.run(asset_or_page(outside, page)).status is HTTPStatus.IM_A_TEAPOT


def test_without_docs_the_links_stay_on_the_site(no_docs: None) -> None:
    """No rendered docs: the public site's address, and nothing served."""
    del no_docs
    doc = Doc("commands/audit/", "#en", "#fr")
    assert served_url(doc, Locale.FR) == f"{DOC_PAGES}/fr/commands/audit/#fr"
    assert served_index() is None
    assert get("/docs/en/").status is HTTPStatus.NOT_FOUND


def test_with_docs_the_links_open_the_served_page(served: Path) -> None:
    """The chapter of the version that runs, in both languages."""
    del served
    doc = Doc("commands/audit/", "#en", "#fr")
    assert served_url(doc, Locale.FR) == "/docs/fr/commands/audit/#fr"
    assert served_url(doc, Locale.EN) == "/docs/en/commands/audit/#en"
    assert served_url(Doc(""), Locale.EN) == "/docs/en/"
    assert served_index() in {"/docs/en/index.json", "/docs/fr/index.json"}


def test_a_developer_renders_from_the_sources_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`MEDIA_HYGIENE_DOCS_DIR` renders the sources there, again once they change."""
    target = tmp_path / "docs"
    monkeypatch.setenv(shelf.DOCS_VARIABLE, str(target))
    shelf.docs_root.cache_clear()
    try:
        assert shelf.docs_root() == target
        index = target / "en" / "index.json"
        old = 10**9  # 1970: older than every page
        os.utime(index, ns=(old, old))
        shelf.docs_root.cache_clear()
        assert shelf.docs_root() == target
        assert index.stat().st_mtime_ns != old  # older than the sources: rendered again
        kept = index.stat().st_mtime_ns
        shelf.docs_root.cache_clear()
        assert shelf.docs_root() == target
        assert index.stat().st_mtime_ns == kept  # up to date: left alone
    finally:
        shelf.docs_root.cache_clear()


def test_a_developer_without_sources_has_no_docs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A folder named, but nothing to render it from: the links stay outside."""
    monkeypatch.setenv(shelf.DOCS_VARIABLE, str(tmp_path / "docs"))
    monkeypatch.setattr(shelf, "REPOSITORY", tmp_path)
    shelf.docs_root.cache_clear()
    try:
        assert shelf.docs_root() is None
    finally:
        shelf.docs_root.cache_clear()


def test_where_a_link_leads(tmp_path: Path) -> None:
    """A page, a screenshot, a file of the repository, another site, the same page."""
    docs = tmp_path / "documentation"
    page = docs / "en" / "start" / "a.md"
    source = LinkSource(docs, page)
    assert resolve(source, "../../fr/start/a.md").kind is LinkKind.PAGE
    assert resolve(source, "../../fr/start/a.md").path == PurePosixPath("fr/start/a.md")
    assert resolve(source, "../images/x.webp").kind is LinkKind.FILE
    assert resolve(source, "../../../CLAUDE.md").kind is LinkKind.REPOSITORY
    assert resolve(source, "https://example.com").kind is LinkKind.OUTSIDE
    assert resolve(source, "").kind is LinkKind.KEEP
    assert resolve(source, "../../../../elsewhere.md").kind is LinkKind.KEEP


def test_the_links_of_a_page_are_rewritten(tmp_path: Path) -> None:
    """Pages, screenshots to their routes; another site in a new tab, never loaded."""
    docs = tmp_path / "documentation"
    source = LinkSource(docs, docs / "en" / "start" / "a.md")
    html = (
        '<a href="../commands/audit.md#x">a</a> <a href="#here">b</a> '
        '<img alt="" src="../images/x.webp"> <a href="https://example.com">c</a> '
        '<img alt="" src="https://example.com/badge.svg"> '
        '<a href="../../../.github/workflows/ci.yml">d</a> <a href="../notes.txt">e</a>'
    )
    rewritten = rewrite_html(html, source)
    assert 'href="/docs/en/commands/audit/#x"' in rewritten
    assert 'href="#here"' in rewritten
    assert 'src="/docs/en/images/x.webp"' in rewritten
    assert 'href="https://example.com" target="_blank" rel="noopener"' in rewritten
    assert "badge.svg" not in rewritten
    assert "blob/main/.github/workflows/ci.yml" in rewritten
    assert "blob/main/documentation/en/notes.txt" in rewritten


def test_the_renderer_from_the_command_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The Dockerfile's call: three arguments, else its usage."""
    assert main([]) == 2
    out = tmp_path / "out"
    assert main([str(DOCUMENTATION), str(MKDOCS), str(out)]) == 0
    assert "pages rendered" in capsys.readouterr().out
    assert (out / "fr" / "index.json").is_file()


def test_the_home_page_links_the_served_chapter(served: Path) -> None:
    """An action's "Doc" link opens the chapter of the version that runs."""
    del served
    found = home_link(Doc("commands/audit/", "#en", "#fr"))
    assert found is not None
    assert found.url_en == "/docs/en/commands/audit/#en"


def test_the_site_hooks_resolve_links_with_the_same_module() -> None:
    """`hooks.py` loads `links.py` by path: the other language's page is the site's."""
    spec = importlib.util.spec_from_file_location("site_hooks", HOOKS)
    assert spec is not None
    assert spec.loader is not None
    hooks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hooks)
    page_file = DOCUMENTATION / "fr" / "start" / "02-keep-the-cache.md"
    config = SimpleNamespace(docs_dir=str(DOCUMENTATION), site_url="https://site/")
    page = SimpleNamespace(file=SimpleNamespace(abs_src_path=str(page_file)))
    source = (
        "[en](../../en/start/02-keep-the-cache.md#x) "
        "[ci](../../../.github/workflows/ci.yml)"
    )
    rewritten = hooks.on_page_markdown(source, page=page, config=config)
    assert "(https://site/start/02-keep-the-cache/#x)" in rewritten
    assert "blob/main/.github/workflows/ci.yml)" in rewritten
