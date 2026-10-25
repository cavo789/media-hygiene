"""`[classify]` — how `classify` proposes a tree; every value is an example."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from media_hygiene.classify.layout import check_layout
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_ai import AiSettings
from media_hygiene.config.classify_defaults import LIBRARY_FOLDERS, NAME_DATES, SCORES
from media_hygiene.config.classify_places import PersonalPlace, check_places
from media_hygiene.config.classify_rules import (
    DEFAULT_RULES,
    ClassifyRule,
    unique_names,
)
from media_hygiene.config.clock_settings import ClockRules
from media_hygiene.config.patterns import valid_patterns
from media_hygiene.config.place_photos import PlacePhotos, check_place_photos
from media_hygiene.i18n import _

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_TownName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ClassifySettings(BaseModel):
    """`[classify]` — layouts per band, events, rules and the confidence thresholds.

    Layouts are relative to the target root; an empty layout leaves the files where they
    are. `target` empty sorts each mounted folder in place.
    """

    model_config = _FROZEN

    target: str = ""
    leave: tuple[str, ...] = ()
    timezone: str = ""
    layout: str = "{year}/{category}"
    unsure_layout: str = "{year}/To check/{category}"
    manual_layout: str = "{year}/To sort/{event}"
    undated_layout: str = "To sort/Undated"
    received_layout: str = "To sort/Received and downloaded"
    session_gap_hours: float = 6
    merge_gap_hours: float = 18
    min_event_size: int = 5
    event_year: Literal["start", "per_file"] = "start"
    sure: int = 80
    unsure: int = 50
    scores: dict[str, int] = SCORES
    name_dates: tuple[str, ...] = NAME_DATES
    generic_folders: tuple[str, ...] = LIBRARY_FOLDERS
    rules: tuple[ClassifyRule, ...] = DEFAULT_RULES
    ai: AiSettings = AiSettings()
    places: tuple[PersonalPlace, ...] = ()
    place_photos: tuple[PlacePhotos, ...] = ()  # photos given a place by hand (0237)
    clocks: ClockRules = ()  # a camera's clock off by an hour or a day, set right
    trip_min_km: float = Field(default=100, gt=0)
    trip_merge_gap_hours: float = Field(default=48, ge=0)
    trip_merge_max_km: float = Field(default=120, ge=0)
    # The exact GeoNames name of a town → the user's name for it ("Brugge" = "Bruges").
    town_names: dict[_TownName, _TownName] = {}
    folder_town_min_population: int = Field(default=5000, ge=0)
    folder_town_ignore: tuple[str, ...] = ()  # folder names that are never towns
    # People whose folders (`Photos Chloé`) are theirs, besides `[[people.person]]`.
    person_folders: tuple[str, ...] = ()

    @field_validator(
        "layout", "unsure_layout", "manual_layout", "undated_layout", "received_layout"
    )
    @classmethod
    def _valid_layout(cls, layout: str) -> str:
        """Refuse a layout with an unknown placeholder or a forbidden name.

        Args:
            layout: A layout.

        Returns:
            It, unchanged.
        """
        check_layout(layout)
        return layout

    @field_validator("name_dates", "generic_folders")
    @classmethod
    def _valid_patterns(cls, patterns: tuple[str, ...]) -> tuple[str, ...]:
        """Reject patterns that are not valid regular expressions.

        Args:
            patterns: Configured patterns.

        Returns:
            The patterns, unchanged.
        """
        return valid_patterns(patterns)

    @field_validator("rules")
    @classmethod
    def _unique_rules(cls, rules: tuple[ClassifyRule, ...]) -> tuple[ClassifyRule, ...]:
        """Refuse two rules with the same name.

        Args:
            rules: The rules.

        Returns:
            Them, unchanged.
        """
        return unique_names(rules)

    @field_validator("places")
    @classmethod
    def _unique_places(
        cls, places: tuple[PersonalPlace, ...]
    ) -> tuple[PersonalPlace, ...]:
        """Refuse two places of the same name, or two homes.

        Args:
            places: The places.

        Returns:
            Them, unchanged.
        """
        check_places(places)
        return places

    @model_validator(mode="after")
    def _trips_need_home(self) -> Self:
        """Refuse a `trip` rule without a home, photos given to no place.

        Returns:
            The settings, unchanged.

        Raises:
            ValueError: A trip rule is written, and no place is home; a
                `[[classify.place_photos]]` names no place.
        """
        check_place_photos(self.places, self.place_photos)
        trips = [rule.name for rule in self.rules if rule.match is RuleMatch.TRIP]
        if trips and not any(place.home for place in self.places):
            message = _(
                "rule '{name}': match = 'trip' needs a [[classify.places]] "
                "with home = true"
            ).format(name=trips[0])
            raise ValueError(message)
        return self

    @field_validator("scores")
    @classmethod
    def _all_scores(cls, scores: dict[str, int]) -> dict[str, int]:
        """Complete the scores a user wrote with the default ones.

        Args:
            scores: The scores written.

        Returns:
            Every score: a reason left out keeps its default.
        """
        return {**SCORES, **scores}
