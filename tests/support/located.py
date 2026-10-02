"""Photos with a GPS position, for the `place` and `trip` rules.

The personal places are fictitious points; the trips go to real, public towns.
"""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.engine import Classification, Scope, classify
from media_hygiene.classify.models import MediaInput
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import VisualFacts

if TYPE_CHECKING:
    from media_hygiene.classify.models import Proposal
    from media_hygiene.geo.gazetteer import Gazetteer

ROOT: Final = Path("/data/c/Photos")
HOME: Final = PersonalPlace(
    name="Home", latitude=50.3, longitude=5.1, radius_m=300, home=True
)
GRANDPA: Final = PersonalPlace(
    name="At grandpa's", latitude=50.4, longitude=5.3, radius_m=200
)
TURIN: Final = (45.0712, 7.6850)
MONCALIERI: Final = (44.9996, 7.6824)
MILAN: Final = (45.4643, 9.1895)
BRUGES: Final = (51.2089, 3.2242)
PLACE_RULE: Final = ClassifyRule(name="Places", match=RuleMatch.PLACE)
TRIP_RULE: Final = ClassifyRule(name="Trips", match=RuleMatch.TRIP)

type Where = tuple[float, float] | None


def located(name: str, when: datetime, where: Where) -> MediaInput:
    """A photo with an EXIF date and, maybe, a position.

    Args:
        name: Its file name, in `DCIM`.
        when: When it was taken.
        where: Latitude and longitude; None: no GPS.

    Returns:
        The photo.
    """
    taken = when.strftime("%Y:%m:%d %H:%M:%S")
    visual = VisualFacts(0, 0, 4000, 3000, 0.0, taken, "Phone")
    metadata = MediaMetadata(latitude=where[0], longitude=where[1]) if where else None
    return MediaInput(ROOT / "DCIM" / name, ROOT, 10, 0, visual, metadata)


def outing(prefix: str, start: datetime, where: tuple[Where, ...]) -> list[MediaInput]:
    """Photos one hour apart, one per position given.

    Args:
        prefix: Their names' start.
        start: When the first was taken.
        where: The position of each.

    Returns:
        The photos.
    """
    return [
        located(f"{prefix}{index}.jpg", start + timedelta(hours=index), spot)
        for index, spot in enumerate(where)
    ]


def run(
    files: list[MediaInput],
    rules: tuple[ClassifyRule, ...],
    towns: Gazetteer | None = None,
) -> dict[str, Proposal]:
    """Classify with these rules and the two places, proposals by file name.

    Args:
        files: The photos.
        rules: The rules.
        towns: The GeoNames towns.

    Returns:
        The proposals.
    """
    settings = ClassifySettings(rules=rules, places=(HOME, GRANDPA))
    found: Classification = classify(files, settings, Scope(towns=towns))
    return {proposal.file.path.name: proposal for proposal in found.proposals}


def start_of(day: int, hour: int = 9) -> datetime:
    """A day of July 2023.

    Args:
        day: Its number.
        hour: The hour.

    Returns:
        The date.
    """
    return datetime(2023, 7, day, hour)
