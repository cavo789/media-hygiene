"""`sort` into a separate target: mounted, persistent, and `classify` is idempotent."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.classify import ClassifyService
from tests.support.runtime import make_runtime
from tests.support.sorting import (
    PHOTOS,
    build_library,
    classify,
    name_first_event,
    sort,
)

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime


def target_runtime(
    locations: Locations, target: str, mounts: tuple[str, ...]
) -> Runtime:
    """A runtime sorting into `target`, with these folders mounted."""
    data = locations.data_dir
    points = frozenset(data / mount for mount in mounts)
    for point in points:
        point.mkdir(parents=True, exist_ok=True)
    runtime = make_runtime(locations, {"classify": {"target": target}})
    return replace(runtime, mounts=MountTable(points))


@pytest.mark.parametrize(
    ("target", "mounts"),
    [("D:\\Tri", (PHOTOS, "d/Tri")), ("C:\\Photos\\Tri", (PHOTOS,))],
)
def test_classify_after_a_sort_into_a_target_proposes_nothing(
    locations: Locations, target: str, mounts: tuple[str, ...]
) -> None:
    """A target of its own, or one inside the mounted folder: nothing moves again."""
    build_library(locations.data_dir)
    runtime = target_runtime(locations, target, mounts)
    name_first_event(classify(runtime))
    result = sort(runtime)
    assert result.manifest.intact
    assert result.moves.moved
    proposals = ClassifyService(runtime, NullProgress()).run().classification.proposals
    moving = [(p.file.path, p.folder) for p in proposals if not p.in_place]
    assert not moving
