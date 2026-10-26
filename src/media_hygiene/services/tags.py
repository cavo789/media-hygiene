"""`tags`: the cheap words of every file, then what the vision model sees.

The folder, name, date and place words are recomputed at every run (seconds). The model
describes only the photos the cache lacks, one per set of identical files, burst
series and group of near duplicates; every photo then takes the cached answers.
"""

from __future__ import annotations

import shutil
from contextlib import ExitStack
from dataclasses import replace
from typing import TYPE_CHECKING, Self

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.constants import FFMPEG_BINARY
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.i18n import active_locale
from media_hygiene.index.descriptions import DescriptionStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.services.tag_derive import model_rows
from media_hygiene.services.tag_files import tag_files
from media_hygiene.services.tag_near import near_search
from media_hygiene.services.tag_work import TagWork, stills_of, version_of
from media_hygiene.tags.context import tag_context
from media_hygiene.tags.models import CHEAP_SOURCES, MODEL_SOURCES, FileTags
from media_hygiene.tags.near_share import near_shared
from media_hygiene.tags.normalize import WordRules
from media_hygiene.tags.producers import cheap_tags
from media_hygiene.tags.selection import STILLS, WITH_VIDEOS, vision_plan
from media_hygiene.tags.vision import prompt_version

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


class TagStep:
    """Computes and stores the tags of a run; the index stays open in its `with`."""

    def __init__(self, runtime: Runtime) -> None:
        """Prepare the step.

        Args:
            runtime: Settings, cache file, process pool.
        """
        settings = runtime.settings
        self._runtime = runtime
        self._ai = settings.classify.ai
        self._rules = WordRules.of(settings.tags, active_locale())
        self._stack = ExitStack()
        self._opened: tuple[FactsRepository, DescriptionStore] | None = None

    def __enter__(self) -> Self:
        """Open the index.

        Returns:
            The step.
        """
        repository = self._stack.enter_context(
            FactsRepository.open(self._runtime.index_file)
        )
        asked = (self._ai.model, prompt_version(self._rules.language))
        self._opened = (repository, DescriptionStore(repository.connection, asked))
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Commit and close the index.

        Args:
            *exc_info: Exception details from the `with` statement (unused).
        """
        self._opened = None
        self._stack.close()

    @property
    def runtime(self) -> Runtime:
        """The settings, cache file and process pool of the run.

        Returns:
            The runtime.
        """
        return self._runtime

    @property
    def rules(self) -> WordRules:
        """The language and stop words of `[tags]`.

        Returns:
            The rules.
        """
        return self._rules

    @property
    def store(self) -> DescriptionStore:
        """The cached answers of the configured model to the `tags` question.

        Returns:
            The store.
        """
        return self._open()[1]

    @property
    def vision_on(self) -> bool:
        """Tell whether a vision model is set in `[classify.ai]`.

        Returns:
            True when `model` is not empty.
        """
        return bool(self._ai.model)

    def plan(self, within: Sequence[Path]) -> TagWork:
        """Read the files of the run and find the photos to describe.

        Args:
            within: Container folders (`--path`); empty: the whole index.

        Returns:
            The work of the run.
        """
        repository, store = self._open()
        files = tag_files(self._runtime, repository.connection, within)
        ffmpeg = shutil.which(FFMPEG_BINARY)
        kinds = STILLS if ffmpeg is None else WITH_VIDEOS
        vision = near_shared(
            vision_plan(files, self._ai.min_edge, kinds),
            files,
            near_search(self._runtime, repository, videos=ffmpeg is not None),
        )
        missing = tuple(
            version_of(file)
            for file in vision.asked
            if self.vision_on and store.get(version_of(file)) is None
        )
        seconds = store.seconds_per_photo() or self._ai.seconds_per_photo
        return TagWork(files, vision, missing, seconds, stills_of(vision.asked, ffmpeg))

    def cheap(self, work: TagWork) -> int:
        """Recompute the folder, name, date and place tags of every file of the run.

        Args:
            work: The files.

        Returns:
            How many tags were written.
        """
        settings = self._runtime.settings
        context = tag_context(settings, self._rules)
        if any(located_point(file.metadata) for file in work.files):
            towns = Gazetteer.load().renamed(settings.classify.town_names)
            context = replace(context, towns=towns)
        rows = [
            FileTags(version_of(file), cheap_tags(file, context)) for file in work.files
        ]
        return TagStore(self._open()[0].connection).replace(CHEAP_SOURCES, rows)

    def derive(self, work: TagWork) -> int:
        """Write the model's tags of every photo whose answer is in the cache.

        A photo takes its own answer, else the one of the photo that answers for it
        (its identical copy, its burst's best shot, its near group's version kept).
        The others keep what an earlier model or prompt gave them.

        Args:
            work: The files and who answers for whom.

        Returns:
            How many photos have the model's tags.
        """
        if not self.vision_on:
            return 0
        rows = model_rows(work, self._open()[1], self.sight)
        TagStore(self._open()[0].connection).replace(MODEL_SOURCES, rows)
        return len(rows)

    @property
    def sight(self) -> tuple[WordRules, str]:
        """What turns an answer into words: the rules of `[tags]`, the model.

        Returns:
            Both.
        """
        return self._rules, self._ai.model

    def _open(self) -> tuple[FactsRepository, DescriptionStore]:
        """The open index and descriptions.

        Returns:
            Both.

        Raises:
            RuntimeError: The step is used outside its `with` block.
        """
        if self._opened is None:
            message = "TagStep used outside its with block"
            raise RuntimeError(message)
        return self._opened
