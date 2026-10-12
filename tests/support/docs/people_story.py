"""Step 10 of the sort guide, played for real: find the faces, name one, sort by person.

The demo library holds generated faces (`portraits.py`); the real detector of the image
finds them. `people --sample` measures, the people page names the largest group, then a
`person` rule is added to config.toml for one `classify`, and config.toml put back as it
was: the rest of the story sorts without it. Every demo photo already lies in a folder:
the rule goes right above *Existing folders*, or that rule would decide them all.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Final

from tests.support.docker import IMAGE
from tests.support.docs.container import Command, read_file, run
from tests.support.docs.names import Locale
from tests.support.docs.screenshots import Job, shoot, start_review, stop_review

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from tests.support.docs.container import Demo

type Captures = dict[str, str]

NAME: Final = "Chloé"  # the woman of `portraits.py`, as the documentation calls her
SAMPLE: Final = "10"  # photos measured: what is left takes long enough to show
PEOPLE_CAPTURES: Final = frozenset(
    {"people-sample.txt", "people.txt", "classify-person.txt"}
)
# The rule of step 10, in each language (the documentation shows the same one).
_RULES: Final[Mapping[Locale, str]] = {
    Locale.EN: '[[classify.rules]]\nname = "With Chloé"\nmatch = "person"\n'
    'names = ["Chloé"]\ncategory = "People/Chloé"\n',
    Locale.FR: '[[classify.rules]]\nname = "Avec Chloé"\nmatch = "person"\n'
    'names = ["Chloé"]\ncategory = "Personnes/Chloé"\n',
}
_CONFIG: Final = "config.toml"
_FOLDERS_RULE: Final = 'match = "existing_folder"'  # two lines below its table header


def with_rule(config: str, rule: str) -> str:
    """Insert a rule right above the *Existing folders* rule of a config.toml.

    Args:
        config: The file.
        rule: The `[[classify.rules]]` table to insert.

    Returns:
        The new file; the rule at the end when there is no such rule.
    """
    lines = config.splitlines(keepends=True)
    header = next(
        (at - 2 for at, line in enumerate(lines) if line.strip() == _FOLDERS_RULE),
        len(lines),
    )
    return "".join((*lines[:header], rule, "\n", *lines[header:]))


def _write_config(demo: Demo, text: str) -> None:
    """Replace config.toml in the demo's config volume, owned by the tool's user.

    Args:
        demo: The demo.
        text: The new content.
    """
    command = ["docker", "run", "--rm", "-i", "--entrypoint", "sh", "-v",
               f"{demo.volume('config')}:/config", IMAGE, "-c",
               f"cat > /config/{_CONFIG}"]  # fmt: skip
    # Fixed, trusted arguments; the file comes on the standard input.
    subprocess.run(  # noqa: S603
        command, input=text, text=True, check=True, capture_output=True
    )


def people_story(demo: Demo, shots: Path) -> Captures:
    """Measure, name the largest group on the page, classify with a `person` rule.

    Args:
        demo: The demo library, audited and cleaned.
        shots: Where the screenshots land (PNG).

    Returns:
        The terminals of `people --sample`, of `people` and of the `classify`.
    """
    captures = {"people-sample.txt": run(demo, Command(("people", "--sample", SAMPLE)))}
    container = start_review(demo, ("people",))
    try:
        shoot(demo, Job(f"container:{container}", ("people", NAME)), shots)
    finally:
        captures["people.txt"] = stop_review(container)
    before = read_file(demo, "config", _CONFIG)
    _write_config(demo, with_rule(before, _RULES[demo.locale]))
    try:
        captures["classify-person.txt"] = run(demo, Command(("classify",)))
    finally:
        _write_config(demo, before)
    return captures
