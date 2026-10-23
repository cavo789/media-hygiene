"""Stage 2, clean: the guide of "Clean in short", in its order.

`open`, `history`, `undo` and `purge` live in the reports and history tools; the
guide lists them too, where they come.
"""

from __future__ import annotations

from media_hygiene.cli.menu_entry import Area, Doc, Group, Kind, Risk, Space, Step
from media_hygiene.cli.status_step import Slot
from media_hygiene.i18n import _

LAUNCHER_SELF = Doc(
    "commands/launcher/", "#what-mh-does-by-itself", "#ce-que-mh-fait-lui-même"
)


def clean_steps() -> tuple[Step, ...]:
    """The actions of the clean guide.

    Returns:
        Them, in order.
    """
    return (
        Step(
            "audit",
            Space.CLEAN,
            _("Find the duplicates and the broken files"),
            _(
                "Reads your folders without changing anything; the report opens in "
                "the browser."
            ),
            "audit",
            Risk.SAFE,
            icon="eye",
            keywords=_(
                "duplicates copies analyse scan check damaged broken unreadable"
            ),
            doc=Doc("commands/audit/"),
            slot=Slot.AUDIT,
        ),
        Step(
            "open",
            Space.REPORTS,
            _("Read the reports in your browser"),
            _("The copies grouped, with their previews and the copy kept."),
            "open",
            Risk.SAFE,
            Kind.HOST,
            icon="report",
            keywords=_("report html browser read see"),
            doc=LAUNCHER_SELF,
        ),
        Step(
            "clean",
            Space.CLEAN,
            _("Set the extra copies aside"),
            _(
                "Asks first, compares byte by byte, then moves to the quarantine: "
                "nothing is erased."
            ),
            "clean",
            Risk.UNDO,
            icon="broom",
            keywords=_("clean duplicates copies quarantine delete room"),
            doc=Doc("commands/clean/"),
            slot=Slot.CLEAN,
        ),
        Step(
            "history",
            Space.HISTORY,
            _("See what each run did"),
            _("Its files moved, the room freed, what can still be undone."),
            "history",
            Risk.SAFE,
            icon="history",
            keywords=_("history journal runs"),
            doc=Doc("commands/history/"),
        ),
        Step(
            "undo",
            Space.HISTORY,
            _("Put back the files of the last run"),
            _("Each file goes back exactly where it was."),
            "undo",
            Risk.UNDO,
            icon="undo",
            keywords=_("undo restore put back revert mistake"),
            doc=Doc("commands/undo/"),
            slot=Slot.UNDO,
        ),
        Step(
            "review",
            Space.CLEAN,
            _("Choose the best shots of each burst"),
            _(
                "One series at a time, with the keyboard, in the browser; nothing "
                "moves before you apply."
            ),
            "review",
            Risk.SAFE,
            Kind.PAGE,
            icon="layers",
            keywords=_("bursts series best photos choose"),
            doc=Doc("commands/review/"),
            slot=Slot.REVIEW,
            optional=True,
        ),
        Step(
            "apply",
            Space.CLEAN,
            _("Apply your choices"),
            _("What you set aside in the browser goes to the quarantine."),
            "clean --tier near --decisions",
            Risk.UNDO,
            icon="check",
            keywords=_("apply decisions choices set aside"),
            doc=Doc("clean/10-review-bursts/"),
            slot=Slot.APPLY,
            optional=True,
        ),
        Step(
            "purge",
            Space.HISTORY,
            _("Free the room of the quarantine"),
            _("For good, once the quarantine is checked."),
            "purge",
            Risk.FINAL,
            icon="trash",
            keywords=_("purge free room quarantine erase empty for good"),
            doc=Doc("commands/purge/"),
            slot=Slot.PURGE,
        ),
    )


def clean_area() -> Area:
    """The clean stage: its guide, then "go further".

    Returns:
        It.
    """
    guide = ("audit", "open", "clean", "history", "undo", "review", "apply", "purge")
    further = (
        "review-near",
        "review-pairs",
        "review-junk",
        "review-gone",
        "crosscheck",
        "shrink",
        "clean-delete",
    )
    return Area(
        Space.CLEAN,
        _("Clean up"),
        _("Clean the duplicates"),
        _(
            "Find the extra copies, set them aside, check, then free the room. "
            "Everything goes through the quarantine first: nothing is erased "
            "without you."
        ),
        "broom",
        (
            Group(_("The guide"), guide, numbered=True),
            Group(_("Go further"), further),
        ),
        Doc("clean/quick-guide/"),
        _("Clean in short"),
        stage=2,
    )
