"""The pages resist hostile names, and refuse any script they did not write (0671).

Names come from outside: a photo received by mail, a NAS folder (Linux allows `<` `>`
`"`), EXIF and XMP fields, album, person, tag and place names. Two locks: every value
reaches the markup escaped (the served HTML here, the scripts' template literals by the
lint of `tests/support/html_sinks.py`), and the policy runs only the scripts carrying
the answer's nonce, so a forgotten `esc` shows text instead of running it.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import json
import re
from http import HTTPStatus
from pathlib import Path
from typing import Final

import pytest
from rich.console import Console

from media_hygiene.places.app import PAGE_POLICY
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.nonce import NONCE_MARK, REVIEW_POLICY, hashed_policy, sealed
from media_hygiene.review.page_header import PAGE_STEPS
from media_hygiene.review.report_files import report_response
from media_hygiene.review.respond import write_response
from media_hygiene.review.serving import json_response
from tests.support.html_sinks import SOURCES, Context, Hole, all_holes, is_safe
from tests.support.page_render import render_page

HOSTILE: Final = (
    "<img src=x onerror=window.__pwned=1>\"'`${alert(1)}"
    "</script><script>alert(1)</script>"
)
_TEMPLATES: Final = sorted(SOURCES.rglob("*.j2"))
_SCRIPT_TAG: Final = re.compile(r"<script\b[^>]*>")
_CONSOLE: Final = "console_"
_NONCED_TAG: Final = '<script nonce="{{ page_nonce }}"'
# Interpolations the lint cannot prove, each read by hand: (template, expression) → why.
EXCEPTIONS: Final = {
    (
        "home_draw.js.j2",
        'out.join("")',
    ): "pills built by riskPill and literals, each escaped",
    (
        "home_draw.js.j2",
        "image(`meerkat-${pose}.webp`)",
    ): "an asset path from POSE constants",
    (
        "home_draw.js.j2",
        "image(`meerkat-${POSE[space.id]}.webp`)",
    ): "same, POSE constants",
    ("home_draw.js.j2", 'image("avatar.webp")'): "a fixed asset path",
    ("home_draw.js.j2", "tileTarget(t)"): "data attributes built with esc",
    (
        "home_draw.js.j2",
        'TILE_PILL()[t.pill] || ""',
    ): "the tool's own pills, texts escaped",
    (
        "home_draw.js.j2",
        "EXTRAS.albums()",
    ): "a block builder of EXTRAS, its literals linted",
    ("home_draw.js.j2", "marker"): "icon() or String(a step number)",
    ("home_draw.js.j2", "extra"): "an EXTRAS builder's markup",
    ("home_draw.js.j2", "top"): "EXTRAS builders' markup, joined",
    ("home_favs.js.j2", "grip"): "a literal whose only value is esc(T.favMove)",
    ("home_favs.js.j2", "cards"): "literals mapped and joined, each value escaped",
    ("home_imports.js.j2", "marks"): "literals mapped and joined, each value escaped",
    ("home_scope.js.j2", "kinds"): "names mapped through esc, then joined",
    ("home_scope.js.j2", "names"): "names mapped through esc, then joined",
    ("home_tags.js.j2", "steps"): "literals mapped and joined, each value escaped",
    ("home_tile_edit.js.j2", "attr"): "a constant attribute each caller writes",
    ("home_tile_edit.js.j2", "text"): "a constant arrow or cross each caller writes",
    (
        "home_tile_edit.js.j2",
        '(edit ? S.tiles.map(editTile) : S.tiles.map(tile)).join("")',
    ): ("two markup builders, their literals linted"),
    ("album.js.j2", "label"): "const label = esc(fill(T.renameAsk, { name }))",
    ("album.js.j2", "cover"): "an <img> literal, its values escaped, or empty",
}


def _key(hole: Hole) -> tuple[str, str]:
    """The key of a hole in `EXCEPTIONS`."""
    return Path(hole.file).name, hole.expression


def test_every_markup_interpolation_is_escaped_or_named() -> None:
    """A `${…}` in a markup literal goes through esc/icon/number…, or is named."""
    holes = all_holes()
    unexplained = [hole for hole in holes if _key(hole) not in EXCEPTIONS]
    assert unexplained == []
    stale = set(EXCEPTIONS) - {_key(hole) for hole in holes}
    assert stale == set()


@pytest.mark.parametrize(
    ("expression", "safe"),
    [
        ("esc(file.name)", True),
        ("file.name", False),
        ('on ? "true" : "false"', True),
        ("ok ? esc(a) : b", False),
        ("items.length", True),
        ('names.map((name) => esc(name)).join("")', True),
        ("T.title", True),
        ("raw(x)", False),
    ],
)
def test_the_lint_tells_safe_from_unproven(expression: str, *, safe: bool) -> None:
    """The lint's judgement on a few interpolations."""
    assert is_safe(expression, Context("", frozenset())) is safe


@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_a_hostile_name_reaches_every_page_escaped(template: str) -> None:
    """Every value of a page set to a hostile name: shown as text, never as markup."""
    page = render_page(template, HOSTILE)
    if template.startswith(_CONSOLE):  # `html`: Rich's escaped export (test below)
        page = page.replace(f"<pre>{HOSTILE}</pre>", "<pre></pre>")
    assert "<img src=x onerror" not in page
    assert "<script>alert(1)" not in page
    # A `</script>` inside inline data would end the script early: one end per start.
    assert page.count("</script>") == len(_SCRIPT_TAG.findall(page))


