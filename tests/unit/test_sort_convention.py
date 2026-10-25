"""The sort convention `YYYY/YYYY-MM/<event>`: defaults, guesses (0401, 0402)."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.classify.convention import Place, shape_of
from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.layout import render
from media_hygiene.classify.models import Band, MediaInput, SortReason
from media_hygiene.classify.rules.kinds import FileKind, RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.scan.models import VisualFacts
from media_hygiene.search.rule_models import PeriodRuleIn
from media_hygiene.services.config_convention import layout_changes, write_convention
from tests.unit.test_classify_engine import ROOT, by_name, series

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

SETTINGS = ClassifySettings()
_SIDE = 4000  # a photo, not a tiny image (those count as screenshots)


def photo(
    relative: str, when: datetime | None, camera: str | None = "Pixel"
) -> MediaInput:
    """A photo of a real size, with an EXIF date (none: only its name or mtime)."""
    taken = when.strftime("%Y:%m:%d %H:%M:%S") if when else None
    visual = VisualFacts(0, 0, _SIDE, _SIDE * 3 // 4, 0.0, taken, camera)
    return MediaInput(ROOT / relative, ROOT, 10, 0, visual)


def folders_of(
    files: Sequence[MediaInput], settings: ClassifySettings = SETTINGS
) -> dict[str, str | None]:
    """The proposed folder of each file, by name."""
    return {
        name: p.folder
        for name, p in by_name(classify(files, settings, Scope()).proposals).items()
    }


def test_the_default_layout_is_year_then_month_then_event() -> None:
    """A named event goes to `2009/2009-11/<name>`; a trip keeps its stage below."""
    assert SETTINGS.layout == "{year}/{year_month}/{category}"
    named = series("Anniversaire de Tom", datetime(2009, 11, 28, 14), 3)
    assert set(folders_of(named).values()) == {"2009/2009-11/Anniversaire de Tom"}
    stage = [photo("2019/2019-07/Montenegro/Budva/a.jpg", datetime(2019, 7, 3, 10))]
    (proposal,) = classify(stage, SETTINGS, Scope()).proposals
    assert proposal.in_place
    assert proposal.category == "Montenegro/Budva"


def test_year_and_year_month_folders_are_dates_only() -> None:
    """`2009`, `2009-11`, `1985-00` mean nothing; `2009/2009-11/X` means `X`."""
    rules = FolderRules.build((), ((), ()))
    for name in ("2009", "2009-11", "1985-00"):
        assert rules.label(name) is None
    assert rules.meaning(ROOT / "2009/2009-11/Anniversaire de Tom", ROOT) == (
        "Anniversaire de Tom",
    )


@pytest.mark.parametrize(
    ("parts", "place", "month"),
    [
        (("2009", "2009-11", "Anniversaire de Tom"), Place.EVENT, 11),
        (("2019", "2019-07", "Montenegro", "Budva"), Place.EVENT, 7),
        (("2009", "2009-11"), Place.NOTHING_SPECIAL, 11),
        (("1985", "1985-00"), Place.NOTHING_SPECIAL, 0),
        (("2009", "2010-01", "X"), Place.LEFT, 0),  # the month of another year
        (("2009", "Novembre 2009"), Place.LEFT, 0),
        (("Photos Chloé",), Place.LEFT, 0),
        ((), Place.LEFT, 0),
    ],
)
def test_the_shape_of_a_path(parts: tuple[str, ...], place: Place, month: int) -> None:
    """Sorted, nothing special, or left: from the folders alone."""
    shape = shape_of(parts)
    assert (shape.place, shape.month) == (place, month)


def test_the_tool_writes_no_word_of_its_own() -> None:
    """A guess, an unknown or an undated file stays where it is."""
    assert (SETTINGS.unsure_layout, SETTINGS.manual_layout) == ("", "")
    assert (SETTINGS.undated_layout, SETTINGS.received_layout) == ("", "")
    loose = series("DCIM", datetime(2016, 7, 14, 18), 6)
    undated = photo("DCIM/old.jpg", None, camera=None)
    for proposal in classify([*loose, undated], SETTINGS, Scope()).proposals:
        assert proposal.band is not Band.SURE
        assert proposal.folder is None
        assert proposal.in_place


def test_a_guess_stays_and_carries_where_it_would_go() -> None:
    """A loose file joining a named folder is a guess: it stays, its values ready."""
    start = datetime(2018, 3, 12, 14)
    named = series("Anniversaire Léa", start, 3)
    loose = [
        photo(f"DCIM/{i}.jpg", start + timedelta(minutes=30 * i + 5)) for i in range(3)
    ]
    found = by_name(classify([*named, *loose], SETTINGS, Scope()).proposals)
    guess = found["1.jpg"]
    assert (guess.band, guess.folder) == (Band.UNSURE, None)
    assert guess.values is not None
    assert render(SETTINGS.layout, guess.values) == "2018/2018-03/Anniversaire Léa"


def test_a_file_directly_in_its_month_folder_stays_there() -> None:
    """Nothing special that month, even beside a named folder of an event then."""
    start = datetime(2009, 11, 28, 14)
    named = series("2009/2009-11/Anniversaire de Tom", start, 3)
    plain = photo("2009/2009-11/x.jpg", start + timedelta(minutes=20))
    elsewhere = photo("2009/2009-11/y.jpg", datetime(2010, 2, 1, 10))  # wrong month
    found = by_name(classify([*named, plain, elsewhere], SETTINGS, Scope()).proposals)
    assert (found["x.jpg"].band, found["x.jpg"].reason) == (
        Band.STAY,
        SortReason.NOTHING_SPECIAL,
    )
    assert found["x.jpg"].in_place
    assert found["y.jpg"].reason is not SortReason.NOTHING_SPECIAL


def test_a_received_picture_joins_the_nearest_event_as_a_guess() -> None:
    """`IMG-20091128-WA0001.jpg`, received the day of the party: its folder, a guess."""
    party = series("Anniversaire de Tom", datetime(2009, 11, 28, 14), 5)
    received = photo("WhatsApp Images/IMG-20091128-WA0001.jpg", None, camera=None)
    found = by_name(classify([*party, received], SETTINGS, Scope()).proposals)
    joined = found["IMG-20091128-WA0001.jpg"]
    assert joined.band is Band.UNSURE
    assert joined.event_id == found["0.jpg"].event_id
    assert joined.values is not None
    assert render(SETTINGS.layout, joined.values) == "2009/2009-11/Anniversaire de Tom"


def test_a_received_picture_far_from_any_event_is_a_guess_of_its_month() -> None:
    """No event within `merge_gap_hours`: its month, never sure."""
    party = series("Anniversaire de Tom", datetime(2009, 11, 28, 14), 5)
    received = photo("WhatsApp Images/IMG-20091215-WA0001.jpg", None, camera=None)
    found = by_name(classify([*party, received], SETTINGS, Scope()).proposals)
    alone = found["IMG-20091215-WA0001.jpg"]
    assert alone.band is not Band.SURE
    assert alone.event_id == ""
    assert alone.values is not None
    assert (alone.values.year, alone.values.month) == (2009, 12)


def test_a_kind_rule_with_its_own_layout_needs_no_year() -> None:
    """Screenshots gathered in a folder of the user's, by year inside it."""
    rule = ClassifyRule(
        name="Screens",
        match=RuleMatch.KIND,
        kind=FileKind.SCREENSHOT,
        category="Documents",
        layout="{category}/{year}",
    )
    settings = ClassifySettings(rules=(rule,))
    screen = photo(
        "DCIM/Screenshot_20190301-101010.png", datetime(2019, 3, 1, 10), camera=None
    )
    assert folders_of([screen], settings) == {screen.path.name: "Documents/2019"}
    default = folders_of([screen])  # the default rule: no category, it stays
    assert default == {screen.path.name: None}


