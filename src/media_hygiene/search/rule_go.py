"""*I checked: sort these N files* (0397): the files a period's rule takes, sorted.

`POST /api/period-rule/go` receives the rule typed and the files the user kept (the
others left where they are on the page); the rule is tried again, so each file goes to
the folder the page showed, then the group is sorted in a thread (`services.group_sort`:
file choices in `sort-decisions.json`, read back, then `sort` cut to those rows,
journaled). The answer is the run as the disk holds it.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.search.rule_desk import refused_rule
from media_hygiene.search.rule_models import PeriodRuleIn

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.review.http import Response
    from media_hygiene.search.rule_desk import RuleDesk

RULE_GO_PATH: Final = "/api/period-rule/go"


class PeriodGoIn(PeriodRuleIn):
    """The rule typed, and the files kept in the group (by their key in the index)."""

    keys: tuple[int, ...]


async def go_answer(desk: RuleDesk, body: bytes) -> Response:
    """Sort the files kept of what the rule takes.

    Args:
        desk: The rule's desk: its trial and its sorter.
        body: The rule and the keys.

    Returns:
        The run read back; 400 for a rule that cannot be written, 409 with the
        sentence to show when nothing can move.
    """
    try:
        asked = PeriodGoIn.model_validate_json(body)
        rule = asked.rule()
    except ValidationError as exc:
        return refused_rule(exc)
    if desk.sorter is None:
        return _conflict(_("This page cannot move files: run 'sort' in the terminal."))
    folders = _kept(desk, asked, rule)
    if not folders:
        return _conflict(
            _("None of these files is taken by the rule: nothing to sort.")
        )
    try:
        done = await asyncio.to_thread(desk.sorter, folders, rule.category)
    except MediaHygieneError as exc:
        return _conflict(" ".join(filter(None, (exc.message, exc.tip))))
    return json_response(HTTPStatus.OK, dict(done))


def _kept(desk: RuleDesk, asked: PeriodGoIn, rule: ClassifyRule) -> dict[Path, str]:
    """The files kept that the rule takes, tried again: each to the folder shown.

    Args:
        desk: The rule's desk.
        asked: The rule typed and the keys kept.
        rule: It, checked.

    Returns:
        Container path → its folder below its root.
    """
    found, tried = desk.run_trial(asked, rule)
    kept = frozenset(asked.keys)
    folders: dict[Path, str] = {}
    for hit in found.hits:
        where = tried.get(hit.photo.path)
        if hit.key in kept and where is not None and where.taken and where.folder:
            folders[hit.photo.path] = where.folder
    return folders


def _conflict(said: str) -> Response:
    """Answer that nothing moved, and why.

    Args:
        said: The sentence to show.

    Returns:
        409, with it.
    """
    return json_response(HTTPStatus.CONFLICT, {"error": said})
