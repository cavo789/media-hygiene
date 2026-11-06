"""0640: a first sort offers the latest month first, on the console and on the page."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from http import HTTPStatus
from types import SimpleNamespace
from typing import TYPE_CHECKING

from media_hygiene.cli.sort_offer import offer_trial
from media_hygiene.review.http import Request
from media_hygiene.search.events_choose import events_get, sort_post
from media_hygiene.search.events_desk import EventsDesk
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.trial_api import (
    TRIAL_PATH,
    TRIAL_REST_PATH,
    TRIAL_RUN_PATH,
)
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from media_hygiene.services.sort_reviewing import open_sort_review
from media_hygiene.services.sort_trial import LATEST, first_sample, only_trial
from media_hygiene.services.sort_trial_page import SortTrial
from tests.integration.test_sort_event import SPRING, SPRING_SHOTS, two_events
from tests.support.cli import run
from tests.support.sorting import PARTY

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_models import Prepared

_JSON = {"host": "127.0.0.1", "content-type": "application/json"}


def _whole(runtime: Runtime, workbook: Path) -> tuple[Prepared, SortTrial]:
    """The whole sort, ready, and the page's trial."""
    trial = SortTrial(runtime)
    inputs = load_inputs(runtime, find_workbook(runtime, str(workbook)))
    return trial._service().prepare(inputs), trial  # noqa: SLF001  # pylint: disable=protected-access


def _desk(runtime: Runtime, search: SearchIndex) -> EventsDesk:
    """The Events view with its trial."""
    return EventsDesk(
        search,
        runtime.mapper,
        lambda: open_sort_review(runtime, None),
        frozenset,
        trial=SortTrial(runtime),
    )


def _post(desk: EventsDesk, path: str) -> dict[str, object]:
    """Post a route of the trial; it must succeed.

    Returns:
        Its answer.
    """
    request = Request("POST", path, _JSON, b"{}")
    answer = asyncio.run(sort_post(desk, request))
    assert answer.status == HTTPStatus.OK, answer.body
    said: dict[str, object] = json.loads(answer.body)
    return said


def _offered(desk: EventsDesk) -> dict[str, object] | None:
    """Ask the page's offer.

    Returns:
        It, or None.
    """
    answer = events_get(desk, TRIAL_PATH)
    assert answer is not None
    said: dict[str, dict[str, object] | None] = json.loads(answer.body)
    return said["offer"]


