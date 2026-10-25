"""0344, 0346: the search says what the index holds, and how to write a search."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.services import search_pages
from media_hygiene.tags.models import TagSource
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.review.http import Response
    from media_hygiene.search.app import SearchApp


def _answers(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch, words: str
) -> tuple[dict[str, object], str]:
    """Open the search page, search `words`; the answer and the page."""
    seen: dict[str, Response] = {}

    async def act(app: SearchApp) -> None:
        seen["found"] = await _call(app, "POST /api/search", {"text": words})
        seen["page"] = await _call(app, "GET /search")

    monkeypatch.setattr(search_pages, "serve_until_ended", fake_server(act))
    assert run(cli, "search").exit_code == 0
    found: dict[str, object] = json.loads(seen["found"].body)
    return found, seen["page"].body.decode()


def test_before_tags_the_answer_says_nothing_is_described(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No word of any source yet: the counts say it, the model's words at 0."""
    found, _page = _answers(cli, monkeypatch, "chat")
    coverage = found["coverage"]
    assert isinstance(coverage, dict)
    assert int(coverage["files"]) > 0
    sources = coverage["sources"]
    assert isinstance(sources, dict)
    assert set(sources) == {source.value for source in TagSource}
    assert sources["vision"] == 0
    assert coverage["meaning"] is False


def test_after_tags_the_cheap_words_are_counted(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`tags --no-describe`: folders and dates have words, the model still none."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    found, _page = _answers(cli, monkeypatch, "durbuy")
    coverage = found["coverage"]
    assert isinstance(coverage, dict)
    sources = coverage["sources"]
    assert isinstance(sources, dict)
    assert int(sources["folder"]) > 0
    assert int(sources["date"]) > 0
    assert sources["vision"] == 0


def test_the_page_explains_every_source_and_the_tips(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each choice of *Words of* with its prefix; the three tips; the coverage line."""
    _found, page = _answers(cli, monkeypatch, "")
    assert '<p id="coverage" role="status" hidden></p>' in page
    for source in TagSource:
        assert f'data-source="{source.value}"' in page, source
        assert f"<code>{source.value}:</code>" in page
    assert "Every word must be found" in page
    assert "people are adult, child, baby or group" in page
    assert 'id="tipSentence"' in page
    assert 'id="tipMeaning" hidden' in page
