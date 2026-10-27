"""What `mh push` says: its plan before Windows acts, the target read back after."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final

from media_hygiene.console.advice import Advice, TipKind
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext
from media_hygiene.plan.backup_gone import GoneReason

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.output import Output
    from media_hygiene.plan.backup_gone import Gone
    from media_hygiene.services.push_proof import PushProof
    from media_hygiene.services.push_run import Prepared

_NAMED: Final = 5  # files named when some are missing; the others counted


def show_plan(output: Output, prepared: Prepared) -> None:
    """Say what the run would do, and why it stops when it does.

    Args:
        output: Where to print.
        prepared: The plan.
    """
    plan = prepared.plan
    for skipped in prepared.skipped:
        output.warning(
            _(
                "{folder} could not be read whole ({count} unreadable): its part "
                "of the backup is left as it is."
            ).format(folder=skipped.host, count=human_number(skipped.unreadable))
        )
    folders = ", ".join(source.host for source in prepared.sources)
    output.info(
        _("Backup of {folders} into {target}:").format(
            folders=folders or "-", target=prepared.target.host
        )
    )
    copies = plan.copies
    lines = (
        (_("Already there"), plan.unchanged),
        (_("To copy"), len(copies)),
        (_("Moved on the PC: renamed on the backup, nothing sent"), len(plan.moves)),
        (_("Edited since: the backup's copy set aside, then copied"), len(plan.edited)),
        (_("Broken on the PC: the backup's copy kept"), len(plan.broken)),
        (_("Gone from the PC: set aside in .removed"), len(plan.removals)),
        (_("Gone from the PC: kept in the backup"), len(plan.kept)),
    )
    for label, count in lines:
        if count:
            output.info(f"    {label}: {human_number(count)}")
    if copies:
        size = human_size(sum(entry.stat.size for entry in copies))
        output.info("    " + _("To copy, in all: {size}").format(size=size))
    _reasons(output, plan.gone)
    idle = not (copies or plan.moves or plan.edited or plan.removals)
    if idle and not prepared.expired and not prepared.stopped:
        output.success(_("The backup is up to date: nothing to copy."))
    if prepared.expired:
        output.info(
            "    "
            + _("Erased from .removed (older than {days} days): {count} runs").format(
                days=prepared.keep_days, count=len(prepared.expired)
            )
        )
    if prepared.stopped:
        output.error(
            _(
                "Stopped: more than {percent} % of the backup would be set aside or "
                "replaced. A drive missing? Many files changed at once? Nothing was "
                "applied; mh push --anyway goes on."
            ).format(percent=prepared.stop_percent)
        )


def show_proof(output: Output, proof: PushProof) -> None:
    """Say what the target holds now, read back.

    Args:
        output: Where to print.
        proof: What the closing run found.
    """
    speed = proof.copied_bytes / 1024**2 / max(proof.seconds, 0.001)
    output.success(
        _(
            "Copied: {count} files ({size}, {speed} MB/s), read back from {target}."
        ).format(
            count=human_number(proof.copied),
            size=human_size(proof.copied_bytes),
            speed=f"{speed:.1f}",
            target=proof.target,
        )
    )
    if proof.renamed:
        output.info(
            _(
                "Renamed on the backup (moved, or set aside in .removed): {count}."
            ).format(count=human_number(proof.renamed))
        )
    if proof.unmade:
        output.warning(
            _("Renames not seen made: {count}. Type mh push again.").format(
                count=human_number(proof.unmade)
            )
        )
    _missing(output, proof)
    output.info(
        _("The backup holds {count} files ({size}).").format(
            count=human_number(proof.held), size=human_size(proof.held_bytes)
        )
    )
    if proof.renamed:
        output.advise(
            Advice(
                TipKind.SAFETY,
                _("Changed your mind? This puts back what was renamed or set aside:"),
                f"mh push --undo {proof.run_id}",
            )
        )
    output.next_step(_("nothing: type mh push again after your next import or sort."))


def _missing(output: Output, proof: PushProof) -> None:
    """Name the files the backup still lacks, a few, the others counted.

    Args:
        output: Where to print.
        proof: What the closing run found.
    """
    if not proof.missing:
        return
    output.warning(
        ngettext(
            "Not in the backup: {count} file (robocopy failed, or new since the "
            "plan). Type mh push again:",
            "Not in the backup: {count} files (robocopy failed, or new since the "
            "plan). Type mh push again:",
            len(proof.missing),
        ).format(count=human_number(len(proof.missing)))
    )
    for path in proof.missing[:_NAMED]:
        output.info(f"    {path}")


def _reasons(output: Output, gone: tuple[Gone, ...]) -> None:
    """Count the files gone from the PC by why.

    Args:
        output: Where to print.
        gone: The files of the backup the PC no longer has.
    """
    labels: dict[GoneReason, Callable[[], str]] = {
        GoneReason.PURGED: lambda: _("purged from the quarantine"),
        GoneReason.CONFIRMED: lambda: _("deleted, confirmed in review --gone"),
        GoneReason.QUARANTINE: lambda: _("still in the quarantine"),
        GoneReason.PENDING: lambda: _("deleted, not confirmed yet in review --gone"),
        GoneReason.UNKNOWN: lambda: _("unknown to the tool: a deletion by mistake?"),
    }
    counts = Counter(item.reason for item in gone)
    for reason, label in labels.items():
        if counts[reason]:
            output.info(f"        {label()}: {human_number(counts[reason])}")
