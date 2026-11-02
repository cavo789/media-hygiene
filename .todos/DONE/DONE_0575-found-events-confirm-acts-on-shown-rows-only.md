# 0575 — Events found in your folders: Confirm acts on the rows shown only

- **Priority**: Critical — one click writes every hidden event
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search_events_found.js.j2`, `src/media_hygiene/search/templates/search_events_found.html.j2`, `src/media_hygiene/search/found_desk.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

## Asked (maintainer, 2026-11-02)

Product rule: **an action never touches what is not shown.** It acts on the rows or tiles
visible, or on a set whose size the button states ("every 1 234 found").

Read in the code (2026-11-02, not tried in the app): in `/search` → *🗂 Events* → *N events
found in your folders*, the filter hides rows, *Tick all* / *Untick all* act on the visible
ones only, but **Confirm** (`foundSave` in `search_events_found.js.j2`) posts every box of
`foundList` and `foundRefusedList`, hidden ones included, and they arrive ticked. Filtering on
"Nouvel An" (20 of 196) then Confirm writes the **196** events into `config.toml`; filtering
on "Restaurant", unticking the 40, Confirm refuses those 40 **and** writes the 156 hidden.

## What

1. Confirm posts only the rows shown by the filter; hidden rows stay to decide, untouched.
2. The button says what it does: "Confirm these 20" (`ngettext`), updated as the filter
   changes; disabled when no row is shown.
3. The server answers with what it wrote, read back (already so), and the list: 196 → 176
   after "Nouvel An", → 136 after "Restaurant" (the 40 go to the folded *Not events*).
4. Test: a filtered post leaves the other folders unwritten (route test with a body of the
   shown rows; and a check of the JS that `shown()` builds the body).

## Audit of the other actions (2026-11-02, by reading the templates)

- Only other row filter with actions found: none. `phone_review.js.j2`, `shrink.js.j2`
  ("all" = every draft listed, no filter), `intruders_review.js.j2` (ticked boxes, no filter)
  act on what is shown.
- Tile pages (`pick_grid.js.j2`): Ctrl+A = every tile shown; *every file found* (`pickAll`)
  is the stated exception — it names its count. To confirm while doing this TODO: the count
  shown equals what is posted, and the files set aside are left out (0518).

## Acceptance

- [x] Confirm with a filter writes and refuses only the rows shown (test).
- [x] The button names its count, singular and plural.
- [x] Docs en + fr say Confirm acts on the rows shown; `i18n_update` + French.
- [x] The rule "never act on what is not shown" added to the product rules of
      `.claude/rules/workflow.md` (and the `photo-picking-pages` skill for tiles).

## Status — DONE (2026-11-02)

Confirm posts only the rows the filter shows (proposed + refused lists), labelled
"Confirm these N" (ngettext, `counted`), disabled when nothing is shown. Server unchanged (it
already writes only what the body names). Rule added to `.claude/rules/workflow.md` and the
`photo-picking-pages` skill. Docs: the section lives in `sort/11-name-events-in-the-browser.md`
(en + fr), not in `commands/search.md`. The *Pick all N found* count vs posted check was not
re-read in the browser.
