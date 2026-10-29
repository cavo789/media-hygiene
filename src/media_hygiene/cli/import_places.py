"""After an `import`: offer to name the new photos' places online (0474).

A position leaves the machine only after an explicit Yes, asked each time (default
No), unless `[places] reverse_lookup = "always"`; `never`, an empty
`[places] nominatim_url` or `--yes` (no one to ask) send nothing.
"""

from __future__ import annotations

from importlib.metadata import version
from typing import TYPE_CHECKING

import typer

from media_hygiene.constants import HOME_PAGE
from media_hygiene.geo.nominatim import Service
from media_hygiene.geo.reverse import ReverseLookup
from media_hygiene.i18n import _, active_locale, ngettext
from media_hygiene.places.osm_search import DISTRIBUTION
from media_hygiene.services.place_names import name_spots, photo_points, unnamed_spots

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.geo.reverse import Pace
    from media_hygiene.services.runtime import Runtime


def offer_place_names(
    runtime: Runtime, copied: Sequence[Path], pace: Pace | None = None
) -> None:
    """Ask, then name the new photos' places online.

    Args:
        runtime: Settings (`[places]`), the cache folder, the output.
        copied: The photos the import copied.
        pace: How requests are sent (a fake server in tests).
    """
    places = runtime.settings.places
    if places.reverse_lookup == "never" or not places.nominatim_url or not copied:
        return
    spots = unnamed_spots(runtime, photo_points(copied))
    if not spots:
        return
    output = runtime.output
    question = ngettext(
        "{n} new place found. Look up its name online (OpenStreetMap)? Its "
        "position, rounded to about 100 m, is sent to {url}.",
        "{n} new places found. Look up their names online (OpenStreetMap)? Their "
        "positions, rounded to about 100 m, are sent to {url}.",
        len(spots),
    ).format(n=len(spots), url=places.nominatim_url)
    if places.reverse_lookup == "ask" and not _agreed(question):
        output.info(_("🔒 Nothing was sent: the places keep their town's name."))
        return
    agent = f"{DISTRIBUTION}/{version(DISTRIBUTION)} (+{HOME_PAGE})"
    service = Service(places.nominatim_url, active_locale().value, agent)
    try:
        named = name_spots(runtime, spots, ReverseLookup(service, pace))
    except OSError as exc:
        output.warning(
            _(
                "OpenStreetMap could not be reached ({error}): try at the next import."
            ).format(error=exc)
        )
        return
    output.success(
        ngettext(
            "{n} place named: the slideshow shows it on the TV.",
            "{n} places named: the slideshow shows them on the TV.",
            named,
        ).format(n=named)
    )


def _agreed(question: str) -> bool:
    """Ask the user; no answer (no terminal) is No.

    Args:
        question: The question.

    Returns:
        True for an explicit Yes only.
    """
    try:
        return typer.confirm(question, default=False)
    except typer.Abort:
        return False
