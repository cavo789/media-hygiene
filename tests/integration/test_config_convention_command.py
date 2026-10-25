"""`config --convention`: old → new, a question, then the file read back."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.output import Output
from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_OLD = (
    '# mine\n[classify]\nlayout = "{year}/{category}"\n'
    'manual_layout = "{year}/To sort/{event}"\n'
)


def test_listed_refused_without_a_yes_then_written(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--dry-run` lists; no yes, nothing written; yes: written, comments kept."""
    locations.config_file.write_text(_OLD, encoding="utf-8")
    listed = run(cli, "config", "--convention", "--dry-run")
    assert listed.exit_code == 0, listed.output
    shown = " ".join(listed.output.split())
    assert "layout: '{year}/{category}' → {year}/{year_month}/{category}" in shown
    assert "manual_layout" in shown
    refused = run(cli, "config", "--convention")  # no terminal: no yes
    assert "Nothing written" in " ".join(refused.output.split())
    assert locations.config_file.read_text(encoding="utf-8") == _OLD
    monkeypatch.setattr(Output, "confirm", lambda _self, _question: True)
    done = run(cli, "config", "--convention")
    assert done.exit_code == 0, done.output
    assert "2 layouts written to" in " ".join(done.output.split())
    text = locations.config_file.read_text(encoding="utf-8")
    assert "# mine" in text
    assert 'layout = "{year}/{year_month}/{category}"' in text
    again = run(cli, "config", "--convention")
    assert "follow the sort convention" in " ".join(again.output.split())


def test_classify_offers_it_and_names_a_rule_of_several_levels(
    cli: CliRunner, locations: Locations
) -> None:
    """One tip with the command; one line per rule whose category is a path."""
    rules = (
        '\n[[classify.rules]]\nname = "Fêtes"\nmatch = "calendar"\n'
        'dates = "12-24..12-26"\ncategory = "Parties/Christmas"\n'
    )
    locations.config_file.write_text(_OLD + rules, encoding="utf-8")
    shown = " ".join(run(cli, "classify").output.split())
    assert "config --convention" in shown
    assert "The rule 'Fêtes' gives the category 'Parties/Christmas'" in shown
