# 0542 — Pick bar: buttons styled by role, the destructive one apart, "Move…" as visible as the rest

- **Priority**: High
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/pick_grid.css.j2`, `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `.claude/skills/photo-picking-pages/SKILL.md`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

On the search page with 16 files picked: "why do the buttons get a dark brown background but not
the *Event…* button? More than once I nearly clicked *Set aside* instead of *Move*, which is not
visible enough."

## Why it happens (read in the code, 2026-10-30)

- `pick_grid.css.j2`: every `button` is filled (`background: var(--accent)`); `button.plain` is
  an outline. The fill means "a button", not "the main action": *Set aside*, *Apply* are filled;
  *Invert*, *Share*, *Send* are outlines.
- `search.html.j2:345`: *Event…* (`#moveOpen`) is `class="plain"` and in its own `<p id="moveBar">`,
  so it wraps to a second line, under *Set aside*, in the weakest style.
- *Set aside* is the destructive action and wears the same fill as the constructive *Apply*:
  nothing tells them apart but the emoji. The eye goes to the filled button just above where it
  looked for *Move*.
- The label says *Event…* (📂) while the maintainer thinks of it as *Move*: the verb is missing.

## To do

1. Three roles, written once in `pick_grid.css.j2`, used by every pick page (skill contract):
   - **primary** (filled accent): the page's main constructive action — *Apply now*, and on
     search the move to an event once files are picked;
   - **secondary** (outline, today's `plain`): invert, share, send, album ±;
   - **danger**: *Set aside* — a red ("danger") **background** (confirmed by the maintainer,
     2026-10-30; the red already used for refusals, 0503), never the accent fill, with a gap
     separating it from the others (end of its group).
2. Search: *Event…* back in the same line as the other actions (no own `<p>`), labelled with the
   verb: "📂 Move to an event…" / « 📂 Déplacer vers un événement… ».
   **Order (maintainer, 2026-10-30)**: the move is the button used most, so it comes **first**
   in the actions, right after the count; *Set aside* goes **last** in the bar, far from it.
   On the other pick pages, the same rule: the page's most used action first, *Set aside* last.
   The bar's start comes from the shared `pick_acting.html.j2`: give it a slot (block or
   variable) for the page's first action, and move `#setAside` to the end of the bar there.
3. Check the other pick pages (browse, reviews, phone, intruders) for the same mix; one look on
   all of them (memory *same features on every page*).
4. Skill `photo-picking-pages`: add the roles table (which bar button gets which role).
5. Both languages' docs; captures are stale → say `docs_screenshots` should run (not run unasked).

## Done when

- Set aside is never filled with the accent colour on any pick page; a test reads the rendered
  bar of each page and checks the class of `#setAside`, `#moveOpen`, *Apply now*.
- On search, *Move to an event…* is the first action of the bar, *Set aside* the last.
