"""French pages and messages: sizes in octets, each count agreeing with its own noun."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Final, cast

import polib

import media_hygiene
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from media_hygiene.report.actions import ActionCommands, audit_actions, sure_count
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.services.review_file import review_page

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings

_SOURCE: Final = Path(media_hygiene.__file__).parent
_CATALOG: Final = _SOURCE / "i18n/locales/fr/LC_MESSAGES/media_hygiene.po"
# The first text of a `_()` or `ngettext()` call in a template.
_TEXT: Final = re.compile(r'(?:_|ngettext)\("((?:[^"\\]|\\.)*)"')


def test_the_sure_groups_agree_with_their_own_number() -> None:
    """`1 sûrs` came from the total of groups: the sure ones carry their plural."""
    install(Locale.FR)
    assert sure_count(0) == "0 sûr"
    assert sure_count(1) == "1 sûr"
    assert sure_count(3) == "3 sûrs"
    similar = SimpleNamespace(groups=(object(),) * 4, sure_groups=1, bursts=())
    plan = SimpleNamespace(decisions=(), returned=())
    findings = cast(
        "AuditFindings", SimpleNamespace(plan=plan, similar=similar, gone=0)
    )
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


def test_the_burst_review_page_gives_both_forms_of_a_count() -> None:
    """The count is known only in the browser: the page gets both forms, no "(s)"."""
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    install(Locale.FR)
    page = review_page("review.html.j2", place, ("/decide", "/file")).decode()
    french = _texts(page)
    install(Locale.EN)
    page = review_page("review.html.j2", place, ("/decide", "/file")).decode()
    english = _texts(page)
    assert french["nAside"] == ["{n} photo écartée", "{n} photos écartées"]
    assert english["nAside"] == ["{n} shot set aside", "{n} shots set aside"]
    assert "Intl.PluralRules(document.documentElement.lang)" in page
    assert "(s)" not in json.dumps(french, ensure_ascii=False)


def _texts(page: str) -> dict[str, object]:
    """Read the texts a review page gives its script.

    Args:
        page: The rendered page.

    Returns:
        The `T` object of the script.
    """
    line = page.split("const T = ", 1)[1].split("\n", 1)[0]
    return cast("dict[str, object]", json.loads(line.removesuffix(";")))


def test_no_page_text_writes_a_plural_with_brackets() -> None:
    """No "(s)" in a text of a template, in English or in its French translation."""
    french = {
        entry.msgid: " ".join([entry.msgstr, *entry.msgstr_plural.values()])
        for entry in polib.pofile(str(_CATALOG))
    }
    texts = {
        text
        for template in _SOURCE.rglob("*.j2")
        for text in _TEXT.findall(template.read_text(encoding="utf-8"))
    }
    bracketed = [text for text in texts if "(s)" in f"{text} {french.get(text, '')}"]
    assert not bracketed