def test_a_console_page_shows_a_hostile_name_as_text() -> None:
    """What a console step printed reaches its page through Rich's escaped export."""
    console = Console(record=True, width=200, file=io.StringIO())
    console.print(HOSTILE, markup=False)
    exported = console.export_html(inline_styles=True, code_format="{code}")
    assert "<img" not in exported
    assert "<script>" not in exported


@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_every_script_of_a_page_carries_the_mark(template: str) -> None:
    """Rendered, each `<script>` carries the mark the answer replaces by its nonce."""
    page = render_page(template)
    tags = _SCRIPT_TAG.findall(page)
    assert tags
    assert all(f'nonce="{NONCE_MARK}"' in tag for tag in tags)


@pytest.mark.parametrize("path", _TEMPLATES, ids=lambda path: path.name)
def test_every_script_tag_of_every_template_has_its_nonce(path: Path) -> None:
    """No `<script` without `nonce=`, no inline handler, no `javascript:` URL."""
    source = re.sub(r"\{#.*?#\}", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
    for found in re.finditer(r"<script(?=[\s>])", source):
        assert source.startswith(_NONCED_TAG, found.start()), source[found.start() :][
            :60
        ]
    assert re.search(r"<[a-z][^>]*\son[a-z]+\s*=", source) is None
    assert "javascript:" not in source.lower()


def test_no_policy_allows_inline_scripts() -> None:
    """`'unsafe-inline'` is gone from `script-src`, the places page's included."""
    for policy in (REVIEW_POLICY, PAGE_POLICY):
        scripts = next(part for part in policy.split(";") if "script-src" in part)
        assert "'unsafe-inline'" not in scripts
        assert f"'nonce-{NONCE_MARK}'" in scripts


def test_each_answer_draws_its_own_nonce() -> None:
    """Two answers of one page: two nonces, each the same in body and policy."""
    page = f'<script nonce="{NONCE_MARK}">go()</script>'.encode()
    response = Response(HTTPStatus.OK, page, ContentType.HTML)
    first, second = sealed(response), sealed(response)
    nonces = [
        re.findall(r"'nonce-([^']+)'", policy)[0] for _b, policy in (first, second)
    ]
    assert nonces[0] != nonces[1]
    assert NONCE_MARK not in first[1]
    assert f'nonce="{nonces[0]}"'.encode() in first[0]


def test_a_cacheable_answer_keeps_the_run_nonce() -> None:
    """A body the browser keeps and revalidates (304) keeps the run's nonce."""
    response = Response(
        HTTPStatus.OK, b"<script nonce=x>", ContentType.HTML, cacheable=True
    )
    assert sealed(response)[1] == sealed(response)[1]


def test_a_json_answer_is_left_as_it_is() -> None:
    """Only HTML bodies are changed: a JSON one holding the mark stays as it is."""
    body = f'{{"a": "{NONCE_MARK}"}}'.encode()
    assert sealed(Response(HTTPStatus.OK, body, ContentType.JSON))[0] == body


def test_a_report_on_disk_runs_by_its_scripts_hashes(tmp_path: Path) -> None:
    """A report written earlier lacks this answer's nonce: its scripts go by SHA-256."""
    code = "document.title = 'x';"
    (tmp_path / "index.html").write_text(
        f"<p>{HOSTILE.replace('<', '&lt;')}</p><script>{code}</script>",
        encoding="utf-8",
    )
    response = asyncio.run(report_response(tmp_path, "/reports/index.html"))
    digest = base64.b64encode(hashlib.sha256(code.encode()).digest()).decode()
    assert f"'sha256-{digest}'" in response.policy
    assert "'unsafe-inline'" not in response.policy.split("script-src")[1].split(";")[0]


def test_a_page_without_scripts_keeps_the_policy() -> None:
    """Nothing to hash: the policy as it was."""
    assert hashed_policy(REVIEW_POLICY, b"<p>no script</p>") == REVIEW_POLICY


class _Writer:
    """A connection keeping what is written to it."""

    def __init__(self) -> None:
        """Nothing written yet."""
        self.data = b""

    def write(self, data: bytes) -> None:
        """Keep what is written."""
        self.data += data

    async def drain(self) -> None:
        """Nothing to wait for."""


def test_the_written_answer_carries_the_same_nonce_twice() -> None:
    """On the wire: the header's nonce is the one the page's scripts carry."""
    writer = _Writer()
    page = f'<script nonce="{NONCE_MARK}">go()</script>'.encode()
    asyncio.run(write_response(writer, Response(HTTPStatus.OK, page, ContentType.HTML)))  # type: ignore[arg-type]
    head, _blank, body = writer.data.partition(b"\r\n\r\n")
    nonce = re.search(rb"'nonce-([^']+)'", head).group(1)  # type: ignore[union-attr]
    assert b'nonce="' + nonce + b'"' in body
    assert int(re.search(rb"Content-Length: (\d+)", head).group(1)) == len(body)  # type: ignore[union-attr]


def test_a_json_answer_carries_a_hostile_name_as_data() -> None:
    """A JSON answer is never read as a page: its type is said and sniffing refused.

    The scripts insert its values through the linted escaping; the browser itself
    never renders it, even opened directly, so a hostile name stays a string.
    """
    writer = _Writer()
    answer = json_response(HTTPStatus.OK, {"name": HOSTILE, "names": [HOSTILE]})
    asyncio.run(write_response(writer, answer))  # type: ignore[arg-type]
    head, _blank, body = writer.data.partition(b"\r\n\r\n")
    assert b"Content-Type: application/json" in head
    assert b"X-Content-Type-Options: nosniff" in head
    assert b"script-src 'nonce-" in head
    assert json.loads(body) == {"name": HOSTILE, "names": [HOSTILE]}
