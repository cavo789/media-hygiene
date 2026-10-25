"""*📌 Make it a rule* on the search page (0396): a period of days becomes a date rule.

`POST /api/period-rule/trial` tries the rule typed on the files of its days (the
classify engine, nothing written, `services.rule_trial`) and answers them as the grid
shows files, each with where it would go and whether the rule takes it.
`POST /api/period-rule` writes it into `config.toml` (or replaces the rule chosen in
*Update a rule…*), read back from the disk; `GET /api/period-rules` lists the date
rules of the file, the latest first, for *Update a rule…*.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.classify.rules.calendar import parse_one_off
from media_hygiene.classify.rules_edit import replace_rule
from media_hygiene.classify.rules_file import add_rule
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.review.sort_rule import overlapping
from media_hygiene.search.chosen_api import chosen_refused
from media_hygiene.search.models import Found
from media_hygiene.search.query import Filters, SearchQuery
from media_hygiene.search.rule_models import (
    PeriodRuleIn,
    RuleTry,
    dated_rules,
    line,
    refused_rule,
    shown_in,
    where_of,
    wider,
)
from media_hygiene.search.views import found_view

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.rule_models import Sorter, Trial, Tried

RULE_TRIAL_PATH: Final = "/api/period-rule/trial"
RULE_SAVE_PATH: Final = "/api/period-rule"
PERIOD_RULES_PATH: Final = "/api/period-rules"
RULE_POSTS: Final = frozenset({RULE_TRIAL_PATH, RULE_SAVE_PATH})
# An evening ending after midnight stays one event: the day before and after are read.
_MARGIN: Final = timedelta(days=1)
_TRIED_MAX: Final = 3000  # files tried at most: a few days hold a few hundred
_NANOSECONDS: Final = 1_000_000_000


@dataclass(frozen=True, slots=True)
class RuleDesk:
    """Answers the page about the rule of a period."""

    index: SearchIndex
    mapper: HostPathMapper
    config: Path | None  # `config.toml`; None: the page cannot write it
    rules: Callable[[], Sequence[ClassifyRule]]  # those of `config.toml`, read now
    trial: Trial
    sorter: Sorter | None = None  # sorts a group checked on the page (0397)

    def run_trial(
        self, asked: PeriodRuleIn, rule: ClassifyRule
    ) -> tuple[Found, Mapping[Path, Tried]]:
        """Try a rule on the files of its days, and the day before and after.

        Args:
            asked: The rule typed, the rule it replaces.
            rule: It, checked.

        Returns:
            The files read, and where each one would go.
        """
        window = parse_one_off(rule.dates)
        days = (window.start - _MARGIN, window.end + _MARGIN)
        found = self.index.find(SearchQuery((), Filters(days=days)), _TRIED_MAX)
        files = [hit.photo for hit in found.hits]
        return found, self.trial(RuleTry(rule, asked.replaces, files))

    def posts(self) -> dict[str, Callable[[bytes], Response]]:
        """The answers to the page's JSON bodies, by path.

        Returns:
            The trial and the save.
        """
        return {RULE_TRIAL_PATH: self.tried, RULE_SAVE_PATH: self.save}

    def state(self) -> Response:
        """`GET /api/period-rules`: the date rules, the latest first.

        Returns:
            Their names, days, folders.
        """
        return json_response(HTTPStatus.OK, {"rules": dated_rules(self.rules())})

    def tried(self, body: bytes) -> Response:
        """`POST /api/period-rule/trial`: what the rule would take, as files.

        Args:
            body: The rule typed.

        Returns:
            The files of its days (and those of the events it takes), each with its
            destination; 400 for a rule that cannot be written.
        """
        try:
            asked = PeriodRuleIn.model_validate_json(body)
            rule = asked.rule()
        except ValidationError as exc:
            return refused_rule(exc)
        window = parse_one_off(rule.dates)
        found, tried = self.run_trial(asked, rule)
        shown = [hit for hit in found.hits if shown_in(hit, tried, window)]
        views = found_view(Found(len(shown), tuple(shown)), self.mapper)["hits"]
        hits: list[dict[str, object]] = [
            {**view, **where_of(tried.get(hit.photo.path))}
            for hit, view in zip(shown, views, strict=True)  # type: ignore[call-overload]
        ]
        taken = sorted((v for v in hits if v["taken"]), key=lambda v: str(v["to"]))
        written = self.rules()  # read now: the page may have saved one since
        return json_response(
            HTTPStatus.OK,
            {
                "hits": taken + [view for view in hits if not view["taken"]],
                "taken": len(taken),
                "left": len(hits) - len(taken),
                "folders": [
                    {"folder": folder, "files": count}
                    for folder, count in Counter(v["to"] for v in taken).most_common()
                ],
                "overlaps": overlapping(
                    window, (r for r in written if r.name != asked.replaces)
                ),
                "name_taken": any(
                    other.name.casefold() == rule.name.casefold()
                    for other in written
                    if other.name != asked.replaces
                ),
                "cut": found.total > _TRIED_MAX,
                "wider": wider(shown, tried, window),  # events mostly outside
            },
        )

    def save(self, body: bytes) -> Response:
        """`POST /api/period-rule`: write the rule into `config.toml`, read it back.

        Args:
            body: The rule typed.

        Returns:
            The rule as the file holds it, and when the file was written; 400 for a
            rule that cannot be written, 409 when the file refused it.
        """
        try:
            asked = PeriodRuleIn.model_validate_json(body)
            rule = asked.rule()
        except ValidationError as exc:
            return refused_rule(exc)
        if self.config is None or not self.config.is_file():
            return chosen_refused(ConfigError(_("This page cannot write config.toml.")))
        try:
            held = (
                replace_rule(self.config, asked.replaces, rule)
                if asked.replaces
                else add_rule(self.config, rule)
            )
        except ConfigError as exc:
            return chosen_refused(exc)
        written = self.config.stat().st_mtime_ns / _NANOSECONDS
        return json_response(
            HTTPStatus.OK,
            {
                **line(held),
                "modified": datetime.fromtimestamp(written, tz=UTC).isoformat(),
                "rules": dated_rules(self.rules()),
            },
        )
