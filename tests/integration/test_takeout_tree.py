"""A Google Photos Takeout next to the PC's folders: its `.json` files travel (0217).

Synthetic: no real Takeout was at hand. The names and fields follow the tools that
read Takeouts.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import TYPE_CHECKING, Final

from typer.testing import CliRunner

from media_hygiene.classify.models import DateSource
from media_hygiene.constants import KeepReason
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.classify import ClassifyService
from media_hygiene.services.clean import CleanService
from tests.support.cli import point_mounts, run
from tests.support.media import MediaFactory
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.paths.locations import Locations

# 2019-06-12 12:00:00 UTC.
_TAKEN: Final = 1_560_340_800
_BRUSSELS: Final = (50.8467, 4.3525)


def write_json(path: Path, title: str) -> Path:
    """Write a Takeout `.json`: a date, a place, a description."""
    document = {
        "title": title,
        "description": "Grand-place",
        "photoTakenTime": {"timestamp": str(_TAKEN), "formatted": "12 juin 2019"},
        "geoData": {"latitude": _BRUSSELS[0], "longitude": _BRUSSELS[1]},
    }
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def takeout_tree(data: Path) -> dict[str, Path]:
    """A Takeout (a year folder, an album repeating a photo) and a PC folder."""
    media = MediaFactory(data / "c")
    photos = "Takeout/Google Photos"
    year = media.image(f"{photos}/Photos from 2019/IMG_0001.jpg", seed=1)
    album = media.copy(year, f"{photos}/Bruxelles/IMG_0001.jpg")
    pc = media.copy(year, "PC/Photos/IMG_0001.jpg")
    undated = media.image(f"{photos}/Photos from 2019/received_picture.png", seed=2)
    return {
        "year": year,
        "album": album,
        "pc": pc,
        "undated": undated,
        "year_json": write_json(
            year.with_name("IMG_0001.jpg.supplemental-metadata.json"), year.name
        ),
        "album_json": write_json(album.with_name("IMG_0001.jpg.json"), album.name),
        "undated_json": write_json(
            undated.with_name("received_picture.png.supplemental-me.json"),
            undated.name,
        ),
        "plain_json": write_json(year.parent / "metadata.json", "Photos from 2019"),
    }


def test_takeout_audit_clean_classify(locations: Locations) -> None:
    """Sidecars paired, the album copy kept, a copy set aside with its `.json`."""
    tree = takeout_tree(locations.data_dir)
    runtime = make_runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    plan = findings.plan
    paired = {sidecar.file.path: sidecar.companions for sidecar in plan.sidecars}
    assert paired[tree["year_json"]] == {"IMG_0001.jpg"}
    assert paired[tree["undated_json"]] == {"received_picture.png"}
    assert tree["plain_json"] not in paired
    (decision,) = plan.decisions
    assert decision.keeper.path == tree["album"]
    assert decision.reason is KeepReason.MEANINGFUL_FOLDER
    assert {file.path for file in plan.orphans} == {tree["year_json"]}

    service = CleanService(runtime, NullProgress())
    service.ensure_ready()
    service.execute(service.feasible(plan))
    assert not tree["year"].exists()
    assert not tree["year_json"].exists()  # set aside with its photo
    assert tree["album_json"].is_file()
    assert tree["plain_json"].is_file()  # describes nothing: left alone

    result = ClassifyService(runtime, NullProgress()).run()
    dated = {
        proposal.file.path: proposal for proposal in result.classification.proposals
    }
    undated = dated[tree["undated"]]
    assert undated.dating is not None
    assert undated.dating.source is DateSource.TAKEOUT
    assert undated.dating.when.date() == datetime(2019, 6, 12).date()  # noqa: DTZ001
    metadata = undated.file.metadata
    assert metadata is not None
    assert (metadata.latitude, metadata.longitude) == _BRUSSELS


def test_takeout_gives_its_words(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`tags` dates and places an undated photo from its `.json`."""
    tree = takeout_tree(locations.data_dir)
    point_mounts(locations, monkeypatch)
    runner = CliRunner()
    assert run(runner, "audit").exit_code == 0
    tagged = run(runner, "tags", "--no-describe")
    assert tagged.exit_code == 0, tagged.output
    with closing(sqlite3.connect(locations.cache_dir / "index.sqlite")) as index:
        rows = index.execute(
            "SELECT source, value FROM tags WHERE path = ?", (str(tree["undated"]),)
        ).fetchall()
    words = set(rows)
    assert ("date", "2019") in words
    assert any(source == "place" for source, _value in words)
