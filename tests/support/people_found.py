"""The people step over the coloured tree, its faces found by the fake recipe."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from media_hygiene.scan.progress import NullProgress
from media_hygiene.services import people as people_service
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.subject_answers import Answering
from tests.support.faces import FakeRecipe
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pytest

    from media_hygiene.paths.locations import Locations


@contextlib.contextmanager
def faces_found(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> Iterator[PeopleStep]:
    """Find the faces of every photo once, with the fake recipe.

    Args:
        locations: The mounts (the tree audited).
        monkeypatch: The test's patcher.

    Yields:
        The people step, open.
    """
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    with PeopleStep(make_runtime(locations)) as people:
        people.find(people.plan(()).missing, Answering(True, NullProgress()))  # noqa: FBT003
        yield people
