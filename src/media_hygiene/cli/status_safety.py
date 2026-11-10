"""*Are my photos safe?* (0689) drawn: in `mh status`, and as the home page's card."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.safety_lines import Level
from media_hygiene.cli.safety_more import safety_card
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeFinding, HomeFindings
from media_hygiene.services.safety import read_safety

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


def home_safety(runtime: Runtime, status: Status) -> HomeFindings:
    """The card of the home page, in the findings' look.

    Args:
        runtime: Settings and mount points.
        status: What `status` read.

    Returns:
        It.
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
            for line in safety_of(runtime, status)
        ),
    )
