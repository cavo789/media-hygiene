# 0624 — *More keys* opens under the shell's vertical menu: its left part is hidden

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/keys.css.j2`, `src/media_hygiene/review/templates/shell.css.j2`, `src/media_hygiene/search/templates/search.html.j2`

## Problem

Seen by the maintainer on the search page (screenshots, 2026-11-06). The ⌨ Keyboard panel is
right when closed. Once *More keys* is clicked, the floating table starts under the vertical
menu of the shell: the left column (the keys themselves) is cut, so the reader sees what each
key does but not which key it is. The panel is useless in that state.

## Likely cause (read in the CSS, not yet checked in a browser)

`keys.css.j2` places the opened list with `position: fixed; left: 16px` (0463). A fixed box
is placed against the window, and it ignores the `padding-left: var(--mh-shell-w)` that
`shell.css.j2` gives the body of a page in the shell (`html.mh-shelled`). 16px therefore falls
inside the menu, whose width is `--mh-shell-w`. Its width
`min(26rem, calc(100vw - 32px))` ignores the menu too.

## Fix

- Start the box after the menu: `left: calc(var(--mh-shell-w, 0px) + 16px)`, with `0px` for a
  page outside the shell; check that the variable is defined where `keys.css.j2` applies.
- Subtract the menu from the width, so the box does not overflow on the right of a narrow window.
- Keep what 0463 wanted: floating, non-modal, Esc closes it, the search form stays on screen.

## Check too

- `#folders[open] > #tree` in `search.html.j2` has the same `position: fixed; left: 16px`, and
  its width has the same formula: the *My folders* tree probably has the same defect
  (not reproduced). Fix it the same way if so.
- The panel is shared (`page_frame.html.j2`): check one other page with *More keys* in the
  shell, and one outside it if any, with the menu folded and unfolded if its width changes.
- The *🗂 Events* tab, whose keys make the list longest (`search_events_keys.html.j2`): the
  first and last rows stay reachable (`max-height: 70vh`, scroll).

## Done when

- On the search page, every row of *More keys* is entirely visible, keys included, next to the
  menu, at the maintainer's window size and on a narrow window.
- A test holds the rule, at the level the existing template tests can reach (the `left` of the
  opened box takes the menu's width into account).
