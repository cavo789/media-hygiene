"""Every route that changes something, declared next to the phone's list (0429).

Anywhere but the PC, everything is read-only (maintainer, 2026-10-27): a test walks this
set against `lan_paths` and fails if a phone may reach one of them, whatever the
`[review]` settings. A new route that writes joins this set. One exception, by its body
only: `POST /api/step` naming an album saved on the PC, on the TV (`lan_show`, 0444).
"""

from __future__ import annotations

from typing import Final

from media_hygiene.people.app import CHANGE_PATH
from media_hygiene.places.posts import ASIDE_PATH, SAVE_PATH
from media_hygiene.review.app import DECIDE_PATH
from media_hygiene.review.ending import STOP_PATH
from media_hygiene.review.gone_app import GONE_DECIDE_PATH
from media_hygiene.review.home_app import AUDIT_PATH
from media_hygiene.review.home_tags_api import RUN_PATHS
from media_hygiene.review.home_views import APPLY_PATH
from media_hygiene.review.lan_phones_api import PHONE_PATHS
from media_hygiene.review.near_app import NEAR_DECIDE_PATH
from media_hygiene.review.pairs_app import PAIRS_DECIDE_PATH
from media_hygiene.review.phone_app import FREE_PATH, PHONE_DECIDE_PATH
from media_hygiene.review.shrink_app import CHOOSE_PATH, LIGHTEN_PATH
from media_hygiene.review.sort_choices import (
    DESTINATION_PATH,
    EVENT_PATH,
    FILES_PATH,
    FORGET_PATH,
    SURE_PATH,
)
from media_hygiene.review.sort_now import SORT_NOW_PATH
from media_hygiene.review.sort_rule_choices import RULE_PATH, RULES_REMOVE_PATH
from media_hygiene.review.step_watch import STEP_PATH
from media_hygiene.review.unwanted_app import JUNK_DECIDE_PATH
from media_hygiene.search.chosen_api import CHOSEN_PATH
from media_hygiene.search.people_desk import PEOPLE_REJECT_PATH
from media_hygiene.search.rule_desk import RULE_SAVE_PATH
from media_hygiene.search.rule_go import GO_PATHS

# The `POST`s that set aside, apply, move, save a rule, a name, a decision file or
# `config.toml`, run a step or the audit, stop the server.
_DECISIONS: Final = frozenset(
    {
        DECIDE_PATH,
        GONE_DECIDE_PATH,
        JUNK_DECIDE_PATH,
        NEAR_DECIDE_PATH,
        PAIRS_DECIDE_PATH,
        PHONE_DECIDE_PATH,
        FREE_PATH,
        CHOOSE_PATH,
        LIGHTEN_PATH,
    }
)
_SORTING: Final = frozenset(
    {
        DESTINATION_PATH,
        EVENT_PATH,
        FILES_PATH,
        FORGET_PATH,
        SURE_PATH,
        SORT_NOW_PATH,
        RULE_PATH,
        RULES_REMOVE_PATH,
        RULE_SAVE_PATH,
        *GO_PATHS,
    }
)
_PC_ONLY: Final = frozenset(
    {STOP_PATH, STEP_PATH, AUDIT_PATH, APPLY_PATH, *RUN_PATHS, *PHONE_PATHS}
)
CHANGES: Final = (
    _DECISIONS
    | _SORTING
    | _PC_ONLY
    | {CHOSEN_PATH, PEOPLE_REJECT_PATH, CHANGE_PATH, SAVE_PATH, ASIDE_PATH}
)
