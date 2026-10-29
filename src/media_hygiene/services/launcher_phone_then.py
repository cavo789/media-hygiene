"""After `mh import --phone`: the chain of `[imports] then`, run by `mh.ps1` (0475).

`phone-plan` ends its plan with one `then<TAB><step>` line per step switched on; once
files are copied, `mh` says the list, runs `audit` (on the home page when it is open
and alone, else here), `copies` (`phone-end --copies`, before the tags, 0480),
`bursts` (the review page of the import's series, in the background), `tags` (🤖,
the new folder only: a model not running is said by `tags` and the chain goes on),
then `phone-end`: the place names (🌐 their own question) and the slideshow of the
new photos, offered in one answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.config.import_settings import ImportStep
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.import_bursts import IMPORT_DECISIONS
from media_hygiene.services.import_end import PHONE_END
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.next_command import TOOL_KINDS

# The first word of a chain line of the plan.
THEN: Final = "then"


@dataclass(frozen=True, slots=True)
class PhoneThen:  # pylint: disable=too-many-instance-attributes  # one per value
    """The steps' names, the command ending the chain and the messages."""

    listed: str  # holds `${list}`
    off: str  # no step on
    tags: str  # 🤖: before `tags`
    tv: str  # the question: the slideshow on the TV now?
    bursts: str  # the page of the import's series opens beside the next steps (0480)
    bursts_done: str  # the question once the other steps ran: done on that page?
    case: str = THEN
    audit: str = ImportStep.AUDIT.value
    tags_step: str = ImportStep.TAGS.value
    copies_step: str = ImportStep.COPIES.value
    bursts_step: str = ImportStep.BURSTS.value
    end: str = PHONE_END
    decisions: str = IMPORT_DECISIONS  # in the reports folder
    reports: int = TOOL_KINDS.index(MountKind.REPORTS)  # its volume in `script.tools`


def phone_then() -> PhoneThen:
    """Translate the messages of the chain.

    Returns:
        Them, safe inside double quotes.
    """
    return PhoneThen(
        listed=say(
            _("After the import: {list} (change it: [imports] then in config.toml)."),
            "list",
        ),
        off=say(
            _(
                "Nothing runs after the import ([imports] then is empty): mh audit "
                "adds the new files to your library."
            )
        ),
        tags=say(
            _(
                "🤖 Describing the new photos with the local AI model (mh tags); "
                "skipped if it is not running:"
            )
        ),
        tv=say(_("Show it on the TV now? (y/N)")),
        bursts=say(
            _(
                "📸 The burst series of the new photos open in your browser: keep "
                "the best shots there while the next steps run."
            )
        ),
        bursts_done=say(
            _(
                "Done on the burst page? Press Enter: the shots you set aside go to "
                "the quarantine (mh undo puts them back)."
            )
        ),
    )
