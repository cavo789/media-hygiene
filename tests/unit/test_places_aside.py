"""Clusters set aside on the map (TODO 0234): a circle in `config.toml`, not a rank.

Two children in a car are no place: ✕ sets the cluster aside. A later audit that moves
its middle by a few metres still matches; two clusters in one circle go together; the
comments of the file are kept; restored, the circle leaves the file.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

from media_hygiene.config.places_settings import ASIDE_RADIUS_M, IgnoredSpot
from media_hygiene.constants import MediaKind
from media_hygiene.geo.distance import Point
from media_hygiene.places.board_state import NOT_ASIDE, BoardView, board_state
from media_hygiene.places.clusters import Cluster
from media_hygiene.places.config_aside import aside_of, read_aside, restore, set_aside
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from media_hygiene.places.hand_desk import HandDesk

CAR = Point(50.30012, 5.10021)
FEW_METRES = 0.00004  # about 4 m north
COMMENTED = """# My settings
[places]
# my own tiles comment
tiles = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
"""


class _NoHand:
    """No photo given a place by hand."""

    given: dict[Path, str] = {}  # noqa: RUF012  # read only

    @staticmethod
    def listed(_place: str) -> list[dict[str, object]]:
        """None."""
        return []


def _view(clusters: tuple[Cluster, ...], aside: tuple[IgnoredSpot, ...]) -> BoardView:
    """A board without places."""
    return BoardView(clusters, (), aside, cast("HandDesk", _NoHand()))


def _cluster(point: Point, pictures: int) -> Cluster:
    """A cluster of pictures."""
    files = tuple(
        MediaFile(
            Path(f"/data/c/Photos/{point.latitude}-{n}.jpg"), 1, 1, MediaKind.IMAGE
        )
        for n in range(pictures)
    )
    return Cluster(point, pictures, 0, (), files)


def test_a_later_audit_moving_the_middle_still_matches() -> None:
    """A position and a radius, not the rank of the cluster."""
    spot = IgnoredSpot(latitude=CAR.latitude, longitude=CAR.longitude)
    moved = Point(CAR.latitude + FEW_METRES, CAR.longitude)
    assert spot.radius_m == ASIDE_RADIUS_M
    assert aside_of(moved, [spot]) == 0
    assert aside_of(Point(CAR.latitude + 0.01, CAR.longitude), [spot]) is None


def test_two_clusters_in_one_circle_are_set_aside_together() -> None:
    """Both hidden; the circle counts both, and opens on the largest."""
    spot = IgnoredSpot(latitude=CAR.latitude, longitude=CAR.longitude, radius_m=400)
    near = Point(CAR.latitude + 0.002, CAR.longitude)  # about 220 m: the next cell
    far = Point(CAR.latitude + 0.05, CAR.longitude)
    clusters = (_cluster(CAR, 5), _cluster(near, 2), _cluster(far, 1))
    state = board_state(_view(clusters, (spot,)))
    rows = cast("list[tuple[object, ...]]", state["clusters"])
    assert [row[5] for row in rows] == [0, 0, NOT_ASIDE]
    [circle] = cast("list[dict[str, object]]", state["aside"])
    assert (circle["pictures"], circle["videos"], circle["cluster"]) == (7, 0, 0)


def test_set_aside_read_back_restore_and_comments_kept(tmp_path: Path) -> None:
    """`[[places.ignored]]` under `[places]`; restored, the table goes."""
    config = tmp_path / "config.toml"
    config.write_text(COMMENTED, "utf-8")
    spot = IgnoredSpot(latitude=CAR.latitude, longitude=CAR.longitude)
    set_aside(config, spot)
    assert read_aside(config) == (spot,)
    text = config.read_text("utf-8")
    assert "# my own tiles comment" in text
    assert "[[places.ignored]]" in text
    restore(config, read_aside(config)[0])
    assert not read_aside(config)
    assert config.read_text("utf-8").startswith(COMMENTED)
    assert "ignored" not in config.read_text("utf-8")


def test_restore_matches_by_position_not_by_rank(tmp_path: Path) -> None:
    """A circle added by hand before it does not make Restore take the wrong one."""
    config = tmp_path / "config.toml"
    first = IgnoredSpot(latitude=10, longitude=10)
    second = IgnoredSpot(latitude=20, longitude=20, radius_m=80)
    set_aside(config, first)
    set_aside(config, second)
    restore(config, first)
    assert read_aside(config) == (second,)
