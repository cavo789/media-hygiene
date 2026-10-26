"""The month folder is the event's start month; `00` when only the year is known."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.layout import Values, check_layout, render
from media_hygiene.config.classify_settings import ClassifySettings
from tests.unit.test_classify_engine import by_name, series, shot

MONTHS = ClassifySettings(
    layout="{year}/{year_month}/{category}",
    unsure_layout="{year}/{year_month}/{category}",
    manual_layout="{year}/{year_month}",
)


def test_an_event_over_two_months_goes_whole_to_its_start_month() -> None:
    """28 August to 2 September: every photo in `2009/2009-08`."""
    start = datetime(2009, 8, 28, 10)
    trip = [shot(f"Vacances/{d}.jpg", start + timedelta(days=d)) for d in range(6)]
    folders = {p.folder for p in classify(trip, MONTHS, Scope()).proposals}
    assert folders == {"2009/2009-08/Vacances"}


def test_a_new_year_party_takes_the_year_and_month_of_its_start() -> None:
    """31 December 2009 to 1 January 2010: `2009/2009-12` for every file."""
    party = series("DCIM", datetime(2009, 12, 31, 22), 5)
    found = classify(party, MONTHS, Scope()).proposals
    assert {p.folder.split("/")[1] for p in found if p.folder} == {"2009-12"}
    assert {p.values.year for p in found if p.values} == {2009}


def test_a_meaningful_folder_takes_the_month_of_its_oldest_file() -> None:
    """A folder `Mariage Tom` from March into April: `2018-03`."""
    files = [
        shot("Mariage Tom/a.jpg", datetime(2018, 4, 2, 10)),
        shot("Mariage Tom/b.jpg", datetime(2018, 3, 30, 10)),
    ]
    found = by_name(classify(files, MONTHS, Scope()).proposals)
    assert found["a.jpg"].folder == "2018/2018-03/Mariage Tom"


def test_a_folder_giving_only_the_year_gives_month_00() -> None:
    """`1985/Scan` without EXIF: `1985-00`; `per_file` dates each file on its own."""
    scan = shot("1985/Noël chez Mamy/a.jpg", None)
    (found,) = classify([scan], MONTHS, Scope()).proposals
    assert found.values is not None
    assert found.values.month == 0
    assert found.folder is not None
    assert found.folder.startswith("1985/1985-00")
    per_file = ClassifySettings(layout="{year}/{month}", event_year="per_file")
    (alone,) = classify(
        [shot("DCIM/a.jpg", datetime(2019, 7, 1))], per_file, Scope()
    ).proposals
    assert alone.folder == "2019/07"


def test_the_placeholders_of_a_month() -> None:
    """`{year_month}`, `{month}`, `{month_name}` and `{quarter}`, month known or not."""
    check_layout("{year}/{year_month}")
    november = Values(year=2009, month=11, day=28)
    unknown = Values(year=1985, month=0, day=1)
    layout = "{year_month}/{month}/{month_name}/Q{quarter}"
    assert render(layout, november) == "2009-11/11/November/Q4"
    assert render(layout, unknown) == "1985-00/00/00/Q0"
