"""`classify` after `tags`: what the model saw for the words is not asked again."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from tests.support.cli import run
from tests.support.subjects import CATEGORIES

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama

PHOTOS = 15  # three events of five shots, none a burst


def test_classify_maps_the_answers_of_tags(cli: CliRunner, fake: FakeOllama) -> None:
    """`tags` sends each photo once; `classify` only maps, with the same subjects."""
    assert run(cli, "audit").exit_code == 0
    tagged = run(cli, "tags", "--yes")
    assert tagged.exit_code == 0, tagged.output
    assert fake.described() == PHOTOS
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert fake.described() == PHOTOS  # not one photo sent again
    assert fake.mapped() > 0
    assert "Sure │    15" in result.output
    for category in CATEGORIES:
        assert re.search(rf"{category}\s+│\s+5 ", result.output)


def test_the_tags_of_another_model_are_not_its_answer(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """Another `[classify.ai] model` than the one of `tags`: described again."""
    assert run(cli, "audit").exit_code == 0
    assert run(cli, "tags", "--yes").exit_code == 0
    text = (locations.config_dir / "config.toml").read_text(encoding="utf-8")
    changed = text.replace('model = "vision"', 'model = "vision2"')
    (locations.config_dir / "config.toml").write_text(changed, encoding="utf-8")
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert fake.described() == PHOTOS + 9  # three samples per event, asked anew
