"""French pages and messages: sizes in octets, each count agreeing with its own noun."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from media_hygiene.report.actions import ActionCommands, audit_actions, sure_count
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.services.review_file import review_page

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings


def test_the_sure_groups_agree_with_their_own_number() -> None:
    """`1 sûrs` came from the total of groups: the sure ones carry their plural."""
    install(Locale.FR)
    assert sure_count(0) == "0 sûr"
    assert sure_count(1) == "1 sûr"
    assert sure_count(3) == "3 sûrs"
    similar = SimpleNamespace(groups=(object(),) * 4, sure_groups=1, bursts=())
    plan = SimpleNamespace(decisions=())
    findings = cast("AuditFindings", SimpleNamespace(plan=plan, similar=similar))
    actions = audit_actions(findings, ActionCommands())
    assert actions[0].text.startswith(
        "4 groupes de quasi-doublons : 1 sûr, 3 à regarder"
    )


def test_the_near_review_page_says_its_sizes_in_french() -> None:
    """The page's script gets the translated units, never a hard-coded `KB`."""
    install(Locale.FR)
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    page = review_page("near_review.html.j2", place, ("/decide", "/file")).decode()
    assert '"units": ["o", "Ko", "Mo", "Go", "To"]' in page
    assert '"KB"' not in page
