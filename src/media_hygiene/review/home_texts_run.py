"""The texts of the home page around a step run: its dialogs, the copy box, palette."""

from __future__ import annotations

from markupsafe import escape

from media_hygiene.i18n import _


def run_texts() -> dict[str, str]:
    """The texts of the steps run, of the dialogs and of the palette.

    Returns:
        By key, in the language in use.
    """
    return {**_dialogs(), **_palette(), "keys": _keys()}


def _dialogs() -> dict[str, str]:
    """A step's form, its confirmation, its run, the copy box, the stopped page.

    Returns:
        By key.
    """
    return {
        "toFill": _("To fill in"),
        "formNote": _(
            "What you type here replaces the console menu's (type it yourself)."
        ),
        "fillEach": _("Fill in each field."),
        "cancel": _("Cancel"),
        "close": _("Close"),
        "keep": _("Keep"),
        "confirmTitle": _("{title}: for good?"),
        "asksAgain": _("mh asks you again in {window} before touching anything."),
        "stepStarted": _("Step started"),
        "runsConsole": _(
            "{command} runs in {window}: answer it if it asks something, then this "
            "page comes back by itself."
        ),
        "runsPage": _(
            "{command} opens its page here, in this tab; its ⌂ Back to the home page "
            "brings you back to this very place."
        ),
        "termComment": _(
            "mh keeps the hand until the end, then opens the home page again"
        ),
        "switchNow": _(
            "Switch to {window} now (Alt+Tab, or its button in the taskbar): it may "
            "ask you something."
        ),
        "nothingMoves": _("Nothing moves? Look at {window} (Alt+Tab)."),
        "notOpenedByMh": _(
            "Not opened by mh? Type the command yourself; this page is closed."
        ),
        "failed": _("Not sent (error {status})."),
        "copied": _("Command copied"),
        "copyIt": _("Copy it (Ctrl+C):"),
        "copyThe": _("Copy the command {command}"),
        "copiedText": _("Copied: {text}"),
        "selectIt": _("Select {text} and press Ctrl+C."),
        "copyHow": _(
            "Stop this page with Ctrl+C in the window where mh runs, paste the command "
            "there (right click), then Enter."
        ),
        "loading": _("Preparing the home page…"),
        "loadingSlow": _(
            "Still reading the tool folders: the first time after a start, it can "
            "take a minute."
        ),
        "starting": _("Sent: the step starts in {window}…"),
        "stoppedTitle": _("Media Hygiene is stopped"),
        "stoppedText": _(
            "Its window was closed (or Ctrl+C was pressed in it). You can close this "
            "tab. To open it again: type mh in PowerShell, or double-click the "
            "Desktop icon."
        ),
    }


def _palette() -> dict[str, str]:
    """The palette (Ctrl+K) and its keys.

    Returns:
        By key.
    """
    return {
        "palettePlaceholder": _("What do you want to do? duplicates, phone, undo…"),
        "actions": _("Actions"),
        "choose": _("choose"),
        "launch": _("to run it"),
        "enterKey": _("Enter"),
        "escKey": _("Esc"),
        "goTo": _("Go to"),
        "goStage": _("Go to stage {stage} of the cycle"),
        "goTools": _("Go to the tools"),
        "goShare": _("Go to Share"),
        "goHome": _("Go to the home page"),
        "results": _("{count} results"),
        "nothingMatches": _("Nothing matches. Try duplicates, phone, NAS or undo."),
        "keyboard": _("Keyboard"),
        "keysTitle": _("Everything works with the keyboard too"),
    }


def _keys() -> str:
    """The list of the keys, as `<dt>` and `<dd>` pairs.

    Returns:
        The markup, its words escaped.
    """
    pairs = (
        (
            "<kbd>Ctrl</kbd> <kbd>K</kbd> / <kbd>/</kbd>",
            _("What do you want to do? Every action, by everyday words."),
        ),
        (
            f"<kbd>{escape(_('Enter'))}</kbd>",
            _("When the page opens, runs the next step, as in the console's menu."),
        ),
        (
            "<kbd>Tab</kbd> <kbd>Shift</kbd> + <kbd>Tab</kbd>",
            _(
                "From one element to the next; the first one leads straight to the "
                "content."
            ),
        ),
        ("<kbd>↑</kbd> <kbd>↓</kbd>", _("In the menu on the left and in the palette.")),
        (f"<kbd>{escape(_('Esc'))}</kbd>", _("Closes what is open.")),
        ("<kbd>?</kbd>", _("This help.")),
    )
    return "".join(f"<dt>{key}</dt><dd>{escape(text)}</dd>" for key, text in pairs)
