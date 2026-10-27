r"""`phone-decisions.json`: the files of a phone ticked to leave it, read back (0248).

Every file the page shows is listed, ticked or not, with the plan's case and reason:
`mh` deletes nothing the file does not hold ticked. The page never trusts its own
memory: after each choice the file is read again from the disk, and the page shows
what it found there. It lies in `/reports`, next to the other decisions files.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.services.phone_plan import PhoneCase

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.services.phone_proof import Ticked

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_NANOSECONDS: Final = 1_000_000_000
PHONE_DECISIONS: Final = "phone-decisions.json"

# A file of the phone as the decisions file names it: its path below DCIM, its size.
type ChoiceKey = tuple[str, int]


class PhoneChoice(BaseModel):
    """One file of the phone, as the page showed it, and whether it is ticked."""

    model_config = _FROZEN

    case: PhoneCase
    path: str  # below DCIM, `/` between folders
    size: int
    modified: str
    reason: tuple[str, ...] = ()
    ticked: bool


class PhoneDecisions(BaseModel):
    """The decisions file of one `mh import --phone`: the phone, and each file shown."""

    model_config = _FROZEN

    version: Literal[1] = 1
    phone: str
    files: tuple[PhoneChoice, ...] = ()


class PhoneProof(BaseModel):
    """The decisions file as just read from the disk: when written, how big, what."""

    model_config = _FROZEN

    size: int
    modified: str  # ISO 8601, UTC: the page shows it in local time
    ticked: tuple[int, ...]  # the files of the page ticked in the file, by rank


def phone_decisions(phone: str, files: Iterable[tuple[Ticked, bool]]) -> PhoneDecisions:
    """List every file of the page, as the plan named it, ticked or not.

    Args:
        phone: The phone's name.
        files: Each file and its tick, in the page's order.

    Returns:
        The decisions file.
    """
    return PhoneDecisions(
        phone=phone,
        files=tuple(
            PhoneChoice(
                case=ticked.case,
                path=ticked.file.path.as_posix(),
                size=ticked.file.size,
                modified=ticked.file.modified,
                reason=ticked.reason,
                ticked=on,
            )
            for ticked, on in files
        ),
    )


def write_phone_decisions(path: Path, decisions: PhoneDecisions) -> None:
    """Save the decisions file at once: a crash never leaves half a file behind.

    Args:
        path: The file, in the container.
        decisions: What to save.
    """
    draft = path.with_name(f".{path.name}.partial")
    draft.write_text(decisions.model_dump_json(indent=2) + "\n", encoding="utf-8")
    draft.replace(path)


def read_phone_decisions(path: Path) -> tuple[PhoneDecisions, PhoneProof]:
    """Read the decisions file from the disk, with its size and when it was written.

    Args:
        path: The file, in the container.

    Returns:
        What it holds, and its stamp (`ticked` left empty).

    Raises:
        DecisionsError: It cannot be read, or is not a phone decisions file.
    """
    try:
        decisions = PhoneDecisions.model_validate_json(path.read_bytes())
        written = path.stat()
    except (OSError, ValidationError) as exc:
        message = _("Cannot read the decisions file {path}.").format(path=path)
        raise DecisionsError(message) from exc
    modified = datetime.fromtimestamp(written.st_mtime_ns / _NANOSECONDS, tz=UTC)
    stamp = PhoneProof(size=written.st_size, modified=modified.isoformat(), ticked=())
    return decisions, stamp


def read_ticked_back(path: Path, ranks: Mapping[ChoiceKey, int]) -> PhoneProof:
    """Read the decisions file back: which files of the page it holds ticked.

    Args:
        path: The file, in the container.
        ranks: Every file of the page, by its key.

    Returns:
        What it holds; a file the page does not show is never counted.

    Raises:
        DecisionsError: It cannot be read, or is not a phone decisions file.
    """
    decisions, stamp = read_phone_decisions(path)
    ticked = sorted(
        ranks[key]
        for choice in decisions.files
        if choice.ticked and (key := (choice.path, choice.size)) in ranks
    )
    return stamp.model_copy(update={"ticked": tuple(ticked)})
