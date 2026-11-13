"""0815: the plan reads scanned and guessed versions at once, the same work."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.index.turn_rows import TurnStore
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services import people as people_service
from media_hygiene.services.people import PeopleStep, PeopleWork
from media_hygiene.services.people_files import people_photos, present_photos
from media_hygiene.services.subject_answers import Answering
from tests.support.faces import FakeRecipe
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def _one_by_one(people: PeopleStep) -> PeopleWork:
    """The plan as it was before 0815: one query per photo, twice.

    Args:
        people: The step, open.

    Returns:
        The work.
    """
    store = people.store
    photos, absent = present_photos(people_photos(store.connection, ()))
    turns = TurnStore(store.connection, FACE_MODEL)
    scanned = {p.path for p in photos if store.scanned(p)}
    missing = tuple(p for p in photos if p.path not in scanned or not turns.guessed(p))
    turn_only = sum(1 for p in missing if p.path in scanned)
    return PeopleWork(photos, missing, absent, turn_only)


def test_the_same_work_as_one_query_per_photo(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unscanned, changed (other mtime), turn-missing, other model: same work."""
    del cli  # the coloured tree, audited
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    with PeopleStep(make_runtime(locations)) as people:
        people.find(people.plan(()).missing, Answering(True, NullProgress()))  # noqa: FBT003
        connection = people.store.connection
        paths = [str(p.path) for p in people.plan(()).photos]
        assert len(paths) >= 4
        connection.execute("DELETE FROM face_scans WHERE path = ?", (paths[0],))
        connection.execute(
            "UPDATE face_scans SET mtime_ns = mtime_ns + 1 WHERE path = ?", (paths[1],)
        )
        connection.execute("DELETE FROM face_turns WHERE path = ?", (paths[2],))
        connection.execute(
            "UPDATE face_turns SET model = 'other' WHERE path = ?", (paths[3],)
        )
        work = people.plan(())
        assert work == _one_by_one(people)
        assert len(work.missing) == 4
        assert work.turn_only == 2
        analysed = sum(people.store.scanned(photo) for photo in work.photos)
        assert people.result(work).tally.photos == analysed == len(paths) - 2
