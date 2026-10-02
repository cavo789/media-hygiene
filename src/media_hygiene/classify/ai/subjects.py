"""From the answers about the samples, the subject of every file of their unit.

The answer most samples gave is the unit's; it is agreed only when at least two
samples gave it and no sample said anything else (3 of 3: sure; 2 of 3, or a lone
photo: to check). An answer of "none of these" is a vote too: when it wins, the
unit gets no subject and the other rules decide.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.models import Subject

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.ai.models import Unit

NONE: Final = ""  # the model's "none of these categories"
_AGREEING: Final = 2


def subjects_of(
    units: Sequence[Unit],
    samples: Mapping[str, tuple[Path, ...]],
    answers: Mapping[Path, str],
) -> dict[Path, Subject]:
    """Give each file of a unit the answer of its samples.

    Args:
        units: The units.
        samples: The samples of each unit, by key.
        answers: The category of each described sample (`NONE`: none fits).

    Returns:
        The subject of every file of a unit whose samples chose a category.
    """
    found: dict[Path, Subject] = {}
    for unit in units:
        votes = [answers[path] for path in samples.get(unit.key, ()) if path in answers]
        subject = _majority(votes)
        if subject is not None:
            found.update(dict.fromkeys(unit.members, subject))
    return found


def per_photo(
    units: Sequence[Unit],
    samples: Mapping[str, tuple[Path, ...]],
    answers: Mapping[Path, str],
) -> dict[Path, Subject]:
    """Give each described photo its own answer; the others take their unit's.

    A photo's answer is agreed when another photo of its unit gave the same one.

    Args:
        units: The units.
        samples: Every photo of each unit, by key.
        answers: The category of each described photo.

    Returns:
        The subject of each file.
    """
    found = subjects_of(units, samples, answers)
    for unit in units:
        votes = Counter(
            answers[path] for path in samples.get(unit.key, ()) if path in answers
        )
        for path in samples.get(unit.key, ()):
            answer = answers.get(path, NONE)
            if answer == NONE:
                found.pop(path, None)
                continue
            found[path] = Subject(answer, votes[answer] >= _AGREEING)
    return found


def _majority(votes: Sequence[str]) -> Subject | None:
    """The answer most samples gave.

    Args:
        votes: The answers, in sample order.

    Returns:
        Its subject, or None without answers or when "none" wins.
    """
    if not votes:
        return None
    counted = Counter(votes)
    answer, count = counted.most_common(1)[0]
    if answer == NONE:
        return None
    return Subject(answer, count == len(votes) and count >= _AGREEING)
