"""Each face and photo of an answer of `/person` told its name (0714)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.person.names import FaceNames


def tagged(names: FaceNames | None, answer: dict[str, object]) -> dict[str, object]:
    """An answer of the page, each face and photo told its name.

    A photo whose face was said not to be the name of the first (the face chosen) is
    left out: "not him" removes it from the search.

    Args:
        names: The desk; None: the answer as it is.
        answer: `faces` (a photo's) or `files` (a face's photos), each with `key`.

    Returns:
        The same answer, with `named` on each item named, `people`, `writable`.
    """
    if names is None:
        return answer
    for listed in ("faces", "files"):
        items = answer.get(listed)
        if not isinstance(items, list):
            continue
        tags = names.tags([int(item["key"]) for item in items])
        for item in items:
            item["named"] = tags.get(int(item["key"]))
        if listed == "files" and items and items[0]["named"]:
            seed = items[0]["named"]["name"]
            answer[listed] = [items[0]] + [
                item
                for item in items[1:]
                if not (item["named"] and seed and seed in item["named"]["not"])
            ]
    people = [person.name for person in names.settings().person]
    return {**answer, "people": people, "writable": names.config_file is not None}
