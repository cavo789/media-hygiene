"""A name proposed for a new event: its place, its day, and what it was (0477).

After an import the slideshow should tell « Promenade à Liège » without the user typing
it. The name is built from what the index already knows, no AI call: the place (a place
of the user's, else the town), the day, and an activity most of the photos' vision tags
share (`walk`, `forest` → *Walk*). It is a proposal only: the search's Events view
offers it, the user confirms or changes it in one click.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import month_name
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from datetime import date

# An activity is named when at least this share of the described photos shows it.
SHARED: Final = 0.5


def _walk() -> str:
    return _("Walk")


def _birthday() -> str:
    return _("Birthday")


def _beach() -> str:
    return _("Beach")


def _wedding() -> str:
    return _("Wedding")


def _hike() -> str:
    return _("Hike")


def _skiing() -> str:
    return _("Skiing")


def _party() -> str:
    return _("Party")


def _picnic() -> str:
    return _("Picnic")


def _concert() -> str:
    return _("Concert")


# The words of the vision tags (English and French: the model answers in the
# user's language) → the activity they tell; its name translated when shown.
ACTIVITIES: Final[Mapping[str, Callable[[], str]]] = MappingProxyType(
    {
        **dict.fromkeys(("walk", "walking", "promenade", "stroll", "balade"), _walk),
        **dict.fromkeys(("hike", "hiking", "randonnée", "trail", "sentier"), _hike),
        **dict.fromkeys(
            ("birthday", "anniversaire", "birthday cake", "candles", "bougies"),
            _birthday,
        ),
        **dict.fromkeys(("beach", "plage", "seaside", "bord de mer"), _beach),
        **dict.fromkeys(("wedding", "mariage", "bride", "mariée"), _wedding),
        **dict.fromkeys(("ski", "skiing", "piste", "ski slope"), _skiing),
        **dict.fromkeys(("party", "fête", "celebration"), _party),
        **dict.fromkeys(("picnic", "pique-nique"), _picnic),
        **dict.fromkeys(("concert", "stage", "scène"), _concert),
    }
)


@dataclass(frozen=True, slots=True)
class TitleFacts:
    """What the index knows of a group of new photos."""

    place: str  # the user's place, else the town; empty without GPS
    day: date | None  # its first day
    activity: str = ""  # translated, capitalised; empty when none is shared


def activity_of(words: Iterable[Iterable[str]]) -> str:
    """The activity most of the described photos share.

    Args:
        words: The vision words of each described photo.

    Returns:
        Its translated name (`Walk`), or empty when none reaches `SHARED`.
    """
    counts: Counter[Callable[[], str]] = Counter()
    described = 0
    for photo in words:
        described += 1
        counts.update(
            {told for word in photo if (told := ACTIVITIES.get(word.casefold()))}
        )
    if not counts:
        return ""
    name, seen = counts.most_common(1)[0]
    return name() if seen >= described * SHARED else ""


def day_text(day: date) -> str:
    """A day as a name says it: `29 October`, `29 octobre`.

    Args:
        day: The day.

    Returns:
        It, translated.
    """
    return _("{day} {month}").format(day=day.day, month=month_name(day.month))


def proposed_title(facts: TitleFacts) -> str:
    """Name a group: activity at place, else place and day, else the day.

    Args:
        facts: Its place, day and activity.

    Returns:
        « Walk in Liège », « Liège — 29 October », « 29 October », or empty.
    """
    if facts.place and facts.activity:
        return _("{activity} in {place}").format(
            activity=facts.activity, place=facts.place
        )
    day = day_text(facts.day) if facts.day is not None else ""
    if facts.place and day:
        return f"{facts.place} — {day}"
    return facts.place or day
