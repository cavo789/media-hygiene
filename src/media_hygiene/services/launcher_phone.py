r"""What `mh import --phone` needs: its waits, its folders and its messages (0219).

`mh import --phone [--to <folder>]` is a host command of `mh.ps1` (`mh_phone.ps1.j2`): a
phone over USB (MTP) has no drive letter, Docker cannot see it, Windows PowerShell
can, through `Shell.Application` (a COM object of Windows: no `Add-Type`). It lists
the phone's `DCIM`, pipes the list to `phone-plan` in the container, then copies the
new files with `CopyHere` only: never `MoveHere`, nothing on the phone is deleted,
moved or renamed. Each file goes into an empty staging folder of the run first: over
MTP Windows ignores "yes to all" (flag 16) and opens its "replace" dialog behind the
console (step 19 of `mh-measure.ps1`, measured 2026-10-19), so the copy never meets a
name already there; `Move-Item` then puts it in place, `_1` added to a name taken.
The messages are written into the script, translated, with the shell variables they
show (`${count}`, `${size}`...).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.launcher_phone_end import PhoneEnd, phone_end
from media_hygiene.services.launcher_phone_free import (
    PhoneFreeCommand,
    phone_free_command,
)
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.phone_known import STAGING_PREFIX
from media_hygiene.services.phone_plan import PHONE_PLAN, PhoneCase

# A copy that stops growing this long is given up: the cable pulled (TODO 0219).
STALL_SECONDS: Final = 60
# How often the staging folder is looked at while a file arrives: every
# FAST_POLL_MILLISECONDS for its first FAST_FOR_MILLISECONDS (a photo arrives in a
# fraction of a second: 0.23 s a file lost to 200 ms polls, measured 0251), then
# every POLL_MILLISECONDS (a large video needs no fast polling).
FAST_POLL_MILLISECONDS: Final = 25
FAST_FOR_MILLISECONDS: Final = 1000
POLL_MILLISECONDS: Final = 200
# Listing over MTP takes about 31 ms a file (measured, 775 files in 24 s): a line
# every this many files says the listing is alive.
LISTED_EVERY: Final = 500
# `<first photo folder>\Phone\<phone name>` without `--to`.
DEFAULT_FOLDER: Final = "Phone"
# `CopyHere` options: no progress window (4), yes to all (16), no error window (1024).
COPY_FLAGS: Final = 4 + 16 + 1024
# A phone seen with no storage (asleep, locked): asked again this often, this
# long (0336).
WAKE_EVERY_SECONDS: Final = 2
WAKE_FOR_SECONDS: Final = 60


@dataclass(frozen=True, slots=True)
class PhoneTexts:  # pylint: disable=too-many-instance-attributes  # one per message
    """The messages of `mh import --phone`, ready to sit inside double quotes."""

    usage: str
    bad_folder: str  # holds `${to}`
    no_folder: str  # no `--to` and no photo folder
    read_only: str
    none: str
    pick: str  # holds `${count}`
    no_dcim: str  # holds `${name}`
    asleep: str  # holds `${name}`
    listing: str  # holds `${name}`
    listed: str  # holds `${count}`
    no_plan: str
    copying: str  # holds `${count}`, `${size}`, `${destination}`
    renamed: str  # holds `${name}`, `${final}`
    unplugged: str  # holds `${count}`
    copied: str  # holds `${count}`, `${size}`, `${speed}`, `${destination}`
    missing: str  # holds `${count}`
    library: str  # holds `${count}`
    here: str  # holds `${count}`
    nothing: str


@dataclass(frozen=True, slots=True)
class PhoneCommand:  # pylint: disable=too-many-instance-attributes  # one per value
    """What the script needs to run `mh import --phone`."""

    texts: PhoneTexts
    end: PhoneEnd  # the set-aside said, the files copied audited (0451)
    free: PhoneFreeCommand  # `--free` (0248)
    plan: str = PHONE_PLAN
    new: str = PhoneCase.NEW.value
    library: str = PhoneCase.LIBRARY.value
    aside: str = PhoneCase.SET_ASIDE.value
    here: str = PhoneCase.DESTINATION.value
    staging: str = STAGING_PREFIX
    folder: str = DEFAULT_FOLDER
    flags: int = COPY_FLAGS
    stall: int = STALL_SECONDS
    fast: int = FAST_POLL_MILLISECONDS
    fast_for: int = FAST_FOR_MILLISECONDS
    poll: int = POLL_MILLISECONDS
    every: int = LISTED_EVERY
    wake_every: int = WAKE_EVERY_SECONDS
    wake_for: int = WAKE_FOR_SECONDS


def phone_command() -> PhoneCommand:
    """Gather the values and the translated messages of `mh import --phone`.

    Returns:
        Them, the messages safe inside double quotes.
    """
    return PhoneCommand(texts=_texts(), end=phone_end(), free=phone_free_command())


def _texts() -> PhoneTexts:
    """Translate the messages of `mh import --phone`.

    Returns:
        The messages.
    """
    return PhoneTexts(
        usage=say(
            _(
                "mh import --phone copies only the new photos and videos of a phone "
                "plugged "
                "in over USB; --to <folder> chooses where, --only <folder of DCIM> "
                "takes that folder only (Camera), --free then offers to delete from "
                "the phone what the PC holds."
            )
        ),
        bad_folder=say(_("{to} is not a folder on a drive letter."), "to"),
        no_folder=say(_("No photo folder: type mh import --phone --to <folder>.")),
        read_only=say(
            _("🔒 The phone is only read: nothing on it is deleted, moved or renamed.")
        ),
        none=say(
            _(
                "No phone seen: plug it in, unlock it, choose File transfer (iPhone: "
                "Trust this computer), then type mh import --phone again."
            )
        ),
        pick=say(_("Number of the phone (1 to {count})"), "count"),
        no_dcim=say(_("No DCIM folder on {name}: no photo to copy."), "name"),
        asleep=say(
            _(
                "{name} answers but shows no storage: wake it up and unlock it, then "
                "choose File transfer in the USB notification (iPhone: Trust this "
                "computer). Waiting for it…"
            ),
            "name",
        ),
        listing=say(
            _(
                "Listing the photos and videos of {name}: about 30 seconds per "
                "1,000 files…"
            ),
            "name",
        ),
        listed=say(_("{count} files listed…"), "count"),
        no_plan=say(_("The comparison with your library failed: nothing was copied.")),
        copying=say(
            _(
                "New photos and videos to copy: {count} ({size} GB) into "
                "{destination}; keep the phone unlocked, screen on…"
            ),
            "count",
            "size",
            "destination",
        ),
        renamed=say(_("{name} was already there: copied as {final}."), "name", "final"),
        unplugged=say(
            _(
                "The phone no longer answers (unplugged, or asleep: keep it unlocked, "
                "screen on, during the copy): {count} files copied so "
                "far. Type mh import --phone again: what is already copied is skipped."
            ),
            "count",
        ),
        copied=say(
            _(
                "New photos and videos copied: {count} ({size} GB, {speed} MB/s), "
                "read back from {destination}."
            ),
            "count",
            "size",
            "speed",
            "destination",
        ),
        missing=say(
            _(
                "Copies not found when read back: {count}. Type mh import --phone "
                "again."
            ),
            "count",
        ),
        library=say(_("Already in your library, not copied: {count}."), "count"),
        here=say(
            _("Already copied by an earlier mh import --phone: {count}."), "count"
        ),
        nothing=say(_("Nothing new on the phone: nothing to copy.")),
    )
