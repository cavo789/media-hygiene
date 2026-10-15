"""`tags`: near duplicates share one description, as `review --near` decided."""

from __future__ import annotations

import json
import shutil
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from tests.integration.tags.test_tags_command import ASKED, PHOTOS, tags_of
from tests.support.cli import run
from tests.support.media import encode

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama

ORIGINAL = "c/Photos/DCIM/IMG_cake_4.jpg"
COPY = "c/Photos/WhatsApp/IMG-20230520-WA0001.jpg"
HOST_ORIGINAL = "C:\\Photos\\DCIM\\IMG_cake_4.jpg"
HOST_COPY = "C:\\Photos\\WhatsApp\\IMG-20230520-WA0001.jpg"


@pytest.fixture
def near(cli: CliRunner, locations: Locations) -> CliRunner:
    """The tags tree, one cake shot saved again smaller without EXIF, audited.

    Returns:
        The runner.
    """
    copy = locations.data_dir / COPY
    copy.parent.mkdir(parents=True)
    with Image.open(locations.data_dir / ORIGINAL) as picture:
        picture.resize((640, 480)).save(copy, "JPEG", quality=70)
    audited = run(cli, "audit")
    assert audited.exit_code == 0, audited.output
    return cli


def write_near_decision(locations: Locations, action: str) -> Path:
    """The decisions file `review --near` writes, the pair decided so."""
    keep = HOST_COPY if action == "swap" else ""
    group = {"kept": HOST_ORIGINAL, "copies": [HOST_COPY], "action": action}
    decisions = {"version": 1, "roots": ["C:\\"], "near": [group | {"keep": keep}]}
    target = locations.reports_dir / "decisions.json"
    target.write_text(json.dumps(decisions), encoding="utf-8")
    return target


def described_paths(locations: Locations) -> set[str]:
    """The paths whose own description the cache holds."""
    index = locations.cache_dir / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        return {row[0] for row in connection.execute("SELECT path FROM descriptions")}


def sent(locations: Locations) -> tuple[bool, bool]:
    """Whether the original and the copy were sent to the model."""
    paths = described_paths(locations)
    return (
        any(path.endswith(ORIGINAL) for path in paths),
        any(path.endswith(COPY) for path in paths),
    )


def test_a_near_pair_sends_the_version_kept(
    near: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """One picture of the pair is sent; the copy takes its words."""
    result = run(near, "--verbosity", "verbose", "tags")
    assert result.exit_code == 0, result.output
    assert fake.described() == ASKED
    assert sent(locations) == (True, False)
    assert tags_of(locations, COPY)["vision"] == tags_of(locations, ORIGINAL)["vision"]
    said = " ".join(result.output.split())
    assert "No decisions file of 'review --near'" in said
    assert f"{PHOTOS + 1} photos have the words of the vision model" in said


def test_a_pair_left_alone_sends_both(
    near: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """`leave`: each file is described on its own."""
    write_near_decision(locations, "leave")
    result = run(near, "tags")
    assert result.exit_code == 0, result.output
    assert fake.described() == ASKED + 1
    assert sent(locations) == (True, True)


def test_a_swapped_pair_sends_the_copy_kept(
    near: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """`swap`: the copy chosen answers for the pair, read from the archived file too."""
    target = write_near_decision(locations, "swap")
    target.rename(target.with_name("decisions.applied-20261015-101010.json"))
    result = run(near, "tags")
    assert result.exit_code == 0, result.output
    assert fake.described() == ASKED
    assert sent(locations) == (False, True)
    assert tags_of(locations, ORIGINAL)["vision"] == tags_of(locations, COPY)["vision"]


def test_planned_or_unreadable_decisions_share_one_description(
    near: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """`planned` keeps the audit's choice; a broken file is said, never fatal."""
    write_near_decision(locations, "planned")
    assert run(near, "tags", "--no-describe").exit_code == 0
    (locations.reports_dir / "decisions.json").write_text("{", encoding="utf-8")
    result = run(near, "--verbosity", "verbose", "tags")
    assert result.exit_code == 0, result.output
    assert fake.described() == ASKED
    said = " ".join(result.output.split())
    assert "is not a valid decisions file" in said
    assert "described through the version kept" in said


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is not installed")
def test_a_small_re_encoded_video_takes_the_words_of_its_original(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """The original is sent by one frame; its copy, too small to be sent, inherits."""
    videos = locations.data_dir / "c" / "Videos"
    original = videos / "Zoom.mp4"
    lavfi = ("-f", "lavfi", "-i", "mandelbrot=size=640x480:rate=15", "-t", "3")
    encode(original, *lavfi, "-pix_fmt", "yuv420p")
    copy = ("-vf", "scale=320:240", "-r", "10", "-map_metadata", "-1")
    encode(videos / "Zoom-WA.mp4", "-i", str(original), *copy)
    assert run(cli, "audit").exit_code == 0
    result = run(cli, "tags", "--yes")
    assert result.exit_code == 0, result.output
    assert fake.described() == ASKED + 1
    words = tags_of(locations, "Videos/Zoom.mp4")["vision"]
    assert tags_of(locations, "Videos/Zoom-WA.mp4")["vision"] == words
