"""The routes of `review --pairs`: the page, its state, previews, and each decision.

`GET /` serves the page, `GET /api/state` every folder pair and the decisions so far,
`GET /preview/<key>.jpg` a large preview of a sample, `GET /original/<key>.<ext>` the
file itself, untouched, `GET /api/file` the decisions file as read from the disk, and
`POST /api/pairs` decides one pair, saved, then answers with that pair as read back
from the disk. A decision needs a JSON body: a page of another site cannot send one
without the browser asking first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final, override

from pydantic import BaseModel, ConfigDict

from media_hygiene.plan.review import PairAction
from media_hygiene.review.decide_route import DecidingApp
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.pairs_session import PairsSession

PAIRS_DECIDE_PATH: Final = "/api/pairs"
PAIRS_FILE_PATH: Final = FILE_PATH


class _Choice(BaseModel):
    """`POST /api/pairs`: the decision on one pair; None: back to undecided."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pair: int
    action: PairAction | None


@dataclass(frozen=True, slots=True)
class PairsApp(DecidingApp[PairsSession]):
    """Answers the browser; the session holds the decisions and saves them."""

    decide_path: ClassVar[str] = PAIRS_DECIDE_PATH

    @override
    def decide(self, body: bytes) -> dict[str, object]:
        """Decide one pair and save the decisions file.

        Args:
            body: The JSON body of `POST /api/pairs`.

        Returns:
            The pairs decided, and that pair as read back from the disk.
        """
        choice = _Choice.model_validate_json(body)
        proof = self.session.decide({choice.pair: choice.action})
        return self.session.counts() | {"file": proof.model_dump(mode="json")}
