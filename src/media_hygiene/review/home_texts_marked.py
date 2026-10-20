"""The texts of the home page holding markup: the words escaped, then the tags."""

from __future__ import annotations

from typing import Final

from markupsafe import escape

from media_hygiene.i18n import _

_AUTHOR: Final = (
    '<a href="https://www.avonture.be" target="_blank" rel="noopener">'
    "Christophe Avonture</a>"
)
_SETTING: Final = "<code>[general] check_updates = false</code>"


def marked_texts() -> dict[str, str]:
    """The texts with a key, a link or a bold lead.

    Returns:
        By key, in the language in use.
    """
    stage = f'<a href="#import" data-go="import">{escape(_("Import"))}</a>'
    return {
        "enterHint": _filled(
            _("{key} runs the step, as in the console's menu."),
            key=f"<kbd>{escape(_('Enter'))}</kbd>",
        ),
        "cycleLoop": _filled(
            _("New photos? The cycle starts again at {stage}."), stage=stage
        ),
        "safeLine": _lead(
            _("Nothing moves without you."),
            _(
                "The audit reads your folders and writes a report; your photos are "
                "not touched."
            ),
        ),
        "undoLine": _lead(
            _("Everything that moves can be undone."),
            _("Each run is written in the journal; undo puts each file back."),
        ),
        "finalLine": _lead(
            _("One thing only is for good:"),
            _("freeing the room of the quarantine, once you checked it."),
        ),
        "updateCheck": _filled(
            _(
                "Checked on Docker Hub once a day at most; {setting} in config.toml "
                "turns it off."
            ),
            setting=_SETTING,
        ),
        "aiSet": _lead(
            _("Local AI set."),
            _(
                "classify and tags also describe what your photos show, with the "
                "model of [classify.ai] model; nothing leaves the PC."
            ),
        ),
        "aiNotSet": _lead(
            _("Local AI not set."),
            _(
                "classify and tags work without. For them to describe what your "
                "photos show, set a local model in [classify.ai] model of "
                "config.toml."
            ),
        ),
        "aboutText": _filled(
            _(
                "Made by {author}, the author of the blog avonture.be. The code is "
                "under the MIT licence; the meerkat stays its author's."
            ),
            author=_AUTHOR,
        ),
    }


def _lead(lead: str, rest: str) -> str:
    """A bold lead, then the rest, both escaped.

    Args:
        lead: The words in bold.
        rest: The words after.

    Returns:
        The markup.
    """
    return f"<strong>{escape(lead)}</strong> {escape(rest)}"


def _filled(text: str, **markup: str) -> str:
    """A translated text escaped, its placeholders replaced by markup.

    Args:
        text: The text, with `{name}` placeholders.
        **markup: The markup of each placeholder.

    Returns:
        The markup.
    """
    return str(escape(text)).format(**markup)
