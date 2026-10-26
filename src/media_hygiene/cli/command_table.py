"""The table of the commands, before `--help` sorts them and marks the read-only."""

from __future__ import annotations

from media_hygiene.cli.command_actions import action_commands
from media_hygiene.i18n import _


def command_table(analyse: str, act: str) -> tuple[tuple[str, str, str], ...]:
    """List the commands, unsorted and before the read-only marker.

    Args:
        analyse: The translated name of the panel of analyses.
        act: The translated name of the panel of actions.

    Returns:
        Name, panel and help text of each command.
    """
    return (
        (
            "audit",
            analyse,
            _("Find exact duplicates and broken files."),
        ),
        (
            "status",
            analyse,
            _("Where am I? The last audit, the quarantine, what is left: no scan."),
        ),
        (
            "menu",
            analyse,
            _(
                "Every step of the guides with its command, the next one first: "
                "what 'mh' alone shows, Enter runs it."
            ),
        ),
        (
            "home",
            act,
            _(
                "The home page in your browser: where you are, the next step as a "
                "button, every step of the guides, the reports."
            ),
        ),
        (
            "crosscheck",
            analyse,
            _(
                "Run Czkawka, an independent duplicate finder, then compare its "
                "groups with a fresh audit: a second opinion."
            ),
        ),
        (
            "classify",
            analyse,
            _(
                "Propose where every photo and video should go: year, event, "
                "category, and what lone photos show with an optional local AI 🤖"
            ),
        ),
        (
            "review-sort",
            act,
            _("Name the events of the classify proposal one by one in your browser."),
        ),
        (
            "places",
            analyse,
            _(
                "Name your places on a map of where the photos were taken; saved "
                "into config.toml for the 'place' and 'trip' rules."
            ),
        ),
        (
            "review",
            analyse,
            _(
                "Set burst shots aside, one series at a time, with the keyboard in "
                "your browser; 'clean --decisions' then moves them."
            ),
        ),
        *action_commands(act),
        (
            "tags",
            analyse,
            _(
                "Give every photo words to find it by, kept in the cache, never in "
                "the photos: its folders, name, date and place, and what it shows "
                "with an optional local AI 🤖"
            ),
        ),
        (
            "search",
            act,
            _(
                "Find photos by their words in your browser (or as a table): "
                "the words 'tags' gave them."
            ),
        ),
        (
            "browse",
            act,
            _(
                "The search page opened on your folders: walk "
                "through them, set photos aside; 'clean --decisions' then moves them."
            ),
        ),
        (
            "slideshow",
            analyse,
            _(
                "Show photos on the TV, the phone choosing the next one: a folder, "
                "a search or an album."
            ),
        ),
        (
            "share",
            analyse,
            _(
                "Prepare an album for sending: resized copies without the GPS "
                "position, a folder and a zip, for a mail or a social network."
            ),
        ),
        (
            "people",
            analyse,
            _(
                "Find the faces in the photos, group those alike and name them in "
                "your browser. Faces kept in the cache, never sent anywhere."
            ),
        ),
        (
            "inventory",
            analyse,
            _(
                "Export every photo and video with what the audits learnt to Excel,"
                " from the cache alone: no file is read."
            ),
        ),
        (
            "launcher",
            analyse,
            _("Write 'mh', a short command holding your folders: mh audit, mh clean."),
        ),
        (
            "history",
            analyse,
            _("List the runs and what they did."),
        ),
        (
            "reports",
            analyse,
            _("List the HTML reports of previous audits and cleans."),
        ),
        (
            "config",
            analyse,
            _("Show every setting, where it comes from, and the mount points."),
        ),
    )
