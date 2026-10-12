"""Several problems at once: one line saying what they share, then one bullet each.

A single problem keeps its whole sentence; with more, the shared explanation ("a typo,
or a setting of a newer version?") is said once, and each bullet only names its place.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import APP_NAME
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Sequence

BULLET: Final = "\n  • "


@dataclass(frozen=True, slots=True)
class Explained:
    """One problem: its whole sentence when alone, its place among others."""

    unknown: bool  # an unknown key or variable, as opposed to a refused value
    sentence: str
    place: str  # where it was written; a refused value adds its reason
    guess: str | None = None  # the known look-alike of an unknown name


def this_version() -> str:
    """Name this version, for "unknown to version 0.3.0".

    Returns:
        The installed version.
    """
    return version(APP_NAME)


def explained(problems: Sequence[Explained]) -> str:
    """The message of one or several problems.

    Args:
        problems: At least one.

    Returns:
        The sentence of a single problem, or a heading and one bullet per problem.
    """
    if len(problems) == 1:
        return problems[0].sentence
    count = len(problems)
    only_unknown = all(problem.unknown for problem in problems)
    if only_unknown:
        heading = ngettext(
            "{count} setting is unknown to version {version} (a typo, or a setting "
            "of a newer version?):",
            "{count} settings are unknown to version {version} (a typo, or a setting "
            "of a newer version?):",
            count,
        ).format(count=count, version=this_version())
    else:
        heading = ngettext(
            "{count} setting cannot be used:", "{count} settings cannot be used:", count
        ).format(count=count)
    bullets = (_bullet(problem, said=only_unknown) for problem in problems)
    return heading + "".join(BULLET + bullet for bullet in bullets)


def _bullet(problem: Explained, *, said: bool) -> str:
    """The bullet of one problem among others.

    Args:
        problem: The problem.
        said: The heading already says the names are unknown.

    Returns:
        E.g. `'timezon' in [general] of config.toml: did you mean 'timezone'?`.
    """
    place, guess = problem.place, problem.guess
    if not problem.unknown or said:
        if guess is None:
            return place
        return _("{place}: did you mean '{key}'?").format(place=place, key=guess)
    if guess is None:
        return _("{place}: unknown to version {version}").format(
            place=place, version=this_version()
        )
    return _("{place}: unknown to version {version}; did you mean '{key}'?").format(
        place=place, version=this_version(), key=guess
    )
