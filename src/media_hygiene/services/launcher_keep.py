r"""Where `mh backup` sends a copy and `mh restore` fetches one (0414, 0419).

The container always writes and reads the archives in the PC folder
(`$HOME\media-hygiene\backups`, mounted on `/backups`). `mh.ps1` then copies them,
itself, to another folder: the one of `--to` (`backup`) or `--from` (`restore`), else
`<push target>\.mh-backups` when `mh push` has a target (the NAS: the archives survive a
lost disk). Windows copies, as for `mh push`: the container never needs the NAS's
password. A folder that cannot be opened is said, the PC copy kept (never a silent
failure); one typed with `--to`/`--from` stops the command instead. A backup only
reads, with SQLite's own copy, so it runs beside a page (0569). A restore overwrites the
index: it is refused while another `mh` container runs (a page, an audit), the home page
waiting in the background excepted (it runs the step), and lists the archives of both
folders first, newest first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.cache_backup import PREFIX, SUFFIX
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.launcher_push import TARGET_FILE

# `<push target>\<this>`: the archives' copy next to the photos' backup (0414).
TARGET_FOLDER: Final = ".mh-backups"
# A copy written under this suffix, renamed once whole: never a half archive taken.
PARTIAL: Final = ".part"


@dataclass(frozen=True, slots=True)
class KeepTexts:
    """The lines of the copies, ready to sit inside double quotes."""

    usage: str
    busy: str
    unreachable: str  # holds `${other}`
    fallback: str
    fetched: str  # holds `${count}`, `${other}`
    sent: str  # holds `${count}`, `${other}`
    failed: str  # holds `${other}`


@dataclass(frozen=True, slots=True)
class ListTexts:
    """The lines of the archives listed before a restore (0569)."""

    listed: str
    this_pc: str


@dataclass(frozen=True, slots=True)
class KeepPlace:
    """The names the scripts need to find, copy and rotate the archives."""

    texts: KeepTexts
    listing: ListTexts
    file: str = TARGET_FILE
    folder: str = TARGET_FOLDER
    prefix: str = PREFIX
    suffix: str = SUFFIX
    partial: str = PARTIAL


def keep_place() -> KeepPlace:
    """Gather the names and the translated lines of the archives' copies.

    Returns:
        Them, the lines safe inside double quotes.
    """
    return KeepPlace(
        KeepTexts(
            usage=say(
                _(
                    "mh backup [--to <folder>] or mh restore [--from <folder>]: by "
                    "default the folder .mh-backups of the mh push target."
                )
            ),
            busy=say(
                _(
                    "Another mh command is running (a page, an audit): close it "
                    "first, the index may be written meanwhile. Nothing was changed."
                )
            ),
            unreachable=say(_("Windows cannot open {other}."), "other"),
            fallback=say(
                _("The archives stay on this PC only, in the folder backups of mh.")
            ),
            fetched=say(
                _("{count} archive(s) copied from {other} to this PC."),
                "count",
                "other",
            ),
            sent=say(_("Read back: {count} archive(s) in {other}."), "count", "other"),
            failed=say(
                _(
                    "The copy to {other} failed: the archive stays on this PC only, "
                    "in the folder backups of mh."
                ),
                "other",
            ),
        ),
        ListTexts(listed=say(_("Archives, newest first:")), this_pc=say(_("this PC"))),
    )