def test_the_default_rules_give_one_name() -> None:
    """No category of several levels among the defaults."""
    assert all("/" not in rule.category for rule in SETTINGS.rules)


def test_the_rule_dialog_asks_a_name_not_a_path() -> None:
    r"""A `/` or a `\` in the folder of a rule typed on a page is refused."""
    base = {"name": "Tom", "first": "2009-11-28", "last": "2009-11-28"}
    named = PeriodRuleIn.model_validate({**base, "category": "Anniversaire de Tom"})
    assert named.category == "Anniversaire de Tom"
    for path in ("Fêtes/Anniversaires", "Fêtes\\Anniversaires"):
        with pytest.raises(ValidationError, match="one name"):
            PeriodRuleIn.model_validate({**base, "category": path})


def test_config_convention_lists_asks_then_writes_keeping_comments(
    tmp_path: Path,
) -> None:
    """Old → new for each layout that differs; comments kept; read back."""
    config = tmp_path / "config.toml"
    config.write_text(
        '# mine\n[classify]\n# where\nlayout = "{year}/{category}"\n'
        'unsure_layout = "{year}/To check/{category}"\nmanual_layout = ""\n',
        encoding="utf-8",
    )
    changes = layout_changes(config)
    assert [(c.key, c.old, c.new) for c in changes] == [
        ("layout", "{year}/{category}", "{year}/{year_month}/{category}"),
        ("unsure_layout", "{year}/To check/{category}", ""),
    ]
    assert write_convention(config) == changes
    text = config.read_text(encoding="utf-8")
    assert "# mine" in text
    assert "# where" in text
    assert not layout_changes(config)
    assert not layout_changes(tmp_path / "missing.toml")
