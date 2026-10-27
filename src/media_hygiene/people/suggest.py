"""Who a group nobody is given looks like: "Papy?" (TODO 0326).

Each face of the group is compared with the verified faces of every person; its best
match counts, and the person's score is the median of those best matches over the
group, so that one look-alike face does not decide. A face the user took out of
someone (`rejected`) never counts towards them. Only a score above `SUGGEST` is
shown: a suggestion, lower than `[people] similarity` (an attribution), naming
nothing on its own. A second person is shown when close to the first (siblings).

Cost (estimated, not measured): `SAMPLE` faces per group and `REFERENCE` verified
faces per person bound it: 1,000 groups and 20 people make one product of 12,000 by
4,000 vectors of 128 values, about 6 GFLOP, a second or so with numpy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import vector_of
from media_hygiene.people.views import spread

if TYPE_CHECKING:
    from collections.abc import Mapping

    from numpy.typing import NDArray

    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.sections import Sections

# Below SFace's 0.363 "same person": a hint to check, never an attribution. Estimated
# from SFace's documented threshold, not measured on real faces (none here).
SUGGEST: Final = 0.30
SECOND: Final = 0.05  # a second person within this of the first is shown too
SAMPLE: Final = 12  # faces of a group compared
REFERENCE: Final = 200  # verified faces of a person compared
_MOST: Final = 2


def suggestions(
    board: PeopleBoard,
    sections: Sections,
    ruled_out: Mapping[int, frozenset[str]],
) -> dict[int, list[dict[str, object]]]:
    """The people each group nobody is given looks like.

    Args:
        board: The faces of the page.
        sections: What the page shows.
        ruled_out: The names each face is not, by number.

    Returns:
        By index of section, one or two `{name, score}`, the closest first.
    """
    people = {
        section.name: _vectors(board, spread(section.faces, REFERENCE))
        for section in sections.shown
        if section.name and section.verified and section.faces
    }
    if not people:
        return {}
    found: dict[int, list[dict[str, object]]] = {}
    for index, section in enumerate(sections.shown):
        if section.name or not section.faces:
            continue
        keys = spread(section.faces, SAMPLE)
        group = _vectors(board, keys)
        scores: list[tuple[float, str]] = []
        for name, known in people.items():
            usable = [
                at for at, key in enumerate(keys) if name not in ruled_out.get(key, ())
            ]
            if not usable:
                continue
            best = (group[usable] @ known.T).max(axis=1)
            scores.append((float(np.median(best)), name))
        scores.sort(reverse=True)
        kept = [
            {"name": name, "score": round(score, 2)}
            for score, name in scores[:_MOST]
            if score >= SUGGEST and score >= scores[0][0] - SECOND
        ]
        if kept:
            found[index] = kept
    return found


def _vectors(board: PeopleBoard, keys: tuple[int, ...]) -> NDArray[np.float32]:
    """The vectors of faces of the board, one row each.

    Args:
        board: The faces of the page.
        keys: Their numbers.

    Returns:
        The rows.
    """
    return np.stack([vector_of(board.faces[key].embedding) for key in keys])
