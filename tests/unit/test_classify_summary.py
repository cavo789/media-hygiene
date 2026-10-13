"""The console summary of `classify`: named reasons, titled categories, `--year`."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime
from io import StringIO
from pathlib import Path

from rich.console import Console

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import DateSource, MediaInput, SortReason
from media_hygiene.classify.names import reason_name
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.console.classify_view import show_classification
from media_hygiene.console.output import Output
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.scan.models import VisualFacts
from media_hygiene.services.classify import ClassifyResult

ROOT = Path("/data/c/Photos")
NS = 1_000_000_000
SETTINGS = ClassifySettings(
    rules=(
        ClassifyRule(
            name="Drone", match=RuleMatch.CAMERA, pattern="DJI", category="Air"
        ),
        ClassifyRule(
            name="Italy", match=RuleMatch.DATE_RANGE, dates="2023-07-01..2023-07-15"
        ),
    )
)


def _shot(name: str, camera: str, mtime: int = 0) -> MediaInput:
    """A photo of June 2019 (its EXIF date), or one only the disk dates."""
    taken = "2019:06:02 10:00:00" if camera else None
    visual = VisualFacts(0, 0, 4000, 3000, 0.0, taken, camera or None)
    return MediaInput(ROOT / name, ROOT, 10, mtime, visual)


def _files() -> list[MediaInput]:
    """A drone shot and a phone shot of 2019, and a copy only the disk dates (2019)."""
    mtime = int(datetime(2019, 6, 3, 12).timestamp()) * NS  # the disk's date only
    return [
        _shot("a.jpg", "DJI FC3170"),
        _shot("b.jpg", "Pixel"),
        _shot("c.jpg", "", mtime),
    ]


def _summary(years: tuple[int, int] | None) -> str:
    """The console summary of a run, on one line."""
    result = ClassifyResult(classify(_files(), SETTINGS, Scope(years=years)), 0)
    buffer = StringIO()
    show_classification(Output(Console(file=buffer, width=200)), result)
    return " ".join(buffer.getvalue().split())


def test_every_reason_has_a_name_in_both_languages() -> None:
    """No raw code reaches the console: each reason is named, and translated."""
    english = {reason: reason_name(reason) for reason in SortReason}
    assert len(set(english.values())) == len(SortReason)
    assert all(name != reason.value for reason, name in english.items())
    with using(Locale.FR):
        french = {reason: reason_name(reason) for reason in SortReason}
    assert all(french[reason] != english[reason] for reason in SortReason)


def test_the_categories_sit_under_their_own_title() -> None:
    """The reasons first, then the largest categories, apart."""
    text = _summary(None)
    assert text.index("Why") < text.index("Largest categories") < text.index("Air")


def test_without_year_the_unused_rules_are_named() -> None:
    """The list and its tip, as before; the disk-dated copy is proposed."""
    text = _summary(None)
    assert "Rules that decided nothing: Italy." in text
    assert "Undated" in text


def test_under_year_one_line_counts_unused_rules_and_disk_dated_files() -> None:
    """`--year`: no names, no tip; the disk-dated copy is left out and counted."""
    year = _year_of_copy()
    text = _summary((year, year))
    assert "Drone" in text  # the 2019 shots are still proposed
    assert "Rules that decided nothing" not in text
    assert "rule decided nothing in" in text or "rules decided nothing in" in text
    assert "1 file dated only by the disk left out" in text


def test_under_year_no_file_dated_by_the_disk_is_proposed() -> None:
    """The copy dated by its modification date gets no proposal."""
    year = _year_of_copy()
    found = classify(_files(), SETTINGS, Scope(years=(year, year)))
    assert all(
        p.dating and p.dating.source is not DateSource.MTIME for p in found.proposals
    )
    assert found.years == ((year, year), 1)


def _year_of_copy() -> int:
    """The year the disk gives the copy."""
    found = classify(_files(), SETTINGS, Scope())
    copy = next(p for p in found.proposals if p.file.path.name == "c.jpg")
    assert copy.dating is not None
    assert copy.dating.source is DateSource.MTIME
    return copy.dating.when.year
