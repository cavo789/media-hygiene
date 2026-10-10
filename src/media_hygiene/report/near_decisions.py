r"""The `near` key of the decisions file: what `review --near` decided, group by group.

```json
"near": [{"kept": "C:\\Photos\\IMG_1.jpg", "copies": ["D:\\WhatsApp\\IMG-WA1.jpg"],
          "action": "swap", "keep": "D:\\WhatsApp\\IMG-WA1.jpg"}]
```

A group is named by the version the audit keeps and the copies it moves, in host
paths: if either changed since, `clean` refuses the file. Groups still undecided are
not listed: the tier decides for them.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, model_validator

from media_hygiene.plan.near_review import NearAction

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class NearGroupDecision(BaseModel):
    """The decision on one group of near duplicates, in host paths."""

    model_config = _FROZEN

    kept: str
    copies: tuple[str, ...]
    action: NearAction
    keep: str = ""  # `swap` only: the copy kept instead

    @model_validator(mode="after")
    def _keep_with_swap(self) -> NearGroupDecision:
        """Refuse a swap without one of the copies to keep, or a keep without swap.

        Returns:
            The decision, unchanged.

        Raises:
            ValueError: The decision is inconsistent.
        """
        if self.action is NearAction.SWAP and self.keep not in self.copies:
            message = "a swapped group of near duplicates keeps none of its copies"
            raise ValueError(message)
        if self.action is not NearAction.SWAP and self.keep:
            message = "only a swapped group of near duplicates keeps a copy"
            raise ValueError(message)
        return self


def _each_group_once(
    groups: tuple[NearGroupDecision, ...],
) -> tuple[NearGroupDecision, ...]:
    """Refuse a group decided twice: which decision would win?

    Args:
        groups: The decisions.

    Returns:
        The decisions, unchanged.

    Raises:
        ValueError: A kept version appears twice.
    """
    kept = [group.kept for group in groups]
    twice = sorted({path for path in kept if kept.count(path) > 1})
    if twice:
        message = f"{twice[0]} is decided twice"
        raise ValueError(message)
    return groups


type NearGroups = Annotated[
    tuple[NearGroupDecision, ...], AfterValidator(_each_group_once)
]
