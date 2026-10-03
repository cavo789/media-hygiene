"""At the moment of use, one line says what happens to the files, and how to undo it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.support.cli import run

if TYPE_CHECKING:
    from typer.testing import CliRunner


def flat(text: str) -> str:
    """The output on one line: Rich wraps long lines."""
    return " ".join(text.split())


def test_clean_says_nothing_is_erased_and_how_to_free_and_undo(cli: CliRunner) -> None:
    """Default clean: moved, never erased; `purge` frees, `undo` brings back."""
    cleaned = flat(run(cli, "clean", "--yes").output)
    assert "🛟 Nothing is erased: each copy is compared byte for byte" in cleaned
    assert "The space is freed by 'purge', once you have checked" in cleaned
    assert "'media-hygiene undo " in cleaned
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
