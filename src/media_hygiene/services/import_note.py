"""The line the burst review shows when it holds an import's series only (0630)."""

from __future__ import annotations

from typing import Final

from media_hygiene.i18n.templates import translated_environment

IMPORTED: Final = "imported"  # `/review/bursts/?imported`: the import chain's link
NOTE_MARK: Final = b"<!-- imported-note -->"  # in `review.html.j2`
_TEMPLATES: Final = "media_hygiene.review"


def imported_note(page: bytes) -> bytes:
    """Say on the page it holds the import's series only, every series a click away.

    Args:
        page: The burst review, rendered.

    Returns:
        It, the line in its left column.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    note = environment.get_template("review_imported.html.j2").render()
    return page.replace(NOTE_MARK, note.encode(), 1)
