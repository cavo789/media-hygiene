"""`crosscheck` runs Czkawka itself: say what it does, run it, say how long it took."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_duration
from media_hygiene.crosscheck.czkawka_run import run_czkawka
from media_hygiene.i18n import _
from media_hygiene.services.crosscheck import czkawka_command

if TYPE_CHECKING:
    from media_hygiene.crosscheck.czkawka_run import CzkawkaRun
    from media_hygiene.services.runtime import Runtime


def run_second_opinion(runtime: Runtime, run: CzkawkaRun) -> None:
    """Run Czkawka on the audit's folders, its own progress on the terminal.

    Args:
        runtime: Settings, mount points and output.
        run: The executable, its results file and its cache.
    """
    output = runtime.output
    output.title(_("Czkawka reads your folders"))
    output.info(
        _(
            "🔒 Czkawka, an independent duplicate finder, now reads the same folders "
            "with its own code and its own hash. It changes nothing. On tens of "
            "thousands of photos, allow a few minutes the first time."
        )
    )
    if run.cache_dir is None:
        output.tip(
            _(
                "With -v media-hygiene-cache:/cache, Czkawka remembers its work: "
                "the next crosscheck only reads what changed."
            )
        )
    started = time.monotonic()
    run_czkawka(czkawka_command(runtime).scope, run)
    output.success(
        _("Czkawka finished in {duration}.").format(
            duration=human_duration(time.monotonic() - started)
        )
    )
    output.blank()
