# 0573 — 📁 Move to an event: a plain filing must not write a `[[classify.rules]]` event

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/move_event.py`, `src/media_hygiene/search/move_go.py`, `src/media_hygiene/search/templates/move_dialog.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

Reported by the maintainer on 2026-11-02: one video moved from `C:\Photos\2019\Photos Chloé`
to `C:\Photos\2019\2019-07\Napoleon` with the **📁 Move to an event** dialog of `search`. The
dialog said *"It will be remembered as the event 'Napoleon' (config.toml)."*
(`move_event.foreseen`) and the move wrote, through `move_event.remember_event`:

```toml
[[classify.rules]]
name = "Napoleon"
match = "date_range"
category = "Napoleon"
dates = "2019-07-22..2019-07-22"
```

That was not wanted: it is only a filing, not an event. The maintainer removed the rule by hand.
Each such move pollutes `config.toml` with a one-day `date_range` rule that `classify` will then
apply to every other file of that day. The same dialog also says *"No rule is written"* in its
intro text, which contradicts the sentence below it.

## What to do

- Writing the event rule becomes a choice in the dialog: a checkbox *"Also remember it as an
  event (config.toml)"*, **always unticked by default**, even when the name matches an
  existing event (maintainer, 2026-11-02). Unticked: the move happens, nothing is written
  to `config.toml`, and `foreseen`'s sentence is not shown (or says nothing will be written).
- Ticked: today's behaviour (`remember_event`, read back from disk and shown).
- Make the intro text true in both cases (no "No rule is written" next to a rule written).
- Undo note: a move's `undo` never removed the rule; say so if the box is ticked.

## Tests

- Move with the box unticked: `config.toml` byte-identical after the move.
- Move with the box ticked: the rule is written and read back (existing tests kept).
- Dialog render: the box present, unticked, the sentence follows it.

## Docs

`documentation/en|fr/commands/search.md` (Move dialog section); a `docs_screenshots` run
afterwards (dialog capture changes).

## Status — DONE (2026-11-03)

- `MoveIn.remember` (False by default); the dialog's box *Also remember it as an event
  (events/)*, unticked at each opening; unticked: nothing written, the line says so; ticked:
  the event foreseen, then written and read back, with the undo note. Intro text fixed.
- Tests `tests/unit/test_move_go_remember.py` (tree byte-identical unticked, rule read back
  ticked, the box in the dialog). Docs en + fr; `docs_screenshots` to run.
