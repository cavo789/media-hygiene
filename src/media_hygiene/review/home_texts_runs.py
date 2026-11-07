"""The texts of the face scan (0424) and search by meaning (0425) of the home page.

Each dialog reuses the shape and the shared words of the tags dialog (`tags_texts`):
figures first, a question, the progress, Stop.
"""

from __future__ import annotations

from media_hygiene.i18n import _


def runs_texts() -> dict[str, str]:
    """The texts of the faces and meaning dialogs.

    Returns:
        By key, in the language in use.
    """
    return {
        "peopleTitle": _("Find the faces in your photos"),
        "peopleText": _(
            "Two small local models find the faces, on this computer: nothing is "
            "sent. Only the cache is written: your photos are not changed."
        ),
        "peoplePreparing": _("Counting the photos to scan…"),
        "peopleAsk": _(
            "{count} photos to scan for faces, about {time}. Each photo's faces are "
            "kept at once: a stop loses nothing, the next run goes on."
        ),
        "peopleNothing": _(
            "Every photo is scanned already: the people page shows the faces."
        ),
        "peopleNow": _("Scan now"),
        "peopleHour": _("Scan for 1 h"),
        "peopleRunning": _("Finding faces…"),
        "peopleStopped": _("Stopped: the next scan goes on where this one stopped."),
        "spotsHere": _("🤖 Let the local AI name the landmark"),
        "spotsTitle": _("🤖 Which landmark does each photo show?"),
        "spotsText": _(
            "Needs a local AI model. It sees each located photo and picks one of the "
            "landmarks within 1 km, or none. The photos go to your own model only; "
            "only the cache is written; a name you typed is never replaced."
        ),
        "spotsPreparing": _("Looking for the photos with a landmark around…"),
        "spotsAsk": _(
            "{count} photos to show to {model}, about {time}. Each pick is kept at "
            "once: a stop loses nothing, the next run goes on."
        ),
        "spotsNoModel": _(
            "These photos would be shown to a local vision model: choose one below "
            "(Ollama), no photo is sent until you ask."
        ),
        "spotsNothing": _("No photo to ask about: none has a landmark left to pick."),
        "spotsNow": _("🤖 Ask about these {count} photos"),
        "spotsHour": _("Ask for 1 h"),
        "spotsRunning": _("The model looks at the photos…"),
        "spotsStopped": _("Stopped: what was picked is kept, the next run goes on."),
        "spotsShown": _("{shown} of the {count} photos it will ask about:"),
        "meaningOpen": _("Build search by meaning"),
        "meaningTitle": _("Search by meaning"),
        "meaningText": _(
            "A local model looks at each photo on this computer's processor, so that "
            "search finds photos by what they show. Nothing is sent; only the cache "
            "is written."
        ),
        "meaningPreparing": _("Counting the photos to look at…"),
        "meaningAsk": _(
            "{count} photos to look at with {model}, about {time}. Each one is kept "
            "at once: a stop loses nothing, the next run goes on. The first time, "
            "the model is downloaded once (about 900 MB)."
        ),
        "meaningNothing": _("Every photo is looked at already."),
        "meaningNow": _("Look now"),
        "meaningHour": _("Look for 1 h"),
        "meaningRunning": _("Looking at the photos…"),
        "meaningStopped": _("Stopped: the next run goes on where this one stopped."),
    }
