"""Why a page could not save into `config.toml`, said to the page in the user's words.

Shared by `places` and `people`, the two pages that write `config.toml`: a refused value
is the user's to correct (422), a file that cannot be written is not (500).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from media_hygiene.review.http import Response

# Pydantic's prefix before the reason a project validator raised, already translated.
_VALUE_ERROR: Final = "Value error, "


def save_refused(error: ValueError | TypeError | OSError) -> Response:
    """Answer a save that failed with a translated message for the page.

    Args:
        error: A refused value (pydantic's or the project's) or a file that cannot be
            written.

    Returns:
        422 with "Not saved: ..." for a refused value, 500 for the file.
    """
    if isinstance(error, OSError):
        message = _("Cannot save config.toml: {error}.")
        text = message.format(error=error.strerror or error)
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": text})
    reason = str(error)
    if isinstance(error, ValidationError):
        reason = "; ".join(
            str(item["msg"]).removeprefix(_VALUE_ERROR) for item in error.errors()
        )
    message = _("Not saved: {reason}.").format(reason=reason)
    return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": message})
