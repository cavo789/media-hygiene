"""0357: the home server serves `review --near` itself, under `/review/near/`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.review.step_watch import served_here
from media_hygiene.services import import_bursts
from tests.support.home_serving import serve_home

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_the_near_review_is_served_under_its_prefix(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page, its state, a preview and a decision, all through the home server."""
    assert served_here(("review", "--near")) == "/review/near/"
    choice = {"choices": [{"group": 0, "action": "swap"}]}
    answers = serve_home(
        cli,
        monkeypatch,
        [
            ("GET /review/near", None),
            ("GET /review/near/", None),
            ("GET /review/near/api/state", None),
            ("POST /review/near/api/near", choice),
            ("GET /review/near/api/file", None),
            ("GET /api/state", None),
        ],
    )
    redirect, page, state, decided, held, home_state = (*answers,)  # pylint: disable=unbalanced-tuple-unpacking
    assert redirect.status == 303
    assert "Location: /review/near/" in redirect.headers
    assert page.status == 200
    assert '"api/state"' in page.body.decode()  # relative: answered under the prefix
    groups = json.loads(state.body)["groups"]
    assert groups
    preview = groups[0]["kept"]["preview"]
    assert preview.startswith("preview/")
    assert decided.status == 200
    assert json.loads(held.body)["entries"][0]["action"] == "swap"
    assert (locations.reports_dir / "decisions.json").exists()
    assert "actions" in json.loads(home_state.body)  # the home page keeps its paths


def test_before_the_page_nothing_answers(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The review's API waits for its page: no session yet."""
    answer = serve_home(cli, monkeypatch, [("GET /review/near/api/state", None)])[0]
    assert answer.status == 404


def test_the_other_reviews_are_served_under_their_prefixes(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0417: the burst series, the pairs, the junk and the files gone, the same way."""
    pages = {
        ("review",): "/review/bursts/",
        ("review", "--pairs"): "/review/pairs/",
        ("review", "--junk"): "/review/junk/",
        ("review", "--gone"): "/review/gone/",
    }
    asked: list[tuple[str, object]] = []
    for words, page in pages.items():
        assert served_here(words) == page
        asked += [(f"GET {page}", None), (f"GET {page}api/state", None)]
    answers = serve_home(cli, monkeypatch, asked)
    for at, page in enumerate(pages.values()):
        shown, state = answers[2 * at], answers[2 * at + 1]
        assert shown.status == 200, page
        if state.status == 404:  # nothing to review: the page said so
            assert b"nothing to review" in shown.body, page
            continue
        assert '"api/state"' in shown.body.decode(), page
        assert '"/preview/' not in state.body.decode(), page  # relative to the page


def _chain(locations: Locations) -> None:
    said = {"steps": ["bursts"], "at": "bursts", "state": "done"}
    chain = {**said, "folder": "C:\\Phone", "since": "all"}
    (locations.cache_dir / "import-chain.json").write_text(json.dumps(chain), "utf-8")


def test_the_chain_opens_the_imports_series_only(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0630: `?imported` shows the import's series and says so; none: nothing."""
    _chain(locations)
    files = tuple(path for path in locations.data_dir.rglob("*") if path.is_file())
    found: list[tuple[Path, ...]] = [files, ()]
    monkeypatch.setattr(import_bursts, "imported", lambda *_: found.pop(0))
    page = "/review/bursts/"
    asked: list[tuple[str, object]] = [(f"GET {page}?imported", None)]
    asked.append((f"GET {page}api/state", None))
    asked += [(f"GET {page}?imported", None), (f"GET {page}", None)]
    answers = serve_home(cli, monkeypatch, asked)
    every, state, none, whole = (*answers,)  # pylint: disable=unbalanced-tuple-unpacking
    assert every.status == 200
    assert 'id="importedOnly"' in every.body.decode()
    assert 'href="./"' in every.body.decode()  # every series, one click away
    assert 'id="applyNow"' in every.body.decode()
    assert json.loads(state.body)
    assert b"nothing to review" in none.body
    assert 'id="everySeries" href="./"' in none.body.decode()  # 0630
    assert 'id="importedOnly"' not in whole.body.decode()
