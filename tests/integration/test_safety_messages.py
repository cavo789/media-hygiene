"""At the moment of use, one line says what happens to the files, and how to undo it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typer.testing import CliRunner

from media_hygiene.paths.mount_kind import MountKind
from tests.support.cli import run
from tests.support.media import MediaFactory

if TYPE_CHECKING:
    import pytest

    from media_hygiene.paths.locations import Locations


def flat(text: str) -> str:
    """The output on one line: Rich wraps long lines."""
    return " ".join(text.split())


def test_clean_says_nothing_is_erased_and_how_to_free_and_undo(cli: CliRunner) -> None:
    """Default clean: moved, never erased; `purge` frees, `undo` brings back."""
    cleaned = flat(run(cli, "clean", "--yes").output)
    assert "🛟 Nothing will be erased: each copy is first compared byte for byte" in (
        cleaned
    )
    assert "once you have checked, 'purge' frees the space" in cleaned
    assert "'media-hygiene undo " in cleaned
    assert cleaned.index("'media-hygiene undo ") < cleaned.index("👉 What next")
    undone = flat(run(cli, "undo", "--yes").output)
    assert "🛟 Each file comes back where it was, never over another one" in undone


def test_delete_and_purge_say_plainly_that_they_erase(cli: CliRunner) -> None:
    """`clean --delete` and `purge`: the only two ways content goes, said so."""
    deleted = flat(run(cli, "clean", "--delete", "--yes").output)
    assert "--delete: the copies are deleted for good, after a byte comparison" in (
        deleted
    )
    purged = run(cli, "purge", "--yes")
    assert purged.exit_code == 0, purged.output
    text = flat(purged.output)
    assert "'purge' erases for good: these files cannot come back" in text
    assert "'undo' can no longer restore these files." in text


def test_an_audit_without_copies_does_not_offer_to_set_copies_aside(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken file alone: no "set 0 of copies aside", no Czkawka, no --prefer."""
    for kind in MountKind:
        monkeypatch.setenv(
            f"MEDIA_HYGIENE_{kind.value.upper()}_DIR", str(locations.path_of(kind))
        )
    MediaFactory(locations.data_dir).empty("c/Photos/IMG_1.jpg")
    audited = flat(run(CliRunner(), "audit").output)
    assert "Broken files" in audited
    for advice in ("of copies aside", "Second opinion", "--prefer"):
        assert advice not in audited
