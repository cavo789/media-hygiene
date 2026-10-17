"""The folder pairs of the demo tree, and what `clean` does once two are decided."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

IPHONE: Final = ("C:\\Family Photos\\iPhone", "D:\\backup\\iPhone")
SUMMER: Final = ("C:\\Users\\Public\\Pictures\\Été 2019", "D:\\backup\\2019")


def clean_swapped_and_skipped(cli: CliRunner, data: Path) -> None:
    """Clean with IPHONE swapped and SUMMER left alone, check the files, undo.

    The backup's HEIC is kept, the summer copy of the backup too (its pair left
    alone); the backup's other copy goes (Vacances has the xmp). `undo` restores.

    Args:
        cli: The runner, the decisions in /reports/decisions.json.
        data: The data folder.
    """
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "pairs swapped: 1, pairs left alone: 1" in result.output
    assert (data / "d/backup/iPhone/IMG_4242.HEIC").is_file()
    assert not (data / "c/Family Photos/iPhone/IMG_4242.HEIC").exists()
    assert (data / "d/backup/2019/IMG_0002.jpg").is_file()
    assert not (data / "d/backup/2019/IMG_0001.jpg").exists()
    assert run(cli, "undo").exit_code == 0
    assert (data / "c/Family Photos/iPhone/IMG_4242.HEIC").is_file()
