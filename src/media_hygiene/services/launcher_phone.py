r"""What `mh phone` needs: its waits, its folders and its messages (0219).

`mh phone [--to <folder>]` is a host command of `mh.ps1` (`mh_phone.ps1.j2`): a
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
from media_hygiene.services.launcher_menu import shell_safe
from media_hygiene.services.phone_known import STAGING_PREFIX
from media_hygiene.services.phone_plan import PHONE_PLAN, PhoneCase

# A copy that stops growing this long is given up: the cable pulled (TODO 0219).
STALL_SECONDS: Final = 60
# How often the staging folder is looked at while a file arrives.
POLL_MILLISECONDS: Final = 200
# Listing over MTP takes about 31 ms a file (measured, 775 files in 24 s): a line
# every this many files says the listing is alive.
LISTED_EVERY: Final = 500
# `<first photo folder>\Phone\<phone name>` without `--to`.
DEFAULT_FOLDER: Final = "Phone"
# `CopyHere` options: no progress window (4), yes to all (16), no error window (1024).
COPY_FLAGS: Final = 4 + 16 + 1024


@dataclass(frozen=True, slots=True)
class PhoneTexts:  # pylint: disable=too-many-instance-attributes  # one per message
    """The messages of `mh phone`, ready to sit inside double quotes."""

    usage: str
    bad_folder: str  # holds `${to}`
    no_folder: str  # no `--to` and no photo folder
    read_only: str
    none: str
    pick: str  # holds `${count}`
    no_dcim: str  # holds `${name}`
    listing: str  # holds `${name}`
    listed: str  # holds `${count}`
    no_plan: str
    copying: str  # holds `${count}`, `${size}`, `${destination}`
    renamed: str  # holds `${name}`, `${final}`
    unplugged: str  # holds `${count}`
    copied: str  # holds `${count}`, `${size}`, `${speed}`, `${destination}`
    missing: str  # holds `${count}`
    library: str  # holds `${count}`
    aside: str  # holds `${count}`
    here: str  # holds `${count}`
    nothing: str
    next: str


@dataclass(frozen=True, slots=True)
class PhoneCommand:  # pylint: disable=too-many-instance-attributes  # one per value
    """What the script needs to run `mh phone`."""

    texts: PhoneTexts
    plan: str = PHONE_PLAN
    new: str = PhoneCase.NEW.value
    library: str = PhoneCase.LIBRARY.value
    aside: str = PhoneCase.SET_ASIDE.value
    here: str = PhoneCase.DESTINATION.value
    staging: str = STAGING_PREFIX
    folder: str = DEFAULT_FOLDER
    flags: int = COPY_FLAGS
    stall: int = STALL_SECONDS
    poll: int = POLL_MILLISECONDS
    every: int = LISTED_EVERY


def phone_command() -> PhoneCommand:
    """Gather the values and the translated messages of `mh phone`.

    Returns:
        Them, the messages safe inside double quotes.
    """
    return PhoneCommand(texts=_texts())


def _say(text: str, *fields: str) -> str:
    """Make a message safe, then put a shell variable in each field.

    Args:
        text: The translated message.
        *fields: The names of its fields, each shown by the variable of that name.

    Returns:
        The message for the script.
    """
    said = shell_safe(text)
    for name in fields:
        said = said.replace(f"{{{name}}}", f"${{{name}}}")
    return said


def _texts() -> PhoneTexts:
    """Translate the messages of `mh phone`.

    Returns:
        The messages.
    """
    return PhoneTexts(
        usage=_say(
            _(
                "mh phone copies only the new photos and videos of a phone plugged "
                "in over USB; mh phone --to <folder> chooses where."
            )
        ),
        bad_folder=_say(_("{to} is not a folder on a drive letter."), "to"),
        no_folder=_say(_("No photo folder: type mh phone --to <folder>.")),
        read_only=_say(
            _("🔒 The phone is only read: nothing on it is deleted, moved or renamed.")
        ),
        none=_say(
            _(
                "No phone seen: plug it in, unlock it, choose File transfer (iPhone: "
                "Trust this computer), then type mh phone again."
            )
        ),
        pick=_say(_("Number of the phone (1 to {count})"), "count"),
        no_dcim=_say(_("No DCIM folder on {name}: no photo to copy."), "name"),
        listing=_say(
            _(
                "Listing the photos and videos of {name}: about 30 seconds per "
                "1,000 files…"
            ),
            "name",
        ),
        listed=_say(_("{count} files listed…"), "count"),
        no_plan=_say(_("The comparison with your library failed: nothing was copied.")),
        copying=_say(
            _("New photos and videos to copy: {count} ({size} GB) into {destination}…"),
            "count",
            "size",
            "destination",
        ),
        renamed=_say(
            _("{name} was already there: copied as {final}."), "name", "final"
        ),
        unplugged=_say(
            _(
                "The phone no longer answers (unplugged?): {count} files copied so "
                "far. Type mh phone again: what is already copied is skipped."
            ),
            "count",
        ),
        copied=_say(
            _(
                "New photos and videos copied: {count} ({size} GB, {speed} MB/s), "
                "read back from {destination}."
            ),
            "count",
            "size",
            "speed",
            "destination",
        ),
        missing=_say(
            _("Copies not found when read back: {count}. Type mh phone again."),
            "count",
        ),
        library=_say(_("Already in your library, not copied: {count}."), "count"),
        aside=_say(_("Set aside before on purpose, not copied: {count}."), "count"),
        here=_say(_("Already copied by an earlier mh phone: {count}."), "count"),
        nothing=_say(_("Nothing new on the phone: nothing to copy.")),
        next=_say(_("👉 What next: mh audit (the new files join your library).")),
    )
