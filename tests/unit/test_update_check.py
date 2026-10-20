"""A newer version: Docker Hub asked once a day at most, every failure silent (0267)."""

from __future__ import annotations

import json
import urllib.error
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.paths.docker_run import IMAGE_VARIABLE
from media_hygiene.services.update_check import (
    CHECK_FILE_NAME,
    RELEASES_URL,
    TAGS_URL,
    newer_version,
)
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_RUNNING: Final = "0.4.0"


class Hub:
    """A stand-in for Docker Hub: its answer, and how many times it was asked."""

    def __init__(self, answer: bytes | Exception) -> None:
        """Answer `answer`, or raise it."""
        self.answer = answer
        self.asked: list[str] = []

    def __call__(self, url: str) -> bytes:
        """Answer one request."""
        self.asked.append(url)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def tags(*names: str) -> bytes:
    """An answer of Docker Hub listing these tags, the newest first."""
    results = [
        {"name": name, "digest": f"sha256:{index}"} for index, name in enumerate(names)
    ]
    return json.dumps({"count": len(names), "results": results}).encode()


@pytest.fixture(autouse=True)
def published(monkeypatch: pytest.MonkeyPatch) -> None:
    """The published image, version 0.4.0."""
    monkeypatch.delenv(IMAGE_VARIABLE, raising=False)
    monkeypatch.setattr(
        "media_hygiene.services.update_check.version", lambda _name: _RUNNING
    )


def _runtime(tmp_path: Path, *, check: bool = True) -> Runtime:
    """A runtime whose `/cache` is in `tmp_path`."""
    runtime = make_runtime(
        make_locations(tmp_path), {"general": {"check_updates": check}}
    )
    runtime.locations.cache_dir.mkdir(parents=True, exist_ok=True)
    return runtime


def test_a_newer_tag_gives_the_banner(tmp_path: Path) -> None:
    """0.5.0 published: the banner's version and the release notes."""
    hub = Hub(tags("latest", "0.5.0", "0.4.0"))
    notice = newer_version(_runtime(tmp_path), hub)
    assert notice is not None
    assert (notice.version, notice.notes) == ("0.5.0", RELEASES_URL)
    assert hub.asked == [TAGS_URL]
    assert "/namespaces/cavo789/repositories/media-hygiene/tags" in TAGS_URL


def test_the_same_version_gives_nothing(tmp_path: Path) -> None:
    """The newest published is the one running."""
    assert newer_version(_runtime(tmp_path), Hub(tags("latest", "0.4.0"))) is None


def test_the_highest_version_wins_whatever_the_order(tmp_path: Path) -> None:
    """0.10.0 is newer than 0.9.0: numbers, not text."""
    notice = newer_version(_runtime(tmp_path), Hub(tags("0.9.0", "0.10.0", "0.4.1")))
    assert notice is not None
    assert notice.version == "0.10.0"


@pytest.mark.parametrize(
    "answer",
    [
        urllib.error.URLError("offline"),
        TimeoutError("timed out"),
        urllib.error.HTTPError(TAGS_URL, 429, "Too Many Requests", None, None),  # type: ignore[arg-type]
        b"<html>not json</html>",
        b'{"results": "nope"}',
        b"[1, 2]",
    ],
    ids=["offline", "timeout", "429", "not json", "no list", "not an object"],
)
def test_every_failure_is_silent(tmp_path: Path, answer: bytes | Exception) -> None:
    """Nothing shown, no exception, and the next try waits for the next day."""
    runtime = _runtime(tmp_path)
    hub = Hub(answer)
    assert newer_version(runtime, hub) is None
    assert newer_version(runtime, hub) is None
    assert len(hub.asked) == 1


@pytest.mark.parametrize(
    "names", [("latest",), ("0.5",), ("v0.5.0",), ("0.5.0-rc1",), ()]
)
def test_only_x_y_z_is_taken_for_a_version(
    tmp_path: Path, names: tuple[str, ...]
) -> None:
    """`latest`, a version without its patch number or a suffix: never the newest."""
    assert newer_version(_runtime(tmp_path), Hub(tags(*names))) is None


def test_an_answer_under_a_day_old_is_not_asked_again(tmp_path: Path) -> None:
    """The first call asks; the second reads `/cache`."""
    runtime = _runtime(tmp_path)
    hub = Hub(tags("0.5.0"))
    first = newer_version(runtime, hub)
    second = newer_version(runtime, Hub(OSError("must not be asked")))
    assert first == second
    assert len(hub.asked) == 1
    kept = json.loads(
        (runtime.locations.cache_dir / CHECK_FILE_NAME).read_text("utf-8")
    )
    assert kept["latest"] == "0.5.0"


def test_an_answer_a_day_old_is_asked_again(tmp_path: Path) -> None:
    """Yesterday's answer: Docker Hub is asked once more."""
    runtime = _runtime(tmp_path)
    old = datetime.now(UTC) - timedelta(days=1, minutes=1)
    (runtime.locations.cache_dir / CHECK_FILE_NAME).write_text(
        json.dumps({"checked_at": old.isoformat(), "latest": "0.4.0"}), "utf-8"
    )
    hub = Hub(tags("0.6.0"))
    notice = newer_version(runtime, hub)
    assert notice is not None
    assert notice.version == "0.6.0"
    assert len(hub.asked) == 1


@pytest.mark.parametrize("kept", ["{broken", '{"checked_at": "never"}'])
def test_an_unreadable_cache_file_is_asked_again(tmp_path: Path, kept: str) -> None:
    """A damaged file is not trusted, and never raises."""
    runtime = _runtime(tmp_path)
    (runtime.locations.cache_dir / CHECK_FILE_NAME).write_text(kept, "utf-8")
    hub = Hub(tags("0.5.0"))
    assert newer_version(runtime, hub) is not None
    assert len(hub.asked) == 1


def test_a_read_only_cache_still_answers(tmp_path: Path) -> None:
    """`/cache` cannot be written: the answer is given, nothing raises."""
    runtime = _runtime(tmp_path)
    cache = runtime.locations.cache_dir
    cache.chmod(0o500)
    try:
        assert newer_version(runtime, Hub(tags("0.5.0"))) is not None
        assert not (cache / CHECK_FILE_NAME).exists()
    finally:
        cache.chmod(0o700)


@pytest.mark.parametrize(
    "prepare",
    [
        lambda _mp, tmp: _runtime(tmp, check=False),
        lambda mp, tmp: (mp.setenv(IMAGE_VARIABLE, "media-hygiene"), _runtime(tmp))[1],
    ],
    ids=["check_updates = false", "a local build"],
)
def test_no_request_when_turned_off_or_built_locally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prepare: Callable[[pytest.MonkeyPatch, Path], Runtime],
) -> None:
    """The setting turned off, or a local build: Docker Hub is never asked."""
    runtime = prepare(monkeypatch, tmp_path)
    hub = Hub(tags("9.9.9"))
    assert newer_version(runtime, hub) is None
    assert not hub.asked
