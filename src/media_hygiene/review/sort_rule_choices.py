"""The rule routes of the sort review (0392, 0393): preview, save, remove.

`POST /api/rule/preview` tells what a rule would take, `/api/rule` writes it into
`config.toml` (or replaces a folder-name rule in place), `/api/rules/remove` removes the
rules that decide nothing; `GET /api/rules` (`events_choose`) lists what each decided.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.review.sort_rule import RuleIn

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.review.sort_choosing import RuleSaved
    from media_hygiene.review.sort_rule import RulePreview
    from media_hygiene.review.sort_rules_view import RulesView

RULE_PREVIEW_PATH: Final = "/api/rule/preview"
RULE_PATH: Final = "/api/rule"
RULES_PATH: Final = "/api/rules"  # GET: *Your rules* (0393)
RULES_REMOVE_PATH: Final = "/api/rules/remove"
PROGRESS_PATH: Final = "/api/progress"  # GET: sorted, in place, left; the runs (0398)


class _RemoveIn(BaseModel):
    """`POST /api/rules/remove`: the rules to remove from `config.toml`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    names: tuple[str, ...]


def _rule_preview(session: SortBatchSession, body: bytes) -> RulePreview:
    """Tell what a rule for an event would take; nothing is saved.

    Args:
        session: The review.
        body: The JSON body.

    Returns:
        Its counts.
    """
    return session.rule_preview(RuleIn.model_validate_json(body))


def _rule(session: SortBatchSession, body: bytes) -> RuleSaved:
    """Write a rule for an event into `config.toml`, and choose the event's folder.

    Args:
        session: The review.
        body: The JSON body.

    Returns:
        The rule read back, and the event.
    """
    return session.save_rule(RuleIn.model_validate_json(body))


def _remove_rules(session: SortBatchSession, body: bytes) -> RulesView:
    """Remove rules from `config.toml`.

    Args:
        session: The review.
        body: The JSON body.

    Returns:
        The rules the file holds now.
    """
    return session.remove_rules(_RemoveIn.model_validate_json(body).names)


RULE_CHOICES: Final[Mapping[str, Callable[[SortBatchSession, bytes], BaseModel]]] = (
    MappingProxyType(
        {
            RULE_PREVIEW_PATH: _rule_preview,
            RULE_PATH: _rule,
            RULES_REMOVE_PATH: _remove_rules,
        }
    )
)
