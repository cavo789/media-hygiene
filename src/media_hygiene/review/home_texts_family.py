"""The texts of the home page a paired phone sees (0293): the family's door."""

from __future__ import annotations

from media_hygiene.i18n import _


def family_texts() -> dict[str, str]:
    """The texts of the family view.

    Returns:
        By key, in the language in use.
    """
    return {
        "familyTitle": _("Our photos"),
        "familyNote": _(
            "Search, browse and the albums of this home: nothing here changes a photo."
        ),
        "familyFind": _("Find a photo"),
        "tvTitle": _("Show on the TV"),
        "tvNote": _(
            "The PC starts the show; the TV opens it at its bookmark, this phone "
            "becomes the remote."
        ),
        "tvNone": _("No album saved yet: choose a folder or a month below."),
        "tvFolder": _("A folder"),
        "tvMonth": _("A month"),
        "tvShow": _("Show"),
        "tvStarting": _("The show starts on the PC…"),
        "tvLate": _("The show did not start: look at the window of mh on the PC."),
    }
