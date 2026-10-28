"""What `mh` told the home server it relays: steps, a form's words.

Read from `MEDIA_HYGIENE_LAUNCHER_STEPS`.
"""

from __future__ import annotations

import os

from media_hygiene.i18n import _
from media_hygiene.review.home_fields import RELAY_FIELDS
from media_hygiene.review.step_watch import WATCH
from media_hygiene.services.launcher_host import windows_menu
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE


def launcher_relays_fields() -> bool:
    """Tell whether `mh` also runs the words of a step's form (0266).

    Returns:
        True when `MEDIA_HYGIENE_LAUNCHER_STEPS` says so: `mh` reads the one-shot
        file of the reports folder (`review/home_fields.py`).
    """
    return os.environ.get(LAUNCHER_STEPS_VARIABLE) in {RELAY_FIELDS, WATCH.kept}


def launcher_relays_steps() -> bool:
    """Tell whether `mh` runs the step a button chose (TODO 0210 sets the variable).

    Returns:
        True when `MEDIA_HYGIENE_LAUNCHER_STEPS` is set: ending the server with
        `STEP_EXIT_BASE + n` then runs step `n`; else the code would be lost.
    """
    return bool(os.environ.get(LAUNCHER_STEPS_VARIABLE))


def mh_window() -> str:
    """Name the window where `mh` runs the step chosen, often behind the browser (0258).

    Returns:
        PowerShell's window from `mh.ps1` (or without `mh`), else the terminal.
    """
    if windows_menu():
        return _("the PowerShell window of mh (in the taskbar)")
    return _("the terminal where mh runs")