def test_the_question_offers_the_month_then_the_whole_sort(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Yes: the sample; no: None, the whole sort's question next; no terminal: none."""
    runtime, workbook, _sizes = two_events(locations)
    whole, trial = _whole(runtime, workbook)
    asked: list[str] = []

    def answer(_self: object, question: str) -> bool:
        asked.append(question)
        return len(asked) == 1

    monkeypatch.setattr("media_hygiene.console.output.Output.confirm", answer)
    prepare = trial._service().prepare  # noqa: SLF001  # pylint: disable=protected-access
    assert offer_trial(runtime, whole, prepare) is None  # no terminal in tests
    assert not asked
    terminal = SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("media_hygiene.cli.sort_offer.sys", terminal)
    sample = offer_trial(runtime, whole, prepare)
    assert sample is not None
    assert len(sample.plan.moves) < len(whole.plan.moves)
    assert offer_trial(runtime, whole, prepare) is None
    assert str(len(whole.plan.moves)) in asked[0]


def test_the_command_runs_the_month_on_a_yes(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A yes at the first question: only the month moves, the rest is suggested."""
    two_events(locations)
    before = len(list((locations.data_dir / PARTY).glob("*.jpg")))
    terminal = SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("media_hygiene.cli.sort_offer.sys", terminal)
    monkeypatch.setattr(
        "media_hygiene.console.output.Output.confirm", lambda _self, _question: True
    )
    result = run(cli, "sort")
    assert result.exit_code == 0, result.output
    assert "Sort the rest" in result.output
    spring = locations.data_dir / SPRING
    assert len(list(spring.glob("*.jpg"))) == SPRING_SHOTS  # an older month: stays
    assert len(list((locations.data_dir / PARTY).glob("*.jpg"))) == before
    assert "1 of 1 moves verified" in " ".join(result.output.split())


def test_no_offer_once_files_moved_or_with_one_month(locations: Locations) -> None:
    """A later sort is not offered a trial; nor a plan whose month is all there is."""
    runtime, workbook, _sizes = two_events(locations)
    whole, trial = _whole(runtime, workbook)
    service = trial._service()  # noqa: SLF001  # pylint: disable=protected-access
    sample = first_sample(runtime, whole, service.prepare)
    assert sample is not None
    one_month = first_sample(runtime, sample, service.prepare)
    assert one_month is None
    service.execute(sample, lambda: False)
    again = service.prepare(whole.inputs)
    assert first_sample(runtime, again, service.prepare) is None


def test_latest_is_a_month_with_files_to_move(locations: Locations) -> None:
    """The latest month holding only files in place is not the sample."""
    runtime, workbook, _sizes = two_events(locations)
    inputs = load_inputs(runtime, find_workbook(runtime, str(workbook)))
    moving = [row for row in inputs.plan.rows if row.date]
    newest = max(moving, key=lambda row: row.date or "")
    rows = tuple(
        row.model_copy(update={"values": None})
        if (row.date or "")[:7] == (newest.date or "")[:7]
        else row
        for row in inputs.plan.rows
    )
    plan = inputs.plan.model_copy(update={"rows": rows})
    cut = only_trial(replace(inputs, plan=plan), LATEST, runtime.mapper)
    assert all((row.date or "")[:7] != (newest.date or "")[:7] for row in cut.plan.rows)


def test_the_page_tries_shows_undoes_then_sorts_the_rest(locations: Locations) -> None:
    """Offer, trial with its tiles at their new place, undo, trial again, the rest."""
    runtime, _workbook, _sizes = two_events(locations)
    data = locations.data_dir
    with SearchIndex.open(locations.index_file) as search:
        desk = _desk(runtime, search)
        offer = _offered(desk)
        assert offer is not None
        files = offer["files"]
        assert isinstance(files, int)
        assert offer["total"] != files
        folders = offer["folders"]
        assert isinstance(folders, list)
        assert folders
        done = _post(desk, TRIAL_RUN_PATH)
        assert done["intact"]
        assert done["moved"] == files
        hits = done["hits"]
        assert isinstance(hits, list)
        assert len(hits) == files
        shown = {hit["folder"] for hit in hits}
        assert shown == {folder["folder"] for folder in folders}
        assert _offered(desk) is None  # a run of the plan exists
        run_id = done["run_id"]
        assert isinstance(run_id, str)
        assert PageUndo(runtime).undo(run_id).back == files
        assert _offered(desk) is not None  # undone: offered again
        _post(desk, TRIAL_RUN_PATH)
        rest = _post(desk, TRIAL_REST_PATH)
        assert rest["intact"]
        assert rest["rest"] == 0
        assert not list((data / PARTY).glob("*.jpg"))
        assert not list((data / SPRING).glob("*.jpg"))
        assert _post(desk, TRIAL_REST_PATH)["run_id"] == ""


def test_a_page_without_a_trial_says_so(locations: Locations) -> None:
    """No desk trial: no offer, 404; a trial with nothing to try: a sentence."""
    runtime, _workbook, _sizes = two_events(locations)
    with SearchIndex.open(locations.index_file) as search:
        bare = EventsDesk(
            search, runtime.mapper, lambda: open_sort_review(runtime, None), frozenset
        )
        assert _offered(bare) is None
        request = Request("POST", TRIAL_RUN_PATH, _JSON, b"{}")
        assert asyncio.run(sort_post(bare, request)).status == HTTPStatus.NOT_FOUND
        desk = _desk(runtime, search)
        _post(desk, TRIAL_REST_PATH)
        late = asyncio.run(sort_post(desk, request))
        assert late.status == HTTPStatus.CONFLICT
