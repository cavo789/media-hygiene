# 0663 — One in-page *ask* dialog replaces the 11 `window.confirm` left

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/undo_toast.html.j2`, `src/media_hygiene/review/templates/phone_review.js.j2`, `src/media_hygiene/review/templates/shrink.js.j2`, `src/media_hygiene/review/templates/quarantine_purge.js.j2`, `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/share/templates/album_edit.js.j2`, `src/media_hygiene/search/templates/events_rule.js.j2`, `src/media_hygiene/search/templates/events_choice.js.j2`, `src/media_hygiene/places/templates/places.html.j2`, `tests/unit/test_undo_toast.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

0521 (PARTIAL) replaced three confirmations by the Undo toast. *Measured* (`grep
window.confirm` over the templates, 2026-11-10): **11** native `window.confirm` remain, in 8
templates — phone page (2), shrink (1), quarantine purge (1), albums (2), album edit (1),
event rules (1), event choice (1), places (2). A native box has the browser's look and
language, names the address (`127.0.0.1:8088 says`), cannot show a count in bold, a
thumbnail or the undo line, and its buttons are *OK / Cancel* whatever is asked.

## Proposal

- One shared template (`ask_dialog`, a `<dialog>`): `window.mhAsk({title, lines, yes, no,
  danger})` returns a promise; the buttons carry the verb (*Purge 124 files*, never *OK*),
  the safe choice has the focus, Esc cancels, the roles of 0542 (danger = red).
- Rule, written in the `photo-picking-pages` skill and the frame's test: what can be undone
  gets the **Undo toast** (no question); what cannot (purge, freeing a phone, deleting an
  album's links) gets the **ask dialog** with what is lost said in one line.
- `tests/unit/test_undo_toast.py` already lists every confirmation with its reason: it ends
  with zero `window.confirm` / `alert` in the templates.

## Acceptance

- [ ] No `window.confirm`, `alert` nor `prompt` in any template (test)
- [ ] Each of the 11 sites: toast or dialog, with the reason in the test's table
- [ ] Headless Chromium: Esc and the safe button never run the action
- [ ] FR translations; `docs_screenshots` should run

## Where the user gains

Before: 11 native boxes (measured), 2 looks for the same question. After: 0; every question
looks the same, in the user's language, with the count and what is lost.
