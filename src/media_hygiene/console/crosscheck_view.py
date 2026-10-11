"""Print the verdict of a cross-check with Czkawka, and what it set aside."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_number
from media_hygiene.crosscheck.compare import OutsideReason
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.crosscheck.compare import CrossCheckResult
    from media_hygiene.crosscheck.czkawka import Group
    from media_hygiene.paths.host_paths import HostPathMapper

_SHOWN_DIFFERENCES: Final = 10
_DATE_FORMAT: Final = "%Y-%m-%d %H:%M %Z"


def show_cross_check(
    output: Output,
    result: CrossCheckResult,
    mapper: HostPathMapper,
) -> None:
    """Say whether Czkawka agrees, list the disagreements, explain the rest.

    Args:
        output: Where to print.
        result: The comparison.
        mapper: Host/container path translator.
    """
    if result.results_date is not None:
        output.info(
            _("Czkawka results of {date}.").format(
                date=result.results_date.astimezone().strftime(_DATE_FORMAT)
            )
        )
    if result.agrees and not result.ours:
        output.success(_("Czkawka agrees: no exact duplicate."))
    elif result.agrees:
        groups = len(result.ours)
        copies = ngettext(
            "{count} extra copy", "{count} extra copies", result.copies
        ).format(count=human_number(result.copies))
        output.success(
            ngettext(
                "Czkawka agrees: the same {copies} in {count} group.",
                "Czkawka agrees: the same {copies} in {count} groups.",
                groups,
            ).format(copies=copies, count=human_number(groups))
        )
    else:
        count = len(result.only_ours) + len(result.only_theirs)
        output.warning(
            ngettext(
                "Czkawka disagrees on {count} group: look at it before cleaning.",
                "Czkawka disagrees on {count} groups: look at them before cleaning.",
                count,
            ).format(count=human_number(count))
        )
        for line in (
            *_differences(_("only media-hygiene"), result.only_ours, mapper),
            *_differences(_("only Czkawka"), result.only_theirs, mapper),
        ):
            output.info(line)
    if result.outside:
        details = ", ".join(
            f"{_outside_label(reason)}: {human_number(count)}"
            for reason, count in sorted(result.outside.items())
        )
        output.info(
            _(
                "Not compared, as media-hygiene does not look at them "
                "(nothing to do): {details}."
            ).format(details=details)
        )
    for folder, count in list(result.skipped_folders.items())[:_SHOWN_DIFFERENCES]:
        output.info(f"  • {mapper.to_host(folder)}: {human_number(count)}")


def _differences(
    label: str,
    groups: tuple[Group, ...],
    mapper: HostPathMapper,
) -> list[str]:
    """Describe the first groups only one tool found.

    Args:
        label: Which tool found them.
        groups: The groups.
        mapper: Host/container path translator.

    Returns:
        One line per group shown, then how many are hidden.
    """
    lines = [
        f"  • {label}: " + " = ".join(mapper.to_host(path) for path in sorted(group))
        for group in groups[:_SHOWN_DIFFERENCES]
    ]
    hidden = len(groups) - _SHOWN_DIFFERENCES
    if hidden > 0:
        lines.append(
            "  • " + _("… and {count} more.").format(count=human_number(hidden))
        )
    return lines


def _outside_label(reason: OutsideReason) -> str:
    """Translate why a file is out of media-hygiene's scope.

    Args:
        reason: The reason.

    Returns:
        A short label.
    """
    labels = {
        OutsideReason.NOT_MOUNTED: _("outside the mounted folders"),
        OutsideReason.EXTENSION: _("other file types"),
        OutsideReason.EXCLUDED: _(
            "in folders never analysed (system, trash, thumbnails, excluded)"
        ),
        OutsideReason.BROKEN: _("broken files"),
    }
    return labels[reason]
