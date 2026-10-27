r"""What `mh push` needs: its file, its orders and its messages (0264).

`mh push [--to <folder>] [--anyway] [--undo <run>]` is a host command of `mh.ps1`
(`mh_push.ps1.j2`): Windows writes to the NAS about 7 times faster than a copy
through Docker (86 to 105.8 MB/s against 15.1 MB/s, step 21 of `mh-measure.ps1`,
measured 2026-10-20), so the container only decides (`push-step`), reading the
photos and the target read-only, and Windows renames (`Move-Item`) and copies
(`robocopy`, never `/MIR` nor `/PURGE`). The target given once is kept in a file next
to the NAS passwords. The bash `mh` refuses it, saying why and the command to type in
Windows PowerShell.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.paths.unc import UNC_FOLDER
from media_hygiene.services.launcher_menu import shell_safe
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.push_lines import PUSH_STEP, Order, PushStep

# `$HOME\media-hygiene\<this>`: the target given with `--to`, its first line.
TARGET_FILE: Final = "push-target.txt"
# What the bash `mh` gives to paste in Windows PowerShell; never translated.
EXAMPLE: Final = rf"{LAUNCHER_FUNCTION} push --to \\<NAS>\backup_photos"
# Robocopy: a copy failed from this exit code on (8: some files, 16: none).
ROBOCOPY_FAILED: Final = 8
# Robocopy's options but `/MT` and the exclusions: subfolders, one retry a second
# later, times within 2 s are the same (FAT, NAS), no progress, no file or folder list.
ROBOCOPY: Final = ("/E", "/R:1", "/W:1", "/FFT", "/NP", "/NFL", "/NDL", "/NJH", "/NJS")


@dataclass(frozen=True, slots=True)
class BackupTexts:  # pylint: disable=too-many-instance-attributes  # one per message
    """The messages of `mh push`, ready to sit inside double quotes."""

    usage: str
    no_target: str
    bad_target: str  # holds `${to}`
    kept: str  # holds `${target}`
    overlap: str  # holds `${target}`, `${folder}`
    absent: str  # holds `${folder}`
    unreachable: str  # holds `${target}`
    no_plan: str
    ask: str
    declined: str
    copying: str  # holds `${from}`, `${into}`
    failed: str  # holds `${from}`, `${code}`
    undo_none: str
    windows: str  # the bash `mh`: why Windows only
    paste: str  # the bash `mh`: the 👉 line before the command


@dataclass(frozen=True, slots=True)
class PushCommand:  # pylint: disable=too-many-instance-attributes  # one per value
    """What the scripts need to run, or refuse, `mh push`."""

    texts: BackupTexts
    file: str = TARGET_FILE
    step: str = PUSH_STEP
    unc: str = UNC_FOLDER
    example: str = EXAMPLE
    failed: int = ROBOCOPY_FAILED
    robocopy: tuple[str, ...] = ROBOCOPY
    steps: type[PushStep] = PushStep
    orders: type[Order] = Order


def push_command() -> PushCommand:
    """Gather the values and the translated messages of `mh push`.

    Returns:
        Them, the messages safe inside double quotes.
    """
    return PushCommand(texts=_texts())


def _texts() -> BackupTexts:
    """Translate the messages of `mh push`.

    Returns:
        The messages.
    """
    return BackupTexts(
        usage=say(
            _(
                "mh push --to <the NAS folder> the first time, then mh push "
                "alone; --anyway goes past the safety stop; --undo <run> puts back "
                "what a run renamed or set aside."
            )
        ),
        no_target=say(
            _(
                "No backup folder yet: type mh push --to <the NAS folder>, a shared "
                "folder of its own such as backup_photos."
            )
        ),
        bad_target=say(
            _("{to} is neither a NAS folder nor a folder on a drive."), "to"
        ),
        kept=say(
            _("Backup folder kept, read back: {target}. Next time, mh push alone."),
            "target",
        ),
        overlap=say(
            _(
                "{target} overlaps {folder}: choose a folder of its own, outside your "
                "photo folders and backups."
            ),
            "target",
            "folder",
        ),
        absent=say(
            _("{folder} is not plugged in: its part of the backup is left as it is."),
            "folder",
        ),
        unreachable=say(
            _(
                "Windows cannot open {target}: is the NAS on, the shared folder "
                "created, the password right? Nothing was changed."
            ),
            "target",
        ),
        no_plan=say(_("The comparison with the backup failed: nothing was changed.")),
        ask=say(_("Apply it? (y/n)")),
        declined=say(_("Nothing was changed.")),
        copying=say(_("robocopy: {from} into {into}…"), "from", "into"),
        failed=say(
            _(
                "robocopy could not copy everything from {from} (code {code}): the "
                "files missing are named below."
            ),
            "from",
            "code",
        ),
        undo_none=say(_("Nothing to put back.")),
        windows=shell_safe(
            _(
                "mh push is for Windows only: Windows writes to the NAS about 7 "
                "times faster than a copy through Docker (measured: 86 to 105.8 MB/s "
                "against 15.1 MB/s). Nothing was started."
            )
        ),
        paste=shell_safe(_("👉 What next: open Windows PowerShell and type:")),
    )
