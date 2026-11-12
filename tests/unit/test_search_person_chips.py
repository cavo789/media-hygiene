"""`library`: a photo's people come first; a click shows only theirs."""

from __future__ import annotations

import re

from tests.support.page_render import render_page


def _script() -> str:
    """The page's script from the words of a file on (`search_words.js.j2`)."""
    page = render_page("search.html.j2")
    return page[page.index("const PERSON_SOURCE") :]


def test_the_names_come_first_so_that_plus_n_never_hides_them() -> None:
    """A stable sort puts `person` first; only the first CHIPS_SHOWN show at S and M."""
    script = _script()
    assert 'const PERSON_SOURCE = "person";' in script
    assert ".sort((one, other) => shownFirst(one) - shownFirst(other))" in script
    assert script.index("shownFirst(other)") < script.index("slice(CHIPS_SHOWN)")


def test_a_name_is_marked_and_searched_among_the_people_only() -> None:
    """👤 before the name; a click searches `person:"<name>"`, not any source."""
    script = _script()
    assert '"chip person"' in script
    assert '"👤 " + word' in script
    assert 'PERSON_SOURCE + ":" + quoted(word)' in script
    assert "fill(TEXTS.lookForPerson, { name: word })" in script
    # Ctrl+click adds it, the filters kept: two names, the photos where both are.
    assert '$("text").value = ($("text").value.trim() + " " + typed).trim();' in script
    # The cross that takes the name off stays on the chip.
    assert "if (person) chip.append(unnameButton(hit, word));" in script


def test_the_bar_chip_keeps_a_name_whole_and_shows_it_as_on_the_card() -> None:
    """`person:"Anne Marie"` is one chip, written 👤 Anne Marie."""
    page = render_page("search.html.j2")
    words = re.search(r"const chipWords = \(text\) => text\.match\((/.+/g)\)", page)
    assert words is not None
    assert words.group(1) == r'/(?:\w+:)?"[^"]*"|\S+/g'
    label = re.search(r"word\.match\((/.+/i)\)", page)
    assert label is not None
    assert label.group(1) == r'/^person:"?([^"]*)"?$/i'
    assert "text: chipLabel(word)," in page
    # The same split in Python: a name of two words stays one chip.
    split = re.findall(r'(?:\w+:)?"[^"]*"|\S+', 'plage person:"Anne Marie" 2015')
    assert split == ["plage", 'person:"Anne Marie"', "2015"]
