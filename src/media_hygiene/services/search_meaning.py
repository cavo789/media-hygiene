"""`search` ranks by meaning when `tags` gave the photos their vectors (TODO 0263).

Whatever `[tags] meaning` says: the vectors are in the index, so they are used. The
model is read from the cache, never downloaded by a search (the cache may be
read-only); without it, the words alone answer, and the console says why.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.index.meaning_rows import vector_count
from media_hygiene.meaning.clip import MODEL
from media_hygiene.meaning.embedder import ClipWords
from media_hygiene.meaning.files import clip_known, clip_present
from media_hygiene.search.meaning import MeaningSource

if TYPE_CHECKING:
    from media_hygiene.search.meaning_index import MeaningIndex
    from media_hygiene.services.runtime import Runtime


def with_meaning(runtime: Runtime, search: MeaningIndex) -> None:
    """Rank by meaning when the index has vectors and the model is in the cache.

    Args:
        runtime: Settings, cache and output.
        search: The open index.
    """
    count = vector_count(search.connection, MODEL)
    if not count:
        return
    output = runtime.output
    cache = runtime.locations.cache_dir
    if not clip_present(cache):
        output.warning(
            _(
                "The photos have vectors, but the model of search by meaning is not "
                "in the cache: the words alone answer."
            )
        )
        output.tip(_("Run 'tags --meaning' once: it downloads the model again."))
        return
    settings = runtime.settings.tags
    load = partial(ClipWords, clip_known(cache), settings.meaning_threads)
    search.understand(MeaningSource(load, settings.meaning_results))
    output.info(
        ngettext(
            "Search by meaning: {count} photo can be found by what it shows.",
            "Search by meaning: {count} photos can be found by what they show.",
            count,
        ).format(count=human_number(count))
    )
