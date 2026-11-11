"""*Are my photos safe?* (0689) drawn: in `mh status`, and as the home page's card.

The card has its own route (`/api/safety`, 0692): the page is drawn without waiting
for it.
"""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.safety_lines import Level
from media_hygiene.cli.safety_more import safety_card
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeFinding, HomeFindings
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.run_book import book_of, read_runs
from media_hygiene.services.safety import read_safety
from media_hygiene.services.status_parts import quarantine_state

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.cli.safety_lines import SafetyLine
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.status import Status

# The console's mark per level; the page draws its colour from the level.
MARKS: Final[Mapping[Level, str]] = MappingProxyType(
    {Level.GOOD: "🟢", Level.WARN: "🟠", Level.BAD: "🔴", Level.UNKNOWN: "⚪"}
)
_ICONS: Final[Mapping[Level, str]] = MappingProxyType(
    {Level.GOOD: "check", Level.WARN: "info", Level.BAD: "info", Level.UNKNOWN: "info"}
)


def safety_of(runtime: Runtime, status: Status) -> tuple[SafetyLine, ...]:
    """Read the card's facts from disk and word them.

    Args:
        runtime: Settings and mount points.
        status: What `status` read (its quarantine is reused).

    Returns:
        The lines.
    """
    facts = read_safety(runtime, status.quarantine)
    return safety_card(facts, runtime.settings.clean.purge_hint_days)


def show_safety(runtime: Runtime, status: Status) -> None:
    """Print the card in the console, one line per fact.

    Args:
        runtime: Settings, mount points and output.
        status: What `status` read.
    """
    runtime.output.title(_("Are my photos safe?"))
    for line in safety_of(runtime, status):
        runtime.output.info(f"{MARKS[line.level]} {line.title}: {line.sub}")


def _card(lines: tuple[SafetyLine, ...]) -> HomeFindings:
    """The lines in the findings' look.

    Args:
        lines: The card's lines.

    Returns:
        The card.
    """
    return HomeFindings(
        title=_("Are my photos safe?"),
        note=_("Read from the disk now."),
        rows=tuple(
            HomeFinding(
                icon=_ICONS[line.level],
                title=line.title,
                sub=line.sub,
                action=line.step,
                ok=line.level is Level.GOOD,
                level=line.level.value,
            )
            for line in lines
        ),
    )


def page_safety(runtime: Runtime) -> HomeFindings:
    """The card on its own route (0692): the quarantine measured, then the card.

    Args:
        runtime: Settings and mount points.

    Returns:
        It.
    """
    folders = mounted_quarantines(runtime).folders
    runs = read_runs(book_of(runtime), datetime.now().astimezone()).facts
    held = {facts.run_id: facts.held for facts in runs}  # no journal read again
    quarantine = quarantine_state(folders, runtime.locations.journal_dir, held)
    return _card(
        safety_card(
            read_safety(runtime, quarantine), runtime.settings.clean.purge_hint_days
        )
    )
