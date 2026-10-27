"""The texts of the home page, translated: the shell, the home view and the spaces.

The page reads them as `T.<key>`; a few hold markup (`<kbd>`, `<strong>`, a link),
built here around the translated text escaped. `home_texts_run.py` holds the texts of
the steps run, of the dialogs and of the palette.
"""

from __future__ import annotations

from media_hygiene.i18n import _
from media_hygiene.review.home_texts_family import family_texts
from media_hygiene.review.home_texts_marked import marked_texts
from media_hygiene.review.home_texts_run import run_texts
from media_hygiene.review.home_texts_tags import tags_texts


def home_texts() -> dict[str, str]:
    """Every text of the page, in the language in use.

    Returns:
        By key.
    """
    return {
        **_shell(),
        **_home(),
        **_spaces(),
        **marked_texts(),
        **run_texts(),
        **tags_texts(),
        **family_texts(),
    }


def _shell() -> dict[str, str]:
    """The sidebar, the top bar, the theme.

    Returns:
        By key.
    """
    return {
        "home": _("Home page"),
        "skip": _("Skip to the content"),
        "sidebar": _("Menu of Media Hygiene"),
        "tagline": _("Your photos, in order"),
        "spaces": _("Spaces"),
        "cycle": _("The cycle of your photos"),
        "tools": _("Tools"),
        "share": _("Share"),
        "addFolder": _("Add a folder"),
        "avatarAlt": _("The meerkat of Christophe Avonture"),
        "by": _("by"),
        "display": _("Display"),
        "themeAuto": _("Auto"),
        "themeLight": _("Light"),
        "themeDark": _("Dark"),
        "openMenu": _("Open the menu"),
        "whatToDo": _("What do you want to do?"),
        "yourFolders": _("Your folders ({count})"),
        "folderMissing": _("a folder not found"),
        "available": _("{version} available"),
        "upToDate": _("up to date"),
        "docHome": _("the documentation's home"),
        "documentation": _("Documentation"),
        "doc": _("Doc"),
        "docOf": _("Documentation: {title} (new tab)"),
        "undoLast": _("Undo the last run"),
        "lanTitle": _("On your phone"),
        "lanOpen": _("Same Wi-Fi, open:"),
        "lanCode": _("Code:"),
        "lanNote": _("Until mh stops; never the internet."),
        "lanCa": _("First time on this phone? Install the certificate first:"),
        "lanCaHow": _("How?"),
        "lanPhones": _("Phones paired for good"),
        "lanForget": _("Forget this phone"),
        "addToHome": _(
            "To keep Media Hygiene as an app: Share, then Add to Home Screen."
        ),
        "lanNone": _("No home network found: the phone cannot open this page."),
        "lanPublic": _(
            "Windows counts this Wi-Fi as public: its firewall blocks the phone. "
            "Settings > Network & Internet > Wi-Fi > Private network."
        ),
        "lanFirewall": _(
            "If Windows asks about Docker Desktop: tick Private networks, then Allow."
        ),
        "onThePc": _(
            "From the phone: the audit, the reports, the albums, the search and "
            "browse. Open this page or run this step on the PC."
        ),
        "albumsOpen": _("Open the albums"),
        "albumsText": _(
            "Your albums as on a phone: a cover, the photos by day, full screen with "
            "a swipe. On a phone of the home Wi-Fi too, once paired with mh --lan."
        ),
    }


def _home() -> dict[str, str]:
    """The home view.

    Returns:
        By key.
    """
    return {
        "whereYourPhotos": _("Where your photos stand"),
        "readNow": _(
            "Read just now in the tool folders: nothing was analysed to show this page."
        ),
        "nextStep": _("Next step"),
        "allApplied": _("Everything is applied"),
        "allInOrder": _("Everything is in order"),
        "allInOrderWhy": _(
            "Nothing left to do: everything is applied. New photos? The cycle starts "
            "again at Import."
        ),
        "cycleNote": _("Five stages; the highlighted one is your next step."),
        "youAreHere": _("You are here"),
        "stepsDone": _("{done} of {total} steps done."),
        "whereYouAre": _("Where you are"),
        "tilesNote": _("Each tile leads to its space."),
        "toDo": _("To do"),
        "toCheck": _("To check"),
        "previews": _("Copies, previewed"),
        "openReport": _("Open the report"),
        "threeThings": _("Three things to know before you start"),
        "recentReports": _("Recent reports"),
        "everyReport": _("Every report"),
        "noReport": _("No report yet: the audit writes one."),
        "auditHere": _("Audit in this page"),
        "auditHereText": _(
            "Reads your folders as mh audit does, its progress shown here, without the "
            "console."
        ),
        "auditNow": _("Audit now"),
        "auditStop": _("Stop the audit"),
        "auditRunning": _("Auditing…"),
        "auditBusy": _("An audit already runs: wait for its end, or stop it."),
        "newVersion": _("Media Hygiene {version} is available"),
        "youHave": _("you have {version}"),
        "whatChanges": _("See what changes"),
        "updateNow": _("Update"),
        "later": _("Later"),
    }


def _spaces() -> dict[str, str]:
    """The pages of the spaces and their panels.

    Returns:
        By key.
    """
    return {
        "stageN": _("Stage {stage} of the cycle"),
        "stepN": _("Step {number}:"),
        "done": _("Done"),
        "optional": _("Optional"),
        "planned": _("Planned"),
        "plannedReason": _("Planned with mh push: not in the tool yet."),
        "nothingYet": _("Nothing to do yet."),
        "riskSafe": _("Photos untouched"),
        "riskUndo": _("Undoable"),
        "riskFinal": _("For good"),
        "aiOn": _("Local AI"),
        "aiOff": _("Local AI if set"),
        "aiOnTitle": _("The local model of [classify.ai] also describes the photos"),
        "aiOffTitle": _(
            "Optional: a local model in [classify.ai] model of config.toml"
        ),
        "verbRun": _("Start"),
        "verbPage": _("Open the page"),
        "verbFill": _("Fill in"),
        "verbSoon": _("Soon"),
        "inThisPage": _("In this page"),
        "backupPlanned": _("Planned: mh push is coming."),
        "backupPlannedText": _(
            "The cycle already keeps its place: once the command exists, its entry in "
            "the catalog lights this page, the palette and the console menu."
        ),
        "stillUndoable": _("Still undoable: {what}"),
        "undoThis": _("Undo this run"),
        "nothingToUndo": _("No run to undo for now."),
        "quarantineByRun": _("The quarantine, run by run"),
        "run": _("Run"),
        "files": _("Files"),
        "room": _("Room"),
        "since": _("Since"),
        "quarantineEmpty": _("The quarantine is empty: nothing waits to be freed."),
        "foldersKnown": _("The folders mh knows"),
        "folder": _("Folder"),
        "role": _("Role"),
        "state": _("State"),
        "isLatest": _("is the latest version."),
        "codeOnGitHub": _("The code on GitHub"),
        "imageOnHub": _("The image on Docker Hub"),
    }
