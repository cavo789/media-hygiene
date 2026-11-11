"""`undo --from-quarantine <run>` in the console: shown first, asked, proven (0687)."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.context import user_errors
from media_hygiene.cli.terminal import require_terminal
from media_hygiene.constants import ExitCode
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.undo_orphan import apply_orphan_plan, orphan_plan

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_SHOWN: Final = 20  # the moves listed before the question; the rest counted


def undo_from_quarantine(runtime: Runtime, run_id: str | None, *, yes: bool) -> int:
    """List the moves rebuilt from a run's quarantine, ask, then move the files back.

    Args:
        runtime: Settings, mount points and output.
        run_id: The run (required: no journal names the latest one).
        yes: `--yes`, skip the question.

    Returns:
        The exit code.

    Raises:
        JournalError: No run named (said by `user_errors`, which exits).
    """
    output = runtime.output
    with user_errors(output):
        if run_id is None:
            raise JournalError(
                _("Name the run: mh undo <run> --from-quarantine."),
                _("Its name is the folder's in the quarantine."),
            )
        plan = orphan_plan(runtime, run_id)
    output.title(_("Undo the run {run_id} from its quarantine").format(run_id=run_id))
    for move in plan.moves[:_SHOWN]:
        output.info(f"  {runtime.mapper.to_host(move.original)}")
    if len(plan.moves) > _SHOWN:
        output.info(_("  … and {count} more.").format(count=len(plan.moves) - _SHOWN))
    for file, why in plan.left:
        output.warning(
            _("Stays in the quarantine: {file} ({why})").format(
                file=runtime.mapper.to_host(file), why=why
            )
        )
    if not plan.moves:
        output.info(_("Nothing was changed."))
        return ExitCode.OK
    if not yes:
        require_terminal(sys.stdin)
        question = ngettext(
            "Move this file back to its place?",
            "Move these {count} files back to their places?",
            len(plan.moves),
        ).format(count=len(plan.moves))
        if not output.confirm(question):
            output.info(_("Nothing was changed."))
            return ExitCode.OK
    outcome = apply_orphan_plan(plan)
    output.success(
        ngettext(
            "{count} file back at its place, read back.",
            "{count} files back at their places, read back.",
            len(outcome.back),
        ).format(count=len(outcome.back))
    )
    return ExitCode.OK if len(outcome.left) == len(plan.left) else ExitCode.FAILURE
