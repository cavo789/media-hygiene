"""The end of `mh import --phone`: what it skipped, then the audit it runs (0451).

The files copied join the library, and `search`, only through an audit: the import
runs it rather than telling the user to. When the home page is open on the port of the
pages, it is asked (`POST /api/audit`): the page shows the run, then reloads on its
summary; else `mh audit` runs in the console.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from media_hygiene.i18n import _
from media_hygiene.review.home_app import AUDIT_PATH, AuditAction
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.launcher_phone_since import PhoneSince, phone_since
from media_hygiene.services.launcher_phone_then import PhoneThen, phone_then


@dataclass(frozen=True, slots=True)
class PhoneEnd:
    """The messages and the request of the end of `mh import --phone`."""

    aside: str  # holds `${count}`: on the phone, set aside before by the user
    on_page: str  # the home page runs the audit
    in_console: str  # `mh audit` runs here
    since: PhoneSince  # `--since`, the last import's day (0476)
    then: PhoneThen  # the chain after the copies (0475)
    path: str = AUDIT_PATH
    body: str = json.dumps({"action": AuditAction.START.value})


def phone_end() -> PhoneEnd:
    """Translate the messages of the end of `mh import --phone`.

    Returns:
        The messages, and the request the home page answers.
    """
    return PhoneEnd(
        aside=say(
            _(
                "Also on the phone, skipped: {count} you set aside earlier (a clean "
                "or a review); they do not come back into your library."
            ),
            "count",
        ),
        on_page=say(
            _(
                "👉 The home page audits the new files now: follow it there, it shows "
                "them when done."
            )
        ),
        in_console=say(
            _("Audit of the new files, so that they join your library (mh audit):")
        ),
        since=phone_since(),
        then=phone_then(),
    )
