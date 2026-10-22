# 0299 — People page: "Frédérique ✓" (verified) and "Frédérique" (attributed), checked 60 at a time

- **Priority**: High — the maintainer asked for it (2026-10-22): names given by likeness are not told apart from the ones they checked
- **Batch**: people-page
- **Depends**: —
- **Files**: `src/media_hygiene/people/sections.py`, `src/media_hygiene/people/views.py`, `src/media_hygiene/people/roster.py`, `src/media_hygiene/people/templates/people.html.j2`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`, `tests/unit/test_people_naming.py`, `tests/integration/people/test_people_names.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

## Why

When a group is named, only the faces shown (`SHOWN = 60`, spread over the group,
`people/views.py`) become confirmed references in `config.toml`; the others of the group
get the name by likeness (`How.ASSIGNED`, `people/naming.py`). Today the page mixes both
under one "Frédérique" section (`sections_of`: every face of every group holding a
confirmed face), and suggestions ("Frédérique?") are a third place. The maintainer wants
to **see** which faces they validated — like a "Verified" badge — and to check the rest in
batches instead of unfolding hundreds of faces at once (error-prone).

## What

Per person, two sections instead of one (plus the suggestions):

| Section | Holds | × on a face | Main action |
|---|---|---|---|
| **Frédérique ✓** (verified badge on the heading and on each face) | her confirmed faces (`How.CONFIRMED`) | not her: `reject` (out of `faces`, into `rejected`) — exists | none |
| **Frédérique** (attributed) | what the tool thinks is her, not confirmed: the other faces of her groups and the suggestion groups ("Frédérique?" merges into it), minus `rejected` (commit c7e1622) | not her: `reject` | "Yes, these N are Frédérique": the faces shown become confirmed and move to ✓; the next 60 show |

- An empty attributed section is not shown.
- The attributed section shows at most `SHOWN` faces at a time (paging, not "and N more
  faces"); the confirm button sends exactly the faces shown minus those taken out (×).
- The unnamed groups ("Group 24") keep today's behaviour.
- Names in the user's words: "verified" / "attributed" (FR: "vérifié" / "attribué"); the
  maintainer dislikes "attributed" as a hidden notion — it must be visible, not explained.
- Keyboard: `y` confirms the attributed faces shown.

## Open points to settle while implementing

- Faces of her group that are `NOBODY` (below `similarity` from every reference): today
  they show under her; keep them in "attributed" (same cluster), say it in the docs.
- A face confirmed for Manon but clustered in Frédérique's group: shown under Manon ✓ only.

## Done when

- Unit test of the sections: confirmed / attributed / suggestion merge / ruled out / empty
  attributed hidden.
- Integration test (`tests/integration/people/`): name a group, confirm the attributed
  page, read `config.toml` back: the faces moved to `faces`; × in either section → `rejected`.
- Both languages of `reference-people.md` and `commands/people.md` updated; `i18n_update`.
- Say that `docs_screenshots` should run (the people page capture changes).
