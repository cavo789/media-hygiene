# 0325 — People page guides the naming: what is left, and the next section to do

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0323, 0324
- **Files**: `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/people/sections.py`, `src/media_hygiene/people/roster.py`, `tests/unit/test_people_naming.py`, `tests/integration/people/`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23: "my current work is to put first names on faces, and I would like
the page's organisation to guide me in it". Today the page shows every section in one order
(read in `people/sections.py`: people with verified faces first, most faces first, each
verified then attributed, then the unnamed groups largest first) and says nothing of what is
left; the work — confirming attributed faces, naming unnamed groups — is scattered between
sections already done.

## What

- A progress line in the top bar, from the state: attributed faces left to confirm (and for how
  many people), unnamed groups left (and their faces), groups ignored; e.g. "To do: 312
  attributed faces (7 people) · 41 unnamed groups (980 faces)". It updates after each change,
  read from the state the server sends back (never counted from memory).
- A **"Next to do"** button and key (e.g. `Tab`-free choice such as `g`; check 0304): moves
  `current` to the next attributed section, then the next unnamed group, skipping verified
  ones, opens it (0323) and focuses the right action (Confirm for attributed, the name field
  for unnamed).
- A view switch "Only what is left" / "Everything": the first hides the verified sections
  (they stay reachable from the people list of 0324).
- Order of the unnamed groups: largest first stays (most faces named per action); say it in
  the page's hint line, so the order is understood.
- After confirming a section, the page moves to the next one to do by itself (the user keeps
  the rhythm `y`, `y`, `y`…), unless the user moved meanwhile.

## Tests

- Unit: the counts of what is left from a `Sections` (attributed faces, people, unnamed groups).
- Integration: "next to do" skips verified sections; after a naming the progress line holds the
  numbers read back from the new state.
- Docs en + fr (the hint line, the key); captures stale → `docs_screenshots`.
