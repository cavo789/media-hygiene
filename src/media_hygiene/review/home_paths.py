"""Every path the home page's own app answers (`HomeApp`).

The home server sends these to `HomeApp`, every other path to `library`: a path missing
here got a 405 from it (the ☆ favourites, the scan scope, the import steps: 0584).
"""

from __future__ import annotations

from typing import Final

from media_hygiene.review.home_app import AUDIT_PATH, FAVOURITES_PATH
from media_hygiene.review.home_more_api import MORE_PATHS
from media_hygiene.review.home_tags_api import RUN_PATHS
from media_hygiene.review.import_chain_api import IMPORT_CHAIN_PATH
from media_hygiene.review.import_steps_api import IMPORT_STEPS_PATH
from media_hygiene.review.lan_switch_api import LAN_SWITCH_PATH
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH
from media_hygiene.review.presence import PRESENCE_PATH
from media_hygiene.review.scan_scope_api import SCOPE_PATH
from media_hygiene.review.step_watch import STEP_PATH

HOME_PATHS: Final = frozenset(
    {PAGE_PATH, STATE_PATH, STEP_PATH, AUDIT_PATH, FAVOURITES_PATH, PRESENCE_PATH}
    | {
        SCOPE_PATH,
        LAN_SWITCH_PATH,
        IMPORT_STEPS_PATH,
        IMPORT_CHAIN_PATH,
        *RUN_PATHS,
        *MORE_PATHS.values(),
    }
)
