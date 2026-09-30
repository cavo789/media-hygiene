"""The ordered rules: dates, paths, cameras, kinds, order, scores, unused rules."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path, PureWindowsPath

from media_hygiene.classify.engine import Classification, Scope, classify
from media_hygiene.classify.models import Band, MediaInput, Proposal, SortReason
from media_hygiene.classify.rules.kinds import FileKind, RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.scan.models import VisualFacts

ROOT = Path("/data/c/Photos")
ITALY = ClassifyRule(
    name="Italy",
    match=RuleMatch.DATE_RANGE,
    dates="2023-07-01..2023-07-15",
    category="Holidays/Italy {year}",
)
FAIR = ClassifyRule(
    name="Fair", match=RuleMatch.PATH, pattern=r"(?i)\\kermesse", category="School"
)
DRONE = ClassifyRule(
    name="Drone", match=RuleMatch.CAMERA, pattern="(?i)dji", category="Drone"
)


def shot(
    relative: str, when: datetime | None, camera: str | None = "Pixel"
) -> MediaInput:
    """A 4000x3000 photo with an EXIF date (none: only its mtime)."""
    taken = when.strftime("%Y:%m:%d %H:%M:%S") if when else None
    visual = VisualFacts(0, 0, 4000, 3000, 0.0, taken, camera)
    return MediaInput(ROOT / relative, ROOT, 10, 0, visual)


def series(folder: str, start: datetime, count: int) -> list[MediaInput]:
    """`count` photos in `folder`, one hour apart."""
    return [
        shot(f"{folder}/{index}.jpg", start + timedelta(hours=index))
        for index in range(count)
    ]


def run(files: list[MediaInput], *rules: ClassifyRule) -> Classification:
    """Classify with these rules only, host paths as Windows writes them."""
    settings = ClassifySettings(rules=rules)
    host = Scope(host=lambda path: str(PureWindowsPath("C:/", *path.parts[3:])))
    return classify(files, settings, host)


def by_name(classification: Classification) -> dict[str, Proposal]:
    """Proposals by file name."""
    return {p.file.path.name: p for p in classification.proposals}


def test_a_date_range_takes_the_whole_trip_and_is_sure() -> None:
    """The trip ends on the 16th at night: still one event, all of it in Italy."""
    trip = series("DCIM", datetime(2023, 7, 15, 20), 6)
    found = by_name(run(trip, ITALY))
    assert {p.folder for p in found.values()} == {"2023/Holidays/Italy 2023"}
    first = found["0.jpg"]
    assert (first.band, first.reason, first.rule) == (
        Band.SURE,
        SortReason.DATE_RANGE,
        "Italy",
    )


def test_a_calendar_day_does_not_swallow_a_long_event() -> None:
    """A birthday inside a week of skiing: the week stays whole, not a birthday."""
    birthday = ClassifyRule(
        name="Birthday", match=RuleMatch.CALENDAR, dates="03-12", category="Parties"
    )
    week = [
        shot(f"DCIM/{day}-{hour}.jpg", datetime(2018, 3, day, hour))
        for day in range(10, 17)
        for hour in range(0, 24, 6)
    ]
    alone = shot("DCIM/alone.jpg", datetime(2019, 3, 12, 10))
    found = by_name(run([*week, alone], birthday))
    assert found["12-0.jpg"].reason is SortReason.NO_SIGNAL
    assert (found["alone.jpg"].folder, found["alone.jpg"].rule) == (
        "2019/Parties",
        "Birthday",
    )


def test_path_and_camera_rules() -> None:
    """A regular expression on the host path; another on the make and model."""
    files = [
        shot("Ecole/Kermesse/a.jpg", datetime(2019, 6, 1)),
        shot("DCIM/b.jpg", datetime(2019, 6, 2), camera="DJI FC3170"),
        shot("DCIM/c.jpg", datetime(2019, 6, 3)),
    ]
    found = by_name(run(files, FAIR, DRONE))
    assert (found["a.jpg"].folder, found["a.jpg"].reason) == (
        "2019/School",
        SortReason.PATH,
    )
    assert found["b.jpg"].folder == "2019/Drone"
    assert found["c.jpg"].reason is SortReason.NO_SIGNAL


def test_each_kind_is_told_from_its_name_and_metadata() -> None:
    """Screenshots, received pictures and downloads; ordinary shots are none."""
    rules = [
        ClassifyRule(name=kind.value, match=RuleMatch.KIND, kind=kind, category="K")
        for kind in FileKind
    ]
    when = datetime(2020, 1, 5)
    icon = MediaInput(
        ROOT / "x/icon.jpg",
        ROOT,
        1,
        0,
        VisualFacts(0, 0, 64, 64, 0.0, "2020:01:05 10:00:00", None),
    )
    files = [
        shot("x/Screenshot_20200105-101010.jpg", when),
        shot("x/export.png", when, camera=None),
        icon,
        shot("x/IMG-20200105-WA0003.jpg", None, camera=None),
        shot("x/Show.S01E05.1080p.x264.mkv", when, camera=None),
        shot("x/IMG_1234.jpg", when),
        shot("x/Holiday 1080p.jpg", when, camera=None),
    ]
    found = by_name(run(files, *rules))
    assert found["Screenshot_20200105-101010.jpg"].rule == "screenshot"
    assert found["export.png"].rule == "screenshot"
    assert found["icon.jpg"].rule == "screenshot"
    assert found["IMG-20200105-WA0003.jpg"].rule == "received"
    assert found["Show.S01E05.1080p.x264.mkv"].rule == "download"
    assert found["IMG_1234.jpg"].rule == ""
    assert found["Holiday 1080p.jpg"].rule == ""  # a large JPEG, not a video


def test_a_rule_without_category_leaves_its_files_where_they_are() -> None:
    """The default list leaves downloaded films alone, even undated ones."""
    film = shot("Films/Movie.2019.1080p.WEB-DL.mp4", None, camera=None)
    (proposal,) = classify([film], ClassifySettings(), Scope()).proposals
    assert (proposal.band, proposal.rule, proposal.folder) == (
        Band.STAY,
        "Films and series",
        None,
    )
    assert proposal.in_place


def test_the_first_sure_rule_wins_and_order_matters() -> None:
    """A folder named by the user, then a date range: the first listed decides."""
    files = series("Vacances Toscane", datetime(2023, 7, 2, 10), 5)
    folders = ClassifyRule(name="Folders", match=RuleMatch.EXISTING_FOLDER)
    first = by_name(run(files, folders, ITALY))["0.jpg"]
    assert (first.rule, first.category) == ("Folders", "Vacances Toscane")
    then = by_name(run(files, ITALY, folders))["0.jpg"]
    assert (then.rule, then.category) == ("Italy", "Holidays/Italy 2023")


def test_a_rule_score_decides_its_band_and_zero_turns_it_off() -> None:
    """Below `sure`, the best match is a guess to check; 0: the rule is off."""
    files = [shot("DCIM/b.jpg", datetime(2019, 6, 2), camera="DJI FC3170")]
    unsure = DRONE.model_copy(update={"score": 60})
    (guess,) = run(files, unsure, FAIR).proposals
    assert (guess.band, guess.folder, guess.verdict.score) == (
        Band.UNSURE,
        "2019/To check/Drone",
        60,
    )
    (off,) = run(files, DRONE.model_copy(update={"score": 0})).proposals
    assert off.reason is SortReason.NO_SIGNAL


def test_other_category_takes_only_what_nothing_matched() -> None:
    """The fallback: a file an earlier rule guessed keeps that guess."""
    other = ClassifyRule(name="Other", match=RuleMatch.OTHER_CATEGORY, category="Other")
    files = [
        shot("DCIM/a.jpg", datetime(2019, 6, 2), camera="DJI"),
        shot("DCIM/b.jpg", datetime(2019, 6, 2)),
    ]
    found = by_name(run(files, DRONE.model_copy(update={"score": 60}), other))
    assert found["a.jpg"].rule == "Drone"
    assert (found["b.jpg"].rule, found["b.jpg"].folder) == ("Other", "2019/Other")


def test_rules_that_decided_nothing_are_listed() -> None:
    """A wrong year or a typo in a pattern: the rule is named, not silent."""
    files = [shot("DCIM/a.jpg", datetime(2019, 6, 2), camera="DJI")]
    result = run(files, ITALY, DRONE, FAIR)
    assert result.unused_rules == ("Italy", "Fair")
