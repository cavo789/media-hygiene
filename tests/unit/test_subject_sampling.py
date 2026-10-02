"""Which photos the model sees, and what their answers give the other files."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from media_hygiene.classify.ai.models import Candidate, Subject, Unit
from media_hygiene.classify.ai.sampling import choose_samples, units_of
from media_hygiene.classify.ai.subjects import NONE, per_photo, subjects_of
from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import MediaInput
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_ai import AiSettings
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.scan.models import VisualFacts

ROOT = Path("/data/c/Photos")
START = datetime(2021, 7, 14, 10)
AI = AiSettings(model="m", min_edge=512)


def shot(
    relative: str, when: datetime, size: tuple[int, int] = (1024, 768)
) -> MediaInput:
    """A photo with an EXIF date, sharper when later."""
    taken = when.strftime("%Y:%m:%d %H:%M:%S")
    visual = VisualFacts(0, 0, *size, float(when.hour), taken, "Canon")
    return MediaInput(ROOT / relative, ROOT, 10, 0, visual)


def series(folder: str, count: int, start: datetime = START) -> list[MediaInput]:
    """`count` photos in `folder`, one hour apart."""
    return [
        shot(f"{folder}/{index}.jpg", start + timedelta(hours=index))
        for index in range(count)
    ]


def units(files: list[MediaInput], *rules: ClassifyRule) -> tuple[Unit, ...]:
    """The units of a run with these rules."""
    found = classify(files, ClassifySettings(rules=rules), Scope())
    return units_of(found.proposals, AI)


def test_an_event_without_a_signal_is_one_unit() -> None:
    """Five loose photos of a day: one unit, every photo a candidate."""
    (unit,) = units(series("DCIM", 5))
    assert len(unit.members) == len(unit.candidates) == 5


def test_decided_tiny_and_video_files_are_never_sent() -> None:
    """A named folder decides; a thumbnail and a video only follow their event."""
    loose = series("DCIM", 5)
    tiny = shot("DCIM/thumb.jpg", START + timedelta(minutes=30), (160, 120))
    video = MediaInput(ROOT / "DCIM/clip.mp4", ROOT, 10, 0)
    named = series("Seaside", 5, START + timedelta(days=30))
    folders = ClassifyRule(name="Folders", match=RuleMatch.EXISTING_FOLDER)
    (unit,) = units([*loose, tiny, video, *named], folders)
    assert tiny.path in unit.members
    assert {c.path for c in unit.candidates} == {f.path for f in loose}
    assert not any(path.parent.name == "Seaside" for path in unit.members)


def test_a_lone_photo_is_a_unit_of_its_own() -> None:
    """Fewer photos than an event: each one answers for itself."""
    found = units(series("DCIM", 2))
    assert [len(unit.members) for unit in found] == [1, 1]


def candidates(count: int) -> Unit:
    """A unit of `count` candidates, one hour apart, sharper when later."""
    made = tuple(
        Candidate(Path(f"/p/{index}.jpg"), START + timedelta(hours=index), index)
        for index in range(count)
    )
    return Unit("e", tuple(c.path for c in made), made)


def test_samples_are_spread_over_the_span_the_sharpest_of_each_part() -> None:
    """Nine photos, three samples: the sharpest of each third."""
    picked = choose_samples(candidates(9), 3, ())
    assert [path.name for path in picked] == ["2.jpg", "5.jpg", "8.jpg"]


def test_described_photos_are_preferred_so_a_recut_costs_nothing() -> None:
    """Enough photos described already: they are the samples."""
    described = {Path("/p/0.jpg"), Path("/p/1.jpg"), Path("/p/4.jpg")}
    assert set(choose_samples(candidates(9), 3, described)) == described
    assert choose_samples(candidates(9), 3, {Path("/p/3.jpg")})[1].name == "3.jpg"


def test_few_candidates_or_per_photo_take_them_all() -> None:
    """Two photos for three samples, or every photo asked: all of them."""
    assert len(choose_samples(candidates(2), 3, ())) == 2
    assert len(choose_samples(candidates(7), 0, ())) == 7


def answered(*answers: str) -> dict[Path, Subject]:
    """The subjects of one unit of three files whose samples gave these answers."""
    unit = candidates(len(answers))
    samples = {"e": unit.members}
    return subjects_of((unit,), samples, dict(zip(unit.members, answers, strict=True)))


def test_agreement_among_samples_is_the_confidence() -> None:
    """3 of 3: agreed; 2 of 3: the majority, to check; one answer: to check."""
    assert set(answered("Beach", "Beach", "Beach").values()) == {
        Subject("Beach", agreed=True)
    }
    assert set(answered("Beach", "Snow", "Beach").values()) == {
        Subject("Beach", agreed=False)
    }
    assert set(answered("Beach").values()) == {Subject("Beach", agreed=False)}


def test_none_of_these_wins_and_leaves_the_other_rules() -> None:
    """Most samples fit no category: no subject at all."""
    assert not answered(NONE, NONE, "Beach")
    assert not subjects_of((candidates(3),), {}, {})


def test_per_photo_gives_each_photo_its_own_answer() -> None:
    """Each photo keeps its answer, agreed when another photo shares it."""
    unit = candidates(3)
    answers = dict(zip(unit.members, ("Beach", "Beach", "Snow"), strict=True))
    found = per_photo((unit,), {"e": unit.members}, answers)
    assert [found[path] for path in unit.members] == [
        Subject("Beach", agreed=True),
        Subject("Beach", agreed=True),
        Subject("Snow", agreed=False),
    ]
    assert not per_photo(
        (unit,), {"e": unit.members}, dict.fromkeys(unit.members, NONE)
    )
