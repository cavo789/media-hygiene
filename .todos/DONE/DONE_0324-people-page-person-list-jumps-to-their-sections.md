# 0324 — People page: people in alphabetical order, and a list to jump straight to someone

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0323
- **Files**: `src/media_hygiene/people/sections.py`, `tests/unit/test_people_naming.py`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/people/roster.py`, `tests/integration/people/`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23: to name people they want to pick a person (e.g. "Papy") from a list
— in a left column or as a filter in the top bar — and land directly on their group. Today the
page is one long column (`<main id="groups">`); the order is not alphabetical (read in
`people/sections.py`): people with verified faces first, then by most faces (verified +
attributed), each verified then attributed; then the unnamed groups, largest first. Finding a
given person means scrolling.

## What

- **Sections in alphabetical order of the person** (maintainer, 2026-10-23: "it would be
  illogical to put Papy first"): `sections_of` sorts the people by folded name
  (`people/folding.py`), no longer by "verified first, most faces first"; each person stays
  verified then attributed; the unnamed groups stay last, largest first. Update the docstring
  of `sections_of`, the module docstring and the page's hint line. The work left is found by
  0325 ("next to do"), not by the order.
- A people list, alphabetical (folded compare: `people/folding.py`, so `Chloé` sorts with
  `chloe`), each entry with its counts: ✓ verified faces, faces attributed still to confirm.
  An entry with attributed faces left is marked (it is work to do).
- Placement: a left column on a wide screen; on a narrow one (phone width), a filter field in
  the top bar (`<header>`) with the same list as suggestions. Typing filters the list
  (folded compare, substring).
- Choosing a person scrolls to their first section, makes it `current`, opens it if folded
  (0323), and its attributed section too. A "show only this person" toggle hides the other
  sections until cleared (Esc).
- Last entries of the list: "Unnamed groups (n)" jumping to the first group nobody is given.
- The list is redrawn from each new state (after a naming, a person appears or their counts
  change); the chosen filter survives the redraw.
- A key to reach the list/filter (e.g. `/` or `p`; check against existing keys and 0304).

## Tests

- Integration: the list holds every name of `state.people` with sections, sorted folded;
  choosing one makes its section current; the filter survives a naming.
- Docs en + fr; captures stale → `docs_screenshots`.
