"""The texts of the home page's favourites (0484): the stars, the row of cards."""

from __future__ import annotations

from media_hygiene.i18n import _


def favourite_texts() -> dict[str, str]:
    """The texts of the starred actions.

    Returns:
        By key, in the language in use.
    """
    return {
        "favTitle": _("Your favourites"),
        "favNote": _(
            "Drag a card to move it, or Alt+← and Alt+→ on it; the ☆ of an action "
            "adds or removes it."
        ),
        "favSuggested": _(
            "Three suggestions: the ☆ of any action makes it one of your favourites."
        ),
        "favAdd": _("Add to the favourites"),
        "favRemove": _("Remove from the favourites"),
        "favMove": _("Drag to move"),
        "favBusy": _("The favourites are being saved: one moment."),
        "favFailed": _("The favourites could not be saved in config.toml."),
    }
