"""The image's ffprobe and ffmpeg open every video extension analysed; its targets."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from media_hygiene.constants import VIDEO_EXTENSIONS

ROOT: Final = Path(__file__).resolve().parents[2]
DEMUXER_MAP: Final = re.compile(
    r"^# Demuxers per video extension: (?P<map>(?:.*\n#)*.*)$", re.MULTILINE
)
DEMUXERS: Final = re.compile(
    r"^ARG VIDEO_DEMUXERS=(?P<names>[a-z0-9,]+)$", re.MULTILINE
)
USES_THEM: Final = '--enable-demuxer="${VIDEO_DEMUXERS}"'
STAGES: Final = ("AS ffprobe", "AS ffmpeg")
LAST_STAGE: Final = re.compile(r"^FROM \S+ AS (?P<name>\S+)$", re.MULTILINE)
BUILD_STEP: Final = "uses: docker/build-push-action@"
NEXT_STEP: Final = "\n      - "


def test_every_video_extension_has_its_demuxer() -> None:
    """A new video extension needs its demuxer in the shared list and its comment."""
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    documented = DEMUXER_MAP.search(dockerfile)
    enabled = DEMUXERS.search(dockerfile)
    assert documented is not None
    assert enabled is not None
    words = set(re.findall(r"[a-z0-9]+", documented["map"]))
    assert {extension.lstrip(".") for extension in VIDEO_EXTENSIONS} <= words
    assert set(enabled["names"].split(",")) <= words


def test_both_tools_open_the_same_containers() -> None:
    """A video ffprobe checks, ffmpeg can fingerprint: one demuxer list."""
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert all(stage in dockerfile for stage in STAGES)
    assert dockerfile.count(USES_THEM) == len(STAGES)
    assert "--enable-demuxer=" not in dockerfile.replace(USES_THEM, "")


def test_a_plain_build_is_local_and_ci_publishes_published() -> None:
    """`docker build .` names itself; the pushed image is the `published` target."""
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert [match["name"] for match in LAST_STAGE.finditer(dockerfile)][-1] == "local"
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    steps = [part.split(NEXT_STEP, 1)[0] for part in workflow.split(BUILD_STEP)[1:]]
    pushing = [step for step in steps if "push=" in step]
    assert pushing
    assert all("target: published" in step for step in pushing)
