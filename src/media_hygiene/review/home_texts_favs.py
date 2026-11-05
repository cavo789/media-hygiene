"""The texts of the favourites (0484), the tiles' edit (0516), random photos (0485)."""

from __future__ import annotations

from media_hygiene.i18n import _


def favourite_texts() -> dict[str, str]:
    """The texts of the starred actions.

    Returns:
        By key, in the language in use.
    """
    return {
        "samplesTitle": _("Random photos"),
        "samplesNote": _(
            "Drawn at each visit; a click opens the Library on its folder."
        ),
        "sampleOpen": _("Open the Library on {folder}"),
        "tilesEdit": _("Edit"),
        "tilesDone": _("Done"),
        "tilesReset": _("Reset"),
        "tilesEditNote": _("✕ hides a tile, ← and → move it; saved at once."),
        "tilesHidden": _("Hidden:"),
        "tileHide": _("Hide {tile}"),
        "tileShow": _("Show {tile}"),
        "tileLeft": _("Move {tile} before"),
        "tileRight": _("Move {tile} after"),
        "tilesFailed": _(
            "The tiles could not be saved in config.toml (error {status})."
        ),
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
        "favFailed": _(
            "The favourites could not be saved in config.toml (error {status})."
        ),
        "favForbidden": _(
            "The favourites can only be saved from this PC's own address"
            " (http://localhost)."
        ),
    }
