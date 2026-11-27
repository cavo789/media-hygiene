"""0558: the late photos of an event, as the search's tiles."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.late_desk import LATE_PATH, LateDesk
from tests.support.sort_review import classified

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_NO_PLAN = "no plan"


def _nothing_chosen() -> frozenset[str]:
    """No file set aside.

    Returns:
        None.
    """
    return frozenset()


def test_late_photos_of_an_event_as_search_tiles(locations: Locations) -> None:
    """0558: the files of an event's days outside its folder, as tiles, ranked."""
    runtime, _workbook = classified(locations)
    with SearchIndex.open(locations.index_file) as search:
        row = search.connection.execute(
            "SELECT media_date FROM files WHERE media_date IS NOT NULL"
        ).fetchone()
        day = str(row[0])[:10].replace(":", "-")
        config = locations.config_dir / "late.toml"
        config.write_text(
            f'[[classify.rules]]\nname = "Party"\nmatch = "date_range"\n'
            f'category = "Party"\ndates = "{day}..{day}"\n',
            encoding="utf-8",
        )
        late = LateDesk(search, runtime.mapper, config, _nothing_chosen)
        listed = json.loads(late.state().body)["events"]
        assert listed[0]["id"] == "Party"
        view = json.loads(late.event(f"{LATE_PATH}/Party").body)
        assert len(view["hits"]) == listed[0]["total"]
        tile = view["hits"][0]
        assert tile["thumb"].startswith("/thumb/")
        assert tile["likely"] in {"probably", "ask"}
        assert tile["ticked"] is (tile["likely"] == "probably")
        empty = json.loads(late.event(f"{LATE_PATH}/Nope").body)
        assert empty["hits"] == []
