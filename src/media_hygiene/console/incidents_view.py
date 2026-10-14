"""The files a run left or could not handle, grouped by reason on the screen.

Thousands of files failing for one reason (a mount refusing every move) printed one
line each: the reason was lost in them. A reason shared by more than `GROUPED_FROM`
files shows its first few, then one line with how many more; the full list stays in
the run's journal and report.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from media_hygiene.actions.outcome import Incident
    from media_hygiene.services.runtime import Runtime

# Above this many files for one reason, the reason is said once for the rest.
GROUPED_FROM: Final = 20
# Files still named, one per line, before that summary line.
SHOWN_FIRST: Final = 5


def show_failed(runtime: Runtime, incidents: Sequence[Incident]) -> None:
    """Show the files that failed, as errors, grouped by reason.

    Args:
        runtime: Settings, mount points and output.
        incidents: The failures, in their order.
    """
    _show(runtime, incidents, runtime.output.error)


def show_skipped(runtime: Runtime, incidents: Sequence[Incident]) -> None:
    """Show the files left untouched, as warnings, grouped by reason.

    Args:
        runtime: Settings, mount points and output.
        incidents: The files left, in their order.
    """
    _show(runtime, incidents, runtime.output.warning)


def _show(
    runtime: Runtime, incidents: Sequence[Incident], say: Callable[[str], None]
) -> None:
    """Name each file with its reason; a crowded reason is said once for the rest.

    Args:
        runtime: Settings, mount points and output.
        incidents: The files and their reasons.
        say: How to print one line (error or warning).
    """
    host = runtime.mapper.to_host
    for reason, group in by_reason(incidents).items():
        shown = group if len(group) <= GROUPED_FROM else group[:SHOWN_FIRST]
        for incident in shown:
            say(escape(f"{host(incident.path)}: {reason}"))
        if len(shown) < len(group):
            more = human_number(len(group) - len(shown))
            say(
                escape(
                    _("... and {count} more: {reason}").format(
                        count=more, reason=reason
                    )
                )
            )


def by_reason(incidents: Sequence[Incident]) -> dict[str, list[Incident]]:
    """Group incidents by reason, in the order each reason first appears.

    Args:
        incidents: The files and their reasons.

    Returns:
        The incidents of each reason.
    """
    groups: dict[str, list[Incident]] = {}
    for incident in incidents:
        groups.setdefault(incident.reason, []).append(incident)
    return groups
