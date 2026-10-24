"""The actions and the spaces of the home page, from the lines of `mh menu`.

Every action keeps the number `mh menu` gives it: the number a button sends is the
one `mh` runs. Its state (available, done, proposed, its reason) is the menu's.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.cli.menu_entry import Risk
from media_hygiene.constants import Locale
from media_hygiene.docs.served import served_url
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeLink
from media_hygiene.review.home_views import HomeAction, HomeField, HomeGroup, HomeNext
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

if TYPE_CHECKING:
    from media_hygiene.cli.menu_entry import Area, Doc
    from media_hygiene.cli.menu_steps import Menu, MenuStep
    from media_hygiene.cli.status_step import NextStep

_RISKS: Final = {Risk.SAFE: "safe", Risk.UNDO: "undo", Risk.FINAL: "final"}


def link(doc: Doc | None) -> HomeLink | None:
    """A chapter of the documentation, in the language in use and in English.

    Served by the tool when its docs are there (0270), else on the public site.

    Args:
        doc: The chapter.

    Returns:
        Both addresses; None without a chapter.
    """
    if doc is None:
        return None
    return HomeLink(url=served_url(doc), url_en=served_url(doc, Locale.EN))


def home_actions(menu: Menu) -> tuple[HomeAction, ...]:
    """Every action the menu lists, with its state.

    Args:
        menu: The menu, every action once.

    Returns:
        The actions, in the menu's order.
    """
    return tuple(_action(line) for line in menu.steps)


def _action(line: MenuStep) -> HomeAction:
    """One action, as the menu fills it.

    Args:
        line: The menu's line.

    Returns:
        The action for the page.
    """
    step = line.step
    shown = line.command or step.typed or step.command
    return HomeAction(
        name=step.name,
        space=step.space.value,
        title=step.title,
        text=step.text,
        command=f"{LAUNCHER_FUNCTION} {shown}",
        risk=_RISKS[step.risk],
        kind=step.kind.value,
        icon=step.icon or "terminal",
        keywords=step.keywords,
        number=line.number,
        available=not line.reason,
        reason=line.reason,
        done=line.done,
        proposed=line.proposed,
        optional=step.optional,
        ai=step.ai,
        windows=step.windows,
        planned=step.planned,
        confirm_title=step.confirm[0] if step.confirm else "",
        confirm_text=step.confirm[1] if step.confirm else "",
        fields=tuple(
            HomeField(
                name=field.name,
                label=field.label,
                example=field.example,
                kind=field.kind.value,
            )
            for field in step.fields
        ),
        doc=link(step.doc),
    )


def home_groups(area: Area, shown: set[str]) -> tuple[HomeGroup, ...]:
    """The groups of a space, each keeping the actions this menu offers.

    Args:
        area: The space.
        shown: The names of the actions offered (the Windows ones left out of bash).

    Returns:
        Its groups.
    """
    return tuple(
        HomeGroup(
            title=group.title,
            actions=tuple(name for name in group.steps if name in shown),
            numbered=group.numbered,
            extra=group.extra,
        )
        for group in area.groups
    )


def home_next(
    menu: Menu, step: NextStep | None, areas: tuple[Area, ...]
) -> HomeNext | None:
    """The next step: why, its command, and where it stands in its guide.

    Args:
        menu: The menu, the proposed line marked.
        step: The step `status` chooses.
        areas: The spaces, to place it in its guide.

    Returns:
        It; None when nothing is left.
    """
    proposed = menu.proposed
    if proposed is None or step is None or proposed.number is None:
        return None
    shown = {line.step.name for line in menu.steps}
    return HomeNext(
        name=proposed.step.name,
        number=proposed.number,
        command=f"{LAUNCHER_FUNCTION} {proposed.command}",
        why=step.text[:1].upper() + step.text[1:],
        where=_place(proposed.step.name, areas, shown),
    )


def _place(name: str, areas: tuple[Area, ...], shown: set[str]) -> str:
    """Where an action stands in the first numbered guide that holds it.

    Args:
        name: The action.
        areas: The spaces.
        shown: The actions offered.

    Returns:
        E.g. "Clean the duplicates · step 3 of 8"; empty outside every guide.
    """
    for area in areas:
        for group in area.groups:
            names = [step for step in group.steps if step in shown]
            if not (area.stage and group.numbered and name in names):
                continue
            place = _("step {index} of {count}").format(
                index=names.index(name) + 1, count=len(names)
            )
            prefix = "" if group is area.groups[0] else f"{group.title} · "
            return f"{area.long} · {prefix}{place}"
    return ""
