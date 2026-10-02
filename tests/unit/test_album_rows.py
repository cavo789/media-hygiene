"""What an album gathers from a plan: category as edited, event by id or name, rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.album_rows import (
    Criteria,
    category_of,
    chosen_rows,
    event_name,
)
from media_hygiene.classify.models import Band
from media_hygiene.classify.plan_file import PlanEvent
from media_hygiene.classify.workbook.edits import CategoryEdit, Edits, EventEdit, Stay
from tests.support.plans import plan_of, row

if TYPE_CHECKING:
    from media_hygiene.classify.plan_file import PlanRow


def sure(name: str, category: str, rule: str = "") -> PlanRow:
    """A sure row of event e1, decided by `rule`."""
    return row(name, Band.SURE, (category, "e1")).model_copy(update={"rule": rule})


EVENT = PlanEvent(
    id="e1",
    start="2016-07-14",
    end="2016-07-14",
    span="2016-07-14",
    label="",
    rows=("a", "b"),
)
PLAN = plan_of(
    (
        sure("a", "Fêtes", "Christmas"),
        sure("b", "Fêtes"),
        row("c", Band.SURE, ("Mer", "")),
        row("d", Band.STAY).model_copy(update={"values": None}),
    ),
    (EVENT,),
)


def ids(criteria: Criteria, edits: Edits | None = None) -> list[str]:
    """The ids of the rows chosen."""
    return [chosen.id for chosen in chosen_rows(PLAN, edits or Edits(), criteria)]


def test_criteria_combine_and_ignore_case() -> None:
    """Every criterion given must match; case and spaces do not matter."""
    assert not Criteria().given
    assert Criteria(rating=3).given
    assert ids(Criteria(category=" fêtes ")) == ["a", "b"]
    assert ids(Criteria(category="Fêtes", rule="christmas")) == ["a"]
    assert ids(Criteria(event="E1")) == ["a", "b"]
    assert ids(Criteria(event="2016-07-14")) == ["a", "b"]
    assert ids(Criteria(event="nowhere")) == []


def test_the_category_is_the_edited_one() -> None:
    """A renamed category, then an event named, give the album's category."""
    renamed = Edits(categories={"Fêtes": CategoryEdit("Noël")})
    assert ids(Criteria(category="Noël"), renamed) == ["a", "b"]
    named = Edits(events={"e1": EventEdit(name="Kermesse")})
    assert ids(Criteria(category="Kermesse"), named) == ["a", "b"]
    assert ids(Criteria(event="kermesse"), named) == ["a", "b"]
    assert event_name(EVENT, named) == "Kermesse"
    filed = Edits(events={"e1": EventEdit(name="Kermesse", category="Fêtes/2016")})
    assert category_of(PLAN.rows[0], filed) == "Fêtes/2016"
    stay = Edits(events={"e1": EventEdit(category=Stay.STAY)})
    assert category_of(PLAN.rows[0], stay) == "Fêtes"
    assert category_of(PLAN.rows[3], renamed) == ""
    kept = Edits(categories={"Mer": CategoryEdit(Stay.STAY)})
    assert category_of(PLAN.rows[2], kept) == "Mer"
