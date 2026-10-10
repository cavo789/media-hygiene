"""`file:///` addresses: Windows host paths only."""

from __future__ import annotations

from media_hygiene.paths.file_uri import file_uri


def test_windows_path() -> None:
    """Spaces and accents are encoded, backslashes become slashes."""
    assert file_uri(r"C:\Photos\Été 2015\a.mp4") == (
        "file:///C:/Photos/%C3%89t%C3%A9%202015/a.mp4"
    )


def test_container_path() -> None:
    """A path the host cannot open has no address."""
    assert file_uri("/data/c/Photos/a.mp4") is None
