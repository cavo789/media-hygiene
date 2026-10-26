"""The cards the sort review page shows: one per event, one per photo."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from media_hygiene.review.sort_sides import Side

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class EventCard(BaseModel):
    """One event of the work list, without its photos."""

    model_config = _FROZEN

    id: str
    title: str  # its label, else its dates
    span: str
    files: int
    undecided: int  # files to check or to sort
    share: int  # cumulated share of the work, in percent
    folders: tuple[str, ...]  # where its files come from, the fullest first
    category: str  # proposed
    folder: str  # proposed, relative to the target; empty: stays
    prefix: str  # the part of the proposed folder before its category: `2011/`
    band: str
    why: str
    sure: bool  # one click may accept its proposal: `sort_sure`
    moves: int  # files accepting the proposal moves
    kept: int  # files that keep a folder the user named
    kept_folders: tuple[str, ...]  # those folders, their last part
    workbook: Side
    page: Side | None
    saved: str  # when the page's choice was saved, as read back: ISO 8601, UTC
    sorted: bool  # an earlier `sort` (this page's included) moved its files
    first_day: str  # ISO: what *Remember as a rule* proposes (0392)
    last_day: str
    rule: str  # the rule deciding most of its files; empty: none
    rule_days: str  # its days, for a `date_range` rule
    conflict: bool


class PhotoCard(BaseModel):
    """One file of an event."""

    model_config = _FROZEN

    row: str
    name: str
    folder: str  # where it is, on the host
    date: str
    band: str
    proposed: str  # its proposed folder; empty: stays
    thumb: str
    preview: str
    movable: bool  # files left as they are ignore every choice
    own: bool  # in a folder the user named: an event choice never flattens it
    workbook: str
    page: str
    conflict: bool
