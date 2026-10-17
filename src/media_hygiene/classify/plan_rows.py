"""The rows and events of `plan.json`: one row per file, files taken close together."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.layout import GeoValues, Values
from media_hygiene.classify.models import Band, DateSource, SortReason
from media_hygiene.classify.names import former_note, reason_name


class Frozen(BaseModel):
    """A frozen, strict pydantic model."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class RowValues(Frozen):
    """What the layouts know of a file: re-rendered when the user names its event."""

    year: int  # the year folder: an event keeps the year of its start
    month: int
    day: int
    category: str
    event: str  # the `{event}` value: the event's label or span
    event_start: str
    place: str = ""  # a personal place
    country: str = ""  # those of a trip
    region: str = ""
    city: str = ""

    @classmethod
    def of(cls, values: Values) -> RowValues:
        """Write layout values down.

        Args:
            values: What the layouts know of a file.

        Returns:
            The same, flat.
        """
        geo = values.geo
        return cls(
            year=values.year,
            month=values.month,
            day=values.day,
            category=values.category,
            event=values.event,
            event_start=values.event_start,
            place=geo.place,
            country=geo.country,
            region=geo.region,
            city=geo.city,
        )

    def as_values(self) -> Values:
        """The layout values.

        Returns:
            Them.
        """
        where = GeoValues(self.place, self.country, self.region, self.city)
        fields = self.model_dump(exclude={"place", "country", "region", "city"})
        return Values(**fields, geo=where)


class PlanRow(Frozen):
    """One media file and where it is proposed to go."""

    id: str
    path: str  # host path of the file
    size: int
    mtime_ns: int
    sha256: str | None
    date: str | None  # ISO date and time, local
    date_source: DateSource | None
    event_id: str
    values: RowValues | None  # what the layout was rendered from; None: stays
    band: Band
    reason: SortReason
    score: int
    rule: str = ""  # the name of the rule that decided; empty: no rule
    root: str  # host folder the proposal is relative to
    folder: str | None  # relative to `root`, `/`-separated; None: stay where it is
    name: str  # the target name: the original one for now
    # The host folders of the copies `clean` removed that the proposal read (0208);
    # `former_agreed` False: they gave several meanings and none was used.
    former: tuple[str, ...] = ()
    former_agreed: bool = True

    @property
    def category(self) -> str:
        """The proposed category.

        Returns:
            It, or an empty string.
        """
        return self.values.category if self.values else ""

    @property
    def decided_by(self) -> str:
        """The rule's name, else the reason, translated.

        Returns:
            It.
        """
        return self.rule or reason_name(self.reason)

    @property
    def why(self) -> str:
        """Why the file goes there, and the folders of removed copies it read.

        Returns:
            It.
        """
        return self.decided_by + former_note(self.former, agreed=self.former_agreed)

    @property
    def parent(self) -> str:
        """The host folder of the file, written as the host writes it.

        Returns:
            It.
        """
        cut = max(self.path.rfind("\\"), self.path.rfind("/"))
        return self.path[:cut] if cut > 0 else self.path

    @property
    def in_place(self) -> bool:
        """Tell whether the file already sits in its proposed folder.

        Returns:
            True when it stays, or its folder is the proposed one.
        """
        if self.folder is None:
            return True
        target = f"{self.root}/{self.folder}".replace("\\", "/")
        return self.parent.replace("\\", "/") == target


class PlanEvent(Frozen):
    """Files taken close together, named once."""

    id: str
    start: str
    end: str
    span: str  # the default name: `2016-07-01..07-15`
    label: str  # the meaningful folder the event came from, if any
    rows: tuple[str, ...]  # row ids, in date order
