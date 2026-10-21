"""The steps of `mh backup` in the container: plan, start, prove, undo, undone (0264).

Lines are data: read on stdin, written on stdout, in UTF-8 both ways; every message
goes to stderr (`backup-step` is a data command).
"""

# pylint: disable=import-outside-toplevel  # lazy: a step loads its code when it runs

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.backup_lines import BackupStep

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.services.runtime import Runtime

_ENCODING: Final = "utf-8"


@dataclass(frozen=True, slots=True)
class StepCall:
    """The options of a step."""

    target: str
    run: str = ""
    anyway: bool = False
    seconds: float = 0.0


def run_step(runtime: Runtime, step: BackupStep, call: StepCall) -> None:
    """Run one step.

    Args:
        runtime: Settings, mount points and output.
        step: The step.
        call: Its options.

    Raises:
        MountError: A step that journals without a journal mount.
    """
    if step is not BackupStep.PLAN and not runtime.persistent(MountKind.JOURNAL):
        raise MountError(_("No journal mount: nothing was changed."))
    steps = {
        BackupStep.PLAN: _plan,
        BackupStep.START: _start,
        BackupStep.PROVE: _prove,
        BackupStep.UNDO: _undo,
        BackupStep.UNDONE: _undone,
    }
    steps[step](runtime, call)


def _plan(runtime: Runtime, call: StepCall) -> None:
    """Compare, say the plan, print its lines.

    Args:
        runtime: Settings, mount points and output.
        call: The target, `--anyway`.
    """
    from media_hygiene.console.backup_target_view import show_plan
    from media_hygiene.services.backup_lines import plan_lines
    from media_hygiene.services.backup_run import prepare_backup

    prepared = prepare_backup(runtime, call.target, anyway=call.anyway)
    show_plan(runtime.output, prepared)
    _write(plan_lines(prepared))


def _start(runtime: Runtime, call: StepCall) -> None:
    """Journal each rename of the plan piped back, before Windows makes it.

    Args:
        runtime: Settings, mount points and output.
        call: The target.
    """
    from media_hygiene.services.backup_journal import backup_run, record_pending
    from media_hygiene.services.backup_proof import ProofQuery, plan_of
    from media_hygiene.services.backup_sources import backup_target

    plan = plan_of(runtime, ProofQuery(call.target, _read()))
    target = backup_target(runtime, call.target)
    record_pending(
        backup_run(runtime.locations.journal_dir, plan.run_id, target), plan.changes
    )


def _prove(runtime: Runtime, call: StepCall) -> None:
    """List the target again, journal what was made, say it.

    Args:
        runtime: Settings, mount points and output.
        call: The target, robocopy's time.
    """
    from media_hygiene.console.backup_target_view import show_proof
    from media_hygiene.services.backup_proof import ProofQuery, prove_backup

    query = ProofQuery(call.target, _read(), call.seconds)
    show_proof(runtime.output, prove_backup(runtime, query))


def _undo(runtime: Runtime, call: StepCall) -> None:
    """Print the renames of a run back, each journaled first.

    Args:
        runtime: Settings, mount points and output.
        call: The target, the run.
    """
    from media_hygiene.services.backup_sources import backup_target
    from media_hygiene.services.backup_undo import plan_undo

    target = backup_target(runtime, call.target)
    undo = plan_undo(runtime.locations.journal_dir, call.run, target)
    output = runtime.output
    if undo.skipped:
        output.warning(
            ngettext(
                "{count} file is no longer where the run left it, or its old "
                "place is taken: left as it is.",
                "{count} files are no longer where the run left them, or their "
                "old place is taken: left as they are.",
                len(undo.skipped),
            ).format(count=len(undo.skipped))
        )
    if undo.copies:
        output.info(_("The files robocopy copied stay in the backup."))
    _write(undo.lines)


def _undone(runtime: Runtime, call: StepCall) -> None:
    """Journal the renames back that the target shows made.

    Args:
        runtime: Settings, mount points and output.
        call: The target, the run.
    """
    from media_hygiene.services.backup_sources import backup_target
    from media_hygiene.services.backup_undo import record_undone

    target = backup_target(runtime, call.target)
    back = record_undone(runtime.locations.journal_dir, call.run, target)
    runtime.output.success(
        ngettext(
            "Put back in the backup: {count} file, read back.",
            "Put back in the backup: {count} files, read back.",
            back,
        ).format(count=back)
    )


def _read() -> list[str]:
    """The lines on stdin.

    Returns:
        Them, without their ends.
    """
    return sys.stdin.buffer.read().decode(_ENCODING, errors="replace").splitlines()


def _write(lines: Iterable[str]) -> None:
    """Print lines on stdout.

    Args:
        lines: Them, without their ends.
    """
    sys.stdout.buffer.write("".join(f"{line}\n" for line in lines).encode(_ENCODING))
    sys.stdout.flush()
