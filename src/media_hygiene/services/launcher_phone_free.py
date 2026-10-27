r"""What `mh phone --free` needs: its batches, its waits and its messages (0248).

After the import, the files the PC may hold are ticked on a page (`phone-review`);
then, batch by batch, each one is copied again into an empty staging folder, proven
by its content in the container (`phone-prove`, journaled `pending`), and only then
moved off the phone with `MoveHere` into a PC folder: no dialog (measured, step 19 of
`mh-measure.ps1`), where `InvokeVerb('delete')` asks in a window behind the console.
The phone's folder is listed again; a moved copy equal to the proven content is
dropped, another one is kept; the files gone are journaled `done` (`phone-done`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.phone_free import PROVEN
from media_hygiene.services.phone_plan import PHONE_DONE, PHONE_PROVE, PHONE_REVIEW

# Files proven per run of the container: its start (≈ 2 s) shared, the staging folder
# kept small (each file waits there for its proof).
BATCH_FILES: Final = 100
# Copy speed from the phone, MB/s (measured 24.2 MB/s, step 19 of mh-measure.ps1): each
# file is read twice (the proof's copy, then the move), said before starting.
PHONE_MB_PER_SECOND: Final = 24
# How long the phone's folder is listed again until a moved file is gone (0.4 s
# measured).
GONE_SECONDS: Final = 10
# The PC folder the files moved off the phone land in, next to the import: never
# removed by a later `mh phone` (unlike the staging folders), emptied as each copy is
# proven equal.
MOVED_PREFIX: Final = ".mh-moved-"
FREE_FLAG: Final = "--free"


@dataclass(frozen=True, slots=True)
class PhoneFreeTexts:  # pylint: disable=too-many-instance-attributes  # one per message
    """The messages of `mh phone --free`, ready to sit inside double quotes."""

    read: str
    none: str
    failed: str
    nothing: str
    estimate: str  # holds `${count}`, `${size}`, `${minutes}`
    kept: str  # holds `${path}`, `${reason}`
    freed: str  # holds `${count}`, `${size}`
    kept_count: str  # holds `${count}`
    still: str  # holds `${count}`
    differs: str  # holds `${count}`, `${folder}`
    stopped: str
    aside: str  # holds `${count}`
    next: str


@dataclass(frozen=True, slots=True)
class PhoneFreeCommand:  # pylint: disable=too-many-instance-attributes  # one per value
    """What the script needs to free the phone."""

    texts: PhoneFreeTexts
    flag: str = FREE_FLAG
    review: str = PHONE_REVIEW
    prove: str = PHONE_PROVE
    done: str = PHONE_DONE
    proven: str = PROVEN
    moved: str = MOVED_PREFIX
    batch: int = BATCH_FILES
    speed: int = PHONE_MB_PER_SECOND
    gone: int = GONE_SECONDS


def phone_free_command() -> PhoneFreeCommand:
    """Gather the values and the translated messages of `mh phone --free`.

    Returns:
        Them, the messages safe inside double quotes.
    """
    return PhoneFreeCommand(
        texts=PhoneFreeTexts(
            read=say(
                _(
                    "🔒 Nothing leaves the phone before you tick it on a page and "
                    "press Delete; each file is first proven on the PC by its content."
                )
            ),
            none=say(_("Nothing on the phone that the PC holds: nothing to free.")),
            failed=say(_("The check of the phone failed: nothing more was deleted.")),
            nothing=say(_("Nothing was deleted from the phone.")),
            estimate=say(
                _(
                    "Checking then deleting {count} files ({size} GB): about {minutes} "
                    "min, each one copied again from the phone, then moved off it."
                ),
                "count",
                "size",
                "minutes",
            ),
            kept=say(_("{path} stays on the phone: {reason}"), "path", "reason"),
            freed=say(
                _(
                    "Phone freed: {count} files deleted ({size} GB), each one seen "
                    "gone from the phone and found whole on the PC."
                ),
                "count",
                "size",
            ),
            kept_count=say(
                _("Kept on the phone, the PC not holding their content: {count}."),
                "count",
            ),
            still=say(
                _(
                    "Still on the phone after the move: {count}. Type mh phone "
                    "--free again."
                ),
                "count",
            ),
            differs=say(
                _(
                    "Moved off the phone with another content than the one proven: "
                    "{count}, kept in {folder}."
                ),
                "count",
                "folder",
            ),
            stopped=say(
                _(
                    "The phone no longer answers (unplugged, or asleep: keep it "
                    "unlocked, screen on): what is counted above was deleted, the rest "
                    "is still on it. Type mh phone --free again."
                )
            ),
            aside=say(_("Set aside before, left on the phone: {count}."), "count"),
            next=say(
                _("👉 What next: mh history (the phone's run, and what it deleted).")
            ),
        )
    )
