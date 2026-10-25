"""What the search page reads and writes through: the index, the desks of its routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.apply_api import ApplyDesk
    from media_hygiene.search.chosen_api import ChosenDesk
    from media_hygiene.search.folders import FolderDesk
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.people_desk import PeopleDesk
    from media_hygiene.search.rule_desk import RuleDesk
    from media_hygiene.share.album_api import AlbumDesk


@dataclass(frozen=True, slots=True)
class SearchPlace:  # pylint: disable=too-many-instance-attributes
    """Where the search reads, and how it writes paths: index, mapper, previews."""

    index: SearchIndex
    mapper: HostPathMapper
    previews: Path | None  # the cache folder of previews, if any
    people: PeopleSettings  # the names, to say when a `person:` word names nobody
    chosen: ChosenDesk  # the files set aside
    folders: FolderDesk  # the folder view
    apply: ApplyDesk  # *Apply now*, opened from the home page
    albums: AlbumDesk  # the albums, never the files set aside
    names: PeopleDesk  # a name taken off a photo (its cross), put back
    rules: RuleDesk  # *Make it a rule* of a period (0396)
