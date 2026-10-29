"""`mh import --phone --since`: what `mh.ps1` needs for a period (0476).

`mh` passes `--since` to `phone-plan`, which decides; after an import that copied files,
`mh` writes today's day into the journal folder (`last-import.txt`): the next import
without `--since` starts there.
"""

from __future__ import annotations

from dataclasses import dataclass

from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.import_since import LAST_IMPORT_FILE
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.next_command import TOOL_KINDS
from media_hygiene.services.phone_plan import PhoneCase


@dataclass(frozen=True, slots=True)
class PhoneSince:
    """The option, the file of the last import and the message of the files left."""

    older: str  # holds `${count}`: new files before the period, left on the phone
    flag: str = "--since"
    case: str = PhoneCase.OLDER.value
    file: str = LAST_IMPORT_FILE
    journal: int = TOOL_KINDS.index(MountKind.JOURNAL)  # its volume in `script.tools`


def phone_since() -> PhoneSince:
    """Translate the message of the files left by `--since`.

    Returns:
        The values of the script.
    """
    return PhoneSince(
        older=say(
            _(
                "Left on the phone: {count} older photos and videos (before the "
                "period; --since all takes them)."
            ),
            "count",
        )
    )
