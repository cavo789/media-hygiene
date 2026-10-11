"""The `person` rule: the events where someone named on the people page shows.

The names of each photo come from its faces (`search.people_words`): a face confirmed
on the page, or close enough to one; suggestions never count. An event is "with Chloé"
when at least `min_share` percent of its files show her (10 by default: she may be the
one taking the pictures); a file outside any event is read alone. With `all = true`,
every name must reach that share; otherwise, the photos showing any of them count.
Names are compared without case nor accents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.people.folding import folded

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

    from media_hygiene.classify.models import Event, MediaInput
    from media_hygiene.classify.rules.matchers import Test
    from media_hygiene.config.classify_rules import ClassifyRule

MIN_SHARE: Final = 10  # percent of an event's files, when the rule says nothing
_PERCENT: Final = 100


def person_test(
    rule: ClassifyRule,
    people: Mapping[Path, tuple[str, ...]],
    event_of: Mapping[Path, Event],
) -> Test:
    """A test of the people on the files: the whole event, or the file alone.

    Args:
        rule: The `person` rule.
        people: The names on each photo, as `[[people.person]]` writes them.
        event_of: The event of each file that has one.

    Returns:
        The test.
    """
    wanted = frozenset(folded(name) for name in rule.names)
    share = rule.min_share or MIN_SHARE
    on = {path: wanted & {folded(n) for n in names} for path, names in people.items()}

    def shown(paths: Collection[Path]) -> bool:
        """Tell whether the people show on enough of these files.

        Args:
            paths: The files of an event, or one file.

        Returns:
            True when the share is reached.
        """
        found = [on.get(path, frozenset()) for path in paths]
        if rule.all:
            counts = [sum(name in names for names in found) for name in wanted]
        else:
            counts = [sum(bool(names) for names in found)]
        return all(count and count * _PERCENT >= share * len(paths) for count in counts)

    events = {event.event_id: event for event in event_of.values()}
    taken = frozenset(key for key, event in events.items() if shown(event.paths))

    def test(file: MediaInput) -> bool:
        """Tell whether one file goes with the people of the rule.

        Args:
            file: The file.

        Returns:
            True for a file of an event showing them, or a lone file showing them.
        """
        event = event_of.get(file.path)
        if event is not None:
            return event.event_id in taken
        return shown((file.path,))

    return test
