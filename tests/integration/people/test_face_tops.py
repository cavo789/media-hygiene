"""0841: photos scanned before get the faces they lack, never renumbered."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.faces.models import FACE_MODEL, PhotoFaces
from media_hygiene.index.face_tops import add_found, is_topped
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services import people as people_service
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.subject_answers import Answering
from tests.support.faces import FakeRecipe
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_FACES = "SELECT path, number, x FROM faces ORDER BY path, number"
_AWAY = 100_000.0  # a box far from any face found: as if the old scan missed it


def test_an_old_scan_is_topped_up_its_faces_kept_and_the_missed_one_added(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scanned before 0841 (no `face_tops`): looked at again once, numbers kept."""
    del cli  # the coloured tree, audited
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    answering = Answering(True, NullProgress())  # noqa: FBT003
    with PeopleStep(make_runtime(locations)) as people:
        people.find(people.plan(()).missing, answering)
        connection = people.store.connection
        assert not people.plan(()).missing  # a new scan is marked topped
        faces = connection.execute(_FACES).fetchall()
        assert faces
        moved = faces[0][0]  # its face 0 lies elsewhere: the detector's face is new
        connection.execute("UPDATE faces SET x = ? WHERE path = ?", (_AWAY, moved))
        connection.execute("DELETE FROM face_tops")
        connection.commit()
        work = people.plan(())
        assert len(work.missing) == len(work.photos)  # faces or not
        assert work.new == 0  # analysed before: top-ups only
        outcome = people.find(work.missing, answering)
        assert (outcome.topped, outcome.added) == (len(work.missing), 1)
        after = connection.execute(_FACES).fetchall()
        assert (moved, 0, _AWAY) in after  # the old face keeps its number
        assert [row[1] for row in after if row[0] == moved] == [0, 1]
        assert len(after) == len(faces) + 1  # the others: found again, not doubled
        assert not people.plan(()).missing


def test_a_top_up_without_faces_marks_the_photo_and_keeps_its_count(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing new: the photo is marked, its count of faces unchanged."""
    del cli
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    with PeopleStep(make_runtime(locations)) as people:
        people.find(people.plan(()).missing, Answering(True, NullProgress()))  # noqa: FBT003
        connection = people.store.connection
        photo = people.plan(()).photos[0]
        connection.execute("DELETE FROM face_tops")
        version = (str(photo.path), photo.size, photo.mtime_ns)
        assert not is_topped(connection, "faces-test", version)
        before = connection.execute("SELECT faces FROM face_scans").fetchall()
        empty = PhotoFaces(photo.path, photo.size, photo.mtime_ns, (), 0.0)
        add_found(connection, FACE_MODEL, empty)
        assert is_topped(connection, FACE_MODEL, version)
        assert connection.execute("SELECT faces FROM face_scans").fetchall() == before
