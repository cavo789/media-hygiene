"""`media-hygiene config --upgrade` from the command line: offered, listed, done."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from media_hygiene.config.loader import default_config
from media_hygiene.constants import Locale
from tests.support.cli import run

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_offered_listed_then_added(cli: CliRunner, locations: Locations) -> None:
    """`config` offers it; `--dry-run` lists; `--upgrade` adds, then up to date."""
    old = re.sub(
        r"\n\[tags\]\n.*?(?=\n\[people\])",
        "\n",
        default_config(Locale.EN),
        flags=re.DOTALL,
    )
    old = re.sub(
        r"# media-hygiene-config: .*\n", "# media-hygiene-config: 0.1.0\n", old
    )
    locations.config_file.write_text(old, encoding="utf-8")
    shown = " ".join(run(cli, "config").output.split())
    assert "config.toml was written by 0.1.0: 1 new setting since." in shown
    assert "'config --upgrade' adds them" in shown
    listed = run(cli, "config", "--dry-run")
    assert listed.exit_code == 0, listed.output
    assert "+ tags" in listed.output
    assert locations.config_file.read_text(encoding="utf-8") == old
    done = run(cli, "config", "--upgrade")
    assert done.exit_code == 0, done.output
    assert "1 setting added to" in " ".join(done.output.split())
    assert "[tags]" in locations.config_file.read_text(encoding="utf-8")
    again = run(cli, "config", "--upgrade")
    assert "is up to date" in " ".join(again.output.split())
    assert "new setting since" not in run(cli, "config").output


def test_without_a_file_it_says_how_to_get_one(
    cli: CliRunner, locations: Locations
) -> None:
    """A fresh run creates a complete file: nothing to add, never a traceback."""
    first = run(cli, "config", "--upgrade")
    assert first.exit_code == 0, first.output
    assert "Traceback" not in first.output
    assert locations.config_file.is_file()
