"""A failed file says why in plain words, never `[Errno 1] ... '/data/c/...'` (0162)."""

from __future__ import annotations

import errno
import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions.outcome import Incident, why
from media_hygiene.console.incidents_view import (
    GROUPED_FROM,
    SHOWN_FIRST,
    by_reason,
    show_failed,
    show_skipped,
)
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_CONTAINER: Final = "/data/c/measure/copies/002000-S3502056.JPG"
_PLAIN: Final = {
    errno.EPERM: "not allowed",
    errno.EACCES: "not allowed",
    errno.ENOSPC: "the disk is full",
    errno.EEXIST: "already there",
    errno.ENOENT: "no longer there",
    errno.EROFS: "read-only",
    errno.ENOTEMPTY: "not empty",
    errno.EBUSY: "another program",
    errno.EIO: "input/output",
}


@pytest.mark.parametrize(("code", "words"), list(_PLAIN.items()))
def test_each_error_is_said_in_plain_words(code: int, words: str) -> None:
    """The reason by error number: no path, no `[Errno n]`."""
    reason = why(OSError(code, os.strerror(code), _CONTAINER))
    assert words in reason
    assert "/data/" not in reason
    assert "[Errno" not in reason


def test_other_errors_keep_the_system_words_only() -> None:
    """An error nobody named: the system's text, still without number nor path."""
    code = errno.ENAMETOOLONG
    assert why(OSError(code, os.strerror(code), _CONTAINER)) == os.strerror(code)
    bare = OSError()
    bare.errno = code
    assert why(bare) == os.strerror(code)


def test_our_own_messages_pass_unchanged() -> None:
    """`OSError(_("..."))` and other errors carry their words already."""
    assert why(OSError("the copy differs from the original")) == (
        "the copy differs from the original"
    )
    assert why(ValueError("broken sidecar")) == "broken sidecar"


def test_the_reasons_are_translated() -> None:
    """French users read French reasons."""
    with using(Locale.FR):
        assert why(PermissionError(errno.EPERM, "x", _CONTAINER)).startswith(
            "non autorisé"
        )
        assert why(OSError(errno.ENOSPC, "x")) == "le disque est plein"


def _incidents(count: int, reason: str, folder: str = "copies") -> list[Incident]:
    """`count` files of one folder failing for one reason."""
    return [
        Incident(Path(f"/data/c/{folder}/{index}.jpg"), reason)
        for index in range(count)
    ]


def test_a_crowded_reason_is_said_once_for_the_rest(locations: Locations) -> None:
    """50 identical failures: a handful of lines, then how many more and why."""
    runtime = make_runtime(locations)
    reason = why(OSError(errno.EPERM, "Operation not permitted", _CONTAINER))
    show_failed(runtime, _incidents(50, reason))
    lines = output_of(runtime).splitlines()
    assert len(lines) == SHOWN_FIRST + 1
    assert "... and 45 more: not allowed" in lines[-1]
    assert "[Errno" not in output_of(runtime)


def test_a_few_failures_are_all_named(locations: Locations) -> None:
    """Up to `GROUPED_FROM` files per reason, each is named; reasons stay apart."""
    runtime = make_runtime(locations)
    incidents = _incidents(GROUPED_FROM, "the disk is full") + _incidents(
        2, "it is no longer there", "gone"
    )
    show_skipped(runtime, incidents)
    text = output_of(runtime)
    assert len(text.splitlines()) == GROUPED_FROM + 2
    assert "more" not in text
    assert list(by_reason(incidents)) == ["the disk is full", "it is no longer there"]


def test_a_path_with_brackets_is_shown_as_is(locations: Locations) -> None:
    """Rich markup in a file name is printed, not interpreted."""
    runtime = make_runtime(locations)
    show_failed(runtime, [Incident(Path("/data/c/[red]x.jpg"), "the disk is full")])
    assert "[red]x.jpg" in output_of(runtime)
