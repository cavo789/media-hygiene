"""`people`: find the faces the index lacks, then group them all; or forget them all.

The faces are kept in the index (`/cache`) and never leave it. The models are
downloaded once into `/cache/models`, their SHA-256 checked (`faces.weights`).
"""

from __future__ import annotations

import asyncio
import secrets
from contextlib import ExitStack
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Self

from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.i18n import _
from media_hygiene.index.face_rows import FaceStore, FaceTally
from media_hygiene.index.moves import load_moves
from media_hygiene.index.repository import FactsRepository
from media_hygiene.people.naming import Known
from media_hygiene.scan.progress import Step
from media_hygiene.services.people_files import people_photos, present_photos
from media_hygiene.services.people_find import FindDeps, FindOutcome, find_all
from media_hygiene.services.people_groups import group_people
from media_hygiene.services.people_models import face_recipe
from media_hygiene.services.people_names import PeopleResult, named_photos

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.subject_answers import Answering


@dataclass(frozen=True, slots=True)
class PeopleWork:
    """The photos of a run, those whose faces the index lacks, those not here."""

    photos: tuple[PhotoVersion, ...]
    missing: tuple[PhotoVersion, ...]
    absent: int = 0  # in the index, not on disk: their folder is not mounted


class PeopleStep:
    """Finds, groups and forgets faces; the index stays open in its `with`."""

    def __init__(self, runtime: Runtime, model: str = FACE_MODEL) -> None:
        """Prepare the step.

        Args:
            runtime: Settings, cache file, process pool.
            model: The pair of models the faces belong to.
        """
        self._runtime = runtime
        self._model = model
        self._stack = ExitStack()
        self._store: FaceStore | None = None

    def __enter__(self) -> Self:
        """Open the index.

        Returns:
            The step.
        """
        repository = self._stack.enter_context(
            FactsRepository.open(self._runtime.index_file)
        )
        self._store = FaceStore(repository.connection, self._model)
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Commit and close the index.

        Args:
            *exc_info: Exception details from the `with` statement (unused).
        """
        self._store = None
        self._stack.close()

    @property
    def store(self) -> FaceStore:
        """The faces of the index.

        Returns:
            The store.

        Raises:
            RuntimeError: The step is used outside its `with` block.
        """
        if self._store is None:
            message = "PeopleStep used outside its with block"
            raise RuntimeError(message)
        return self._store

    def plan(self, within: Sequence[Path]) -> PeopleWork:
        """List the photos of the run (on disk) and those not analysed yet.

        Args:
            within: Container folders (`--path`); empty: the whole index.

        Returns:
            The work.
        """
        store = self.store
        photos, absent = present_photos(people_photos(store.connection, within))
        missing = tuple(p for p in photos if not store.scanned(p))
        return PeopleWork(photos, missing, absent)

    def find(self, photos: Sequence[PhotoVersion], answering: Answering) -> FindOutcome:
        """Find the faces of photos, each one committed at once.

        Args:
            photos: The photos to analyse.
            answering: Progress and Ctrl+C.

        Returns:
            How it went.
        """
        recipe = face_recipe(self._runtime)
        progress = answering.progress
        with self._runtime.executor_factory() as executor:
            deps = FindDeps(recipe, self.store, executor, progress, answering.stopped)
            progress.start(
                Step(_("Finding faces"), _("two small local models: nothing is sent")),
                len(photos),
            )
            try:
                return asyncio.run(find_all(photos, deps))
            finally:
                progress.stop()

    def sample(self, work: PeopleWork, count: int) -> tuple[PhotoVersion, ...]:
        """Pick photos at random among those not analysed yet.

        Args:
            work: The work of a full run.
            count: How many.

        Returns:
            The photos picked.
        """
        missing = list(work.missing)
        picked = secrets.SystemRandom().sample(missing, min(count, len(missing)))
        return tuple(picked)

    def result(self, work: PeopleWork) -> PeopleResult:
        """Group the faces of the photos of the run, count them, name them.

        The faces of photos not mounted this time stay in the index, and still
        name people, but are not shown: the page could not cut them out.

        Args:
            work: The photos of the run.

        Returns:
            The groups, the counts, every face of the index and the people named.
        """
        store = self.store
        every = store.faces()
        shown = {photo.path for photo in work.photos}
        faces = tuple(face for face in every if face.path in shown)
        settings = self._runtime.settings.people
        analysed = sum(store.scanned(photo) for photo in work.photos)
        moves = load_moves(store.connection)
        return PeopleResult(
            group_people(faces, settings),
            FaceTally(analysed, len(faces), store.tally().seconds_per_photo),
            every,
            named_photos(faces, Known.of(every, settings, moves)),
            MappingProxyType(moves),
        )
