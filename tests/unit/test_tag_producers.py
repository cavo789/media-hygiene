"""The cheap tags, on synthetic paths: folder words, dates, holidays, places."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from media_hygiene.classify.models import MediaInput
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.settings import Settings
from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.constants import Locale
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import VisualFacts
from media_hygiene.tags.context import TagContext, tag_context
from media_hygiene.tags.models import PlaceKind, Tag, TagSource
from media_hygiene.tags.normalize import WordRules
from media_hygiene.tags.producers import cheap_tags, folder_words, place_tags
from tests.support.towns import write_towns

ROOT = Path("/data/c/Photos")
TURIN = MediaMetadata(latitude=45.0712, longitude=7.6850)


def context(settings: Settings | None = None, language: str = "fr") -> TagContext:
    """The producers' context of some settings, tags in `language`."""
    chosen = settings or Settings()
    tags = TagSettings(language=language)  # type: ignore[arg-type]
    return tag_context(chosen, WordRules.of(tags, Locale.EN))


def photo(
    relative: str, taken_at: str | None = None, metadata: MediaMetadata | None = None
) -> MediaInput:
    """A photo below the root, with an EXIF date and metadata."""
    visual = VisualFacts(0, 0, 4000, 3000, 200.0, taken_at=taken_at)
    return MediaInput(ROOT / relative, ROOT, 10, 1, visual, metadata)


def test_folder_words_skip_generic_dates_months_and_links() -> None:
    """`2019/Juillet 2019/Durbuy - les ours` → Durbuy, ours."""
    file = photo("2019/Juillet 2019/Durbuy - les ours/IMG_0001.jpg")
    assert folder_words(file, context()) == ("Durbuy", "ours")


def test_device_and_library_folders_say_nothing() -> None:
    """DCIM, 100CANON, Camera: no word."""
    assert not folder_words(photo("DCIM/100CANON/IMG_0001.jpg"), context())


def test_a_labelled_month_keeps_its_label() -> None:
    """`Mars 2005 - Travaux maison` → Travaux, maison."""
    file = photo("Mars 2005 - Travaux maison/IMG_1.jpg")
    assert folder_words(file, context()) == ("Travaux", "maison")


def test_words_are_listed_once_whatever_their_case() -> None:
    """`Durbuy/durbuy` gives one folder tag."""
    tags = cheap_tags(photo("Durbuy/durbuy/IMG_1.jpg"), context())
    assert [t for t in tags if t.source is TagSource.FOLDER] == [
        Tag(TagSource.FOLDER, "Durbuy")
    ]


def date_tags(file: MediaInput, chosen: TagContext) -> list[str]:
    """The values of the date tags of a file."""
    return [t.value for t in cheap_tags(file, chosen) if t.source is TagSource.DATE]


def test_date_words_in_french() -> None:
    """Year, month, season, Christmas."""
    file = photo("IMG_1.jpg", "2006:12:25 10:00:00")
    assert date_tags(file, context()) == ["2006", "décembre", "hiver", "Noël"]


def test_easter_and_english() -> None:
    """Easter Monday 2007, in English."""
    file = photo("IMG_1.jpg", "2007:04:09 10:00:00")
    assert date_tags(file, context(language="en")) == [
        "2007",
        "April",
        "spring",
        "Easter",
    ]


def test_the_southern_hemisphere_turns_the_seasons() -> None:
    """July in Sydney is winter."""
    sydney = MediaMetadata(latitude=-33.87, longitude=151.21)
    file = photo("IMG_1.jpg", "2019:07:14 10:00:00", sydney)
    assert date_tags(file, context(language="en"))[2] == "winter"


def test_without_a_date_the_folder_gives_the_year() -> None:
    """`Avril 2007` → 2007, avril, printemps; `2008` alone → 2008."""
    assert date_tags(photo("Avril 2007/IMG_1.jpg"), context()) == [
        "2007",
        "avril",
        "printemps",
    ]
    assert date_tags(photo("2008/IMG_1.jpg"), context()) == ["2008"]
    assert date_tags(photo("Divers/IMG_1.jpg"), context()) == []


def test_the_users_date_rules_name_their_days() -> None:
    """A calendar rule and a date range give their names; a rule turned off not."""
    rules = (
        ClassifyRule(name="Kermesse", match=RuleMatch.CALENDAR, dates="06-15"),
        ClassifyRule(
            name="Sicile", match=RuleMatch.DATE_RANGE, dates="2019-06-10..2019-06-20"
        ),
        ClassifyRule(name="Off", match=RuleMatch.CALENDAR, dates="06-15", score=0),
    )
    settings = Settings.model_validate({"classify": {"rules": rules}})
    file = photo("IMG_1.jpg", "2019:06:15 10:00:00")
    assert date_tags(file, context(settings))[-2:] == ["Kermesse", "Sicile"]


def test_a_video_is_dated_by_its_own_date() -> None:
    """No EXIF: the date the video recorded."""
    video = MediaInput(
        ROOT / "clip.mp4",
        ROOT,
        10,
        1,
        None,
        MediaMetadata(created="2021-07-14T10:00:00Z"),
    )
    assert date_tags(video, context(language="en"))[:2] == ["2021", "July"]


def test_places_name_the_users_place_then_the_town(tmp_path: Path) -> None:
    """Inside a personal circle, near Turin; nothing without GPS nor far at sea."""
    home = PersonalPlace(name="Chez Marco", latitude=45.0712, longitude=7.685)
    settings = Settings.model_validate({"classify": {"places": [home]}})
    chosen = replace(context(settings), towns=Gazetteer.load(write_towns(tmp_path)))
    assert place_tags(photo("a.jpg", metadata=TURIN), chosen) == (
        Tag(TagSource.PLACE, "Chez Marco", kinds=(PlaceKind.PERSONAL,)),
        Tag(TagSource.PLACE, "Turin", kinds=(PlaceKind.TOWN,)),
        Tag(TagSource.PLACE, "Italy", kinds=(PlaceKind.COUNTRY,)),
    )
    assert not place_tags(photo("a.jpg"), chosen)
    sea = MediaMetadata(latitude=40.0, longitude=10.0)
    assert not place_tags(photo("a.jpg", metadata=sea), chosen)


def test_a_place_named_like_its_town_is_kept_once(tmp_path: Path) -> None:
    """A personal place called `turin`: one word, a place and a town both."""
    home = PersonalPlace(name="turin", latitude=45.0712, longitude=7.685)
    settings = Settings.model_validate({"classify": {"places": [home]}})
    chosen = replace(context(settings), towns=Gazetteer.load(write_towns(tmp_path)))
    found = place_tags(photo("a.jpg", metadata=TURIN), chosen)
    assert [(tag.value, tag.kinds) for tag in found] == [
        ("turin", (PlaceKind.PERSONAL, PlaceKind.TOWN)),
        ("Italy", (PlaceKind.COUNTRY,)),
    ]


def test_without_towns_only_personal_places() -> None:
    """No gazetteer loaded: no town, no error."""
    assert not place_tags(photo("a.jpg", metadata=TURIN), context())
