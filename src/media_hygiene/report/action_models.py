"""What an audit lets the user do: one action, and the commands they suggest."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionCommands:
    """The full command of each action, ready to paste."""

    clean: str = ""
    near: str = ""
    review: str = ""
    near_review: str = ""  # `review --near`: the groups to look at, in the browser
    gone_review: str = ""  # `review --gone`: the files deleted in the Explorer (0224)


@dataclass(frozen=True, slots=True)
class AuditAction:
    """One thing the user can do now: an icon, what it gains and costs, its command."""

    icon: str
    text: str
    command: str = ""
