"""0395: Your rules by kind, then the latest period first; the file keeps its order."""

from __future__ import annotations

from media_hygiene.review.sort_rules_order import group_of, shown_order
from media_hygiene.review.sort_rules_view import RuleLine


def _line(name: str, match: str, position: int, **more: object) -> RuleLine:
    values: dict[str, object] = {
        "name": name,
        "match": match,
        "category": name,
        "dates": "",
        "files": 1,
        "built_in": False,
        "event": "",
        "first": "",
        "last": "",
        "position": position,
    }
    values.update(more)
    return RuleLine.model_validate(values)


def test_the_rules_are_shown_by_kind_then_the_latest_period_first() -> None:
    """Two date rules, three folder-name ones (one dead), a built-in one, a fallback."""
    lines = [
        _line("Existing folders", "existing_folder", 0, built_in=True),
        _line("Kermesse", "path", 1, first="2016-07-14"),
        _line("Old wedding", "date_range", 2, dates="2005-06-04..2005-06-04"),
        _line("Sun Park", "path", 3, files=0),
        _line("Other", "other_category", 4),
        _line("Montenegro", "date_range", 5, dates="2019-07-12..2019-07-19"),
        _line("Durbuy", "path", 6, first="2022-12-25"),
    ]
    assert [line.name for line in shown_order(lines)] == [
        "Montenegro",
        "Old wedding",
        "Durbuy",
        "Kermesse",
        "Sun Park",
        "Other",
        "Existing folders",
    ]
    assert [line.position for line in lines] == list(range(7))  # the file's order
    assert group_of(lines[2]) == "Dates"
    assert group_of(lines[0]) != group_of(lines[1])
