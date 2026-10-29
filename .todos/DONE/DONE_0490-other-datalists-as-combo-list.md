# 0490 — The other datalists as the shared combo list

- **Priority**: Low
- **Batch**: search
- **Depends**: 0487
- **Files**: `src/media_hygiene/search/templates/combo_list.js.j2`, the templates holding `albumNames` (album bar), `names` / `whoList` (people), `categories` (`search_events_dialogs`)

0487 replaced the move dialog's native `<datalist id="moveNames">` with `comboList()`
(`combo_list.js.j2`, shared with Path contains: a list attached under the field, full width,
the page's font, counts, ✕, keys). Four native datalists remain, still drawn by the browser as
a small detached tooltip: `albumNames`, `names`, `whoList`, `categories`.

- Include `combo_list.js.j2` (and the `.comboBox/.comboList/.comboClear` CSS) where each
  lives; a field keeps accepting a value not in the list.
- Some are on other pages: share the CSS rather than copy it (duplicate-code hook at push).

Done when: no `<datalist>` left in the search/people pages, their tests pass, a browser check.
