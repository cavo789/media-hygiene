"""`people --straighten`: the fast path of the *Photos to straighten* page (0810).

Every turn the page would show, written at once after one question, journaled: for a
large collection. The page (`/straighten/` of the home page) shows each photo turned
first: it is offered first.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.context import user_errors
from media_hygiene.console.formatting import human_number
from media_hygiene.console.progress import RichProgress
from media_hygiene.i18n import _
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.turn_apply import TurnService

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def straighten_flow(runtime: Runtime) -> int:
    """Count the photos to turn, ask, turn them, then say how to undo.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        How many photos were turned.
    """
    output = runtime.output
    with user_errors(output):
        jobs = TurnService(runtime, NullProgress()).prepare()
        if not jobs:
            output.info(
                _("No photo to straighten: nothing proposed, or every turn refused.")
            )
            return 0
        output.info(
            _(
                "To see them turned first: the page Photos to straighten of the "
                "home page (mh home)."
            )
        )
        question = _(
            "Turn these {count} photos? Only their orientation tag is written, "
            "journaled."
        ).format(count=human_number(len(jobs)))
        if not output.confirm(question):
            return 0
        with RichProgress(output.console) as progress:
            result = TurnService(runtime, progress).execute(jobs, lambda: False)
        for incident in (*result.outcome.skipped, *result.outcome.failed):
            output.warning(
                f"{runtime.mapper.to_host(incident.path)}: {incident.reason}"
            )
        output.success(
            _("Turned, read back: {count} photos.").format(
                count=human_number(result.outcome.done)
            )
        )
        output.info(
            _("Undo: mh undo {run} (each photo back byte for byte).").format(
                run=result.run_id
            )
        )
        return result.outcome.done
