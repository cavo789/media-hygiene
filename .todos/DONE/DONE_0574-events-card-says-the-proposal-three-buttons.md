# 0574 — Events card: say where the files go, three buttons, the bar's gestures

- **Priority**: High
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search_events.html.j2`, `src/media_hygiene/search/templates/search_events.js.j2`, `src/media_hygiene/search/events_choose.py`, `src/media_hygiene/review/templates/pick_keys_more.html.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

## Asked (maintainer, 2026-11-02)

In `/search` → *🗂 Events*, the card of an event (copied from `review-sort`, 0437) is not
understood: a full-width box "F" over an empty field, "Name of the event E", and six buttons
(*Sort this event now*, *Remember as a rule*, *Send to another folder (O)*, *Leave where they
are (S)*, *Leave the whole event where it is (Shift+S)*, *Take back the choice made here (T)*)
whose differences nobody can guess. The bar above already has *Event…* (`move_go`): two
gestures for one job.

What the maintainer wants: see the proposal, accept it in one click and go to the next event;
*Event…* only when the proposal is wrong.

## What

1. **The proposal as one sentence** at the top of the card, with the right plural:
   "This file will go to `C:\Photos\2019\2019-07-11 …`" / "These 10 files will go to …"
   (`ngettext`, the host path as the user knows it). When nothing is proposed, say so and
   point to *Event…*.
2. **Three buttons**, in this order:
   - **Sort here now** (today's *Sort this event now*, M): moves the event's files to the
     proposed folder, journaled, then shows the **next** event to decide.
   - **Another folder…**: opens the same dialog as the bar's *Event…* (the picked photos, or
     the whole event when none is picked). Replaces the folder field (F), the name field (E)
     and *Send to another folder* (O).
   - **Do not sort this event** (today's Shift+S): it stays where it is, counted as decided.
     Its title says that skipping an event (→) is *not* this: a skipped event stays to decide
     and a later `sort` would still move it.
3. **Undo my choice** (T) shown only when the event holds a saved choice.
4. *Leave where they are* (S, the picked photos left out of the move): drop it from the card
   (setting a photo aside or picking only the others covers it), or move it into the
   *Another folder…* dialog — decide while doing it; say which in the commit.
5. *Remember as a rule* stays, as a plain link under the buttons (it is not a sort action).
6. Shortcut letters leave the labels and go to the keys panel (`pick_keys_more.html.j2`); the
   `<kbd>F</kbd>` box rendered as a full-width bar disappears with the field.
7. Docs en + fr (search command page, sort step 11) rewritten for the new card; i18n.

## Acceptance

- [ ] The card opens with the one-sentence proposal, singular and plural right (test).
- [ ] Sort here now moves then shows the next event to decide (test on the route + JS order).
- [ ] Another folder… opens the bar's *Event…* dialog, no second folder/name form on the card.
- [ ] Do not sort this event saved and read back; Undo my choice only when a choice exists.
- [ ] Set-aside files never counted in the sentence nor moved (0518 rule).
- [ ] Docs en + fr, keys panel, `i18n_update` + French; `docs_screenshots` to run (captures
      of the Events tab change).

Related: 0523 (one-click album/TV buttons on the same card) — keep its button below these three.

## Decided (2026-11-02)

By the maintainer, review of the 2026-11-02 iterate: since 0572 the Events tab lists events built
from the index and hides the card's folder and name fields and its six buttons. This TODO is
**rewritten for that index-based card**: before coding, read what the tab shows today and apply
the goal above to it (say in one sentence where the files go, at most three buttons, the bar's
gestures). The plan-based card does not come back.

## Status — DONE (2026-11-03)

- The card of an index event (`#spanChoice`, `search_events_span_card.js.j2`): one sentence
  from the move view (`goes_said`, ngettext, host path; set-aside files left out by
  `_picked`), then **Sort here now** (the move, journaled, the list read again, the next
  event to decide), **Another folder…** (the bar's *Move to an event…*, the whole event when
  nothing is picked), **Do not sort this event** (content ids in `/config/events/left.toml`,
  read back, `⏸` in the list; `POST /api/events/left`, `span_left.py`); **Undo my choice**
  only when the event is left; *Remember as a rule* a link opening the rule dialog on the
  event's days.
- Point 4 decided: *Leave where they are* (S) dropped — picking only the others (or setting
  them aside) covers it.
- Keys in the ⌨ panel (`search_events_keys.html.j2`): N/P, U, M, O, Shift+S, T, ⌫.
- Docs en + fr (`commands/search.md`, the `sort/11` note); `docs_screenshots` to run.
- Not done: no browser test (syntax checked with `node --check`); the plan-based templates
  stay hidden (0572's follow-up).
