"""The people seen in a show, for the remote's "Avoid some people" (0825).

Only the people named (`[[people.person]]`) who show on at least one photo of the
selection are offered, with their count: a show of 150 holiday photos lists the few
people on them, not every name of the collection, so the one to avoid is not lost in
a long list. Each count says how sure it is: ✓ a face named as theirs, ≈ a face only
close to their mean (the guess of `/person`): a name seen only by ≈ may be a stranger
who looks like them. Same generous match as the avoiding itself (`paths_by_name`), so
a name offered sets out exactly the photos it counted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.services.slideshow_avoid import named_people, paths_by_name
from media_hygiene.slideshow.avoid_desk import AvoidDesk, Memory
from media_hygiene.slideshow.avoid_memory import known_of, remembered
from media_hygiene.slideshow.avoid_seen import Seen

if TYPE_CHECKING:
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.slideshow.desk import Desk


def avoid_desk(runtime: Runtime, desk: Desk, search: SearchIndex) -> AvoidDesk:
    """The remote's people to avoid, for the show of a desk.

    Args:
        runtime: Settings, mount points and the host mapper.
        desk: The show whose photos are matched.
        search: The open index, naming the file of each key.

    Returns:
        The desk, finding the people of the show when the remote first asks,
        starting from those `[slideshow] avoid` remembers (read from the disk).
    """

    def present() -> dict[str, Seen]:
        """The people on the show's photos, alphabetical, and the keys of theirs.

        Returns:
            By name, the keys of the show's photos they are on, named (✓) or guessed
            (≈); nobody seen: empty.
        """
        keys = {
            photo.path: slide.key
            for slide in desk.show.slides
            if (photo := search.source_of(slide.key))
        }
        found = paths_by_name(runtime, named_people(runtime))
        seen = {
            name: Seen(
                frozenset(keys[path] for path in photos.sure if path in keys),
                frozenset(keys[path] for path in photos.guessed if path in keys),
            )
            for name, photos in found.items()
        }
        return {name: on for name, on in seen.items() if on.sure or on.guessed}

    config_file = runtime.locations.config_file
    names = known_of(remembered(config_file), named_people(runtime))
    return AvoidDesk(present, memory=Memory(config_file, names))
