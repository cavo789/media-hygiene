"""The texts of `tags` run by the home page (0343): question, progress, end."""

from __future__ import annotations

from media_hygiene.i18n import _


def tags_texts() -> dict[str, str]:
    """The texts of the tags dialog.

    Returns:
        By key, in the language in use.
    """
    return {
        "tagsEyebrow": _("In this page"),
        "tagsTitle": _("Give your photos words"),
        "tagsText": _(
            "Words from folders, names, dates and places first (seconds), then what "
            "the local AI sees. Only the cache is written: your photos are not changed."
        ),
        "tagsPreparing": _("Words of folders, names, dates and places…"),
        "tagsAsk": _(
            "{count} photos to describe with {model}, about {time}. Each answer is "
            "kept at once: a stop loses nothing, the next run goes on."
        ),
        "tagsNoModel": _(
            "Words written. Set [classify.ai] model to a local vision model "
            "(Ollama) to add what the photos show."
        ),
        "tagsNothing": _("Words written; the AI has already described every photo."),
        "tagsNow": _("Describe now"),
        "tagsHour": _("Describe for 1 h"),
        "tagsNotNow": _("Not now"),
        "tagsRunning": _("Describing…"),
        "tagsRate": _("{rate} photos a minute, about {time} left."),
        "tagsStop": _("Stop after this photo"),
        "tagsStopped": _("Stopped: the next tags run goes on where this one stopped."),
        "tagsBusy": _("Tags already run: wait for the end, or stop them."),
        "tagsHours": _("{h} h {min} min"),
        "tagsMinutes": _("{min} min"),
    }
