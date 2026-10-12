"""The faces of the documentation demo: sourced, licensed, and never in a burst."""

from __future__ import annotations

import pytest
from PIL import Image

from tests.support.docs.people_story import with_rule
from tests.support.docs.portraits import (
    FACES,
    Person,
    Placement,
    paste_face,
    placement_of,
)

ATTRIBUTION = FACES / "ATTRIBUTION.md"
# The scenes of the burst series (events.py): their shots must stay comparable.
BURSTS = (("balloons", 1), ("mountains", 60), ("sunset", 40))


@pytest.mark.parametrize("person", list(Person))
def test_every_face_has_its_source_and_licence(person: Person) -> None:
    """Each file is listed in ATTRIBUTION.md with its Commons page and its licence."""
    assert (FACES / f"{person}.jpg").is_file()
    line = next(
        line
        for line in ATTRIBUTION.read_text(encoding="utf-8").splitlines()
        if line.startswith(f"| `{person}.jpg`")
    )
    assert "commons.wikimedia.org/wiki/File:" in line
    assert "Public domain" in line


@pytest.mark.parametrize(("kind", "seed"), BURSTS)
def test_no_burst_scene_holds_a_face(kind: str, seed: int) -> None:
    """A series keeps its own subject and its shaken shot."""
    assert placement_of(kind, seed) is None


def test_a_face_is_pasted_where_it_is_placed() -> None:
    """The pixels inside the placement change, those outside do not."""
    scene = Image.new("RGB", (800, 600), (0, 128, 0))
    paste_face(scene, Placement(Person.WOMAN, 200, 100, 300))
    assert scene.getpixel((350, 270)) != (0, 128, 0)
    assert scene.getpixel((50, 50)) == (0, 128, 0)


def test_the_person_rule_goes_above_existing_folders() -> None:
    """In the demo every photo lies in a folder: the rule must come before that one."""
    config = (
        '[[classify.rules]]\nname = "Existing folders"\nmatch = "existing_folder"\n'
    )
    changed = with_rule(config, '[[classify.rules]]\nname = "With Chloé"\n')
    assert changed.index("With Chloé") < changed.index("Existing folders")
    assert with_rule("", "rule\n") == "rule\n\n"
