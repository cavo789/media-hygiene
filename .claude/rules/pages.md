---
paths:
  - "src/media_hygiene/**/templates/**"
  - "src/media_hygiene/review/**"
  - "src/media_hygiene/search/**"
  - "src/media_hygiene/people/**"
  - "src/media_hygiene/person/**"
  - "src/media_hygiene/share/**"
  - "src/media_hygiene/slideshow/**"
  - "src/media_hygiene/places/**"
---

# Served pages and templates — always apply

Every page the tool serves (home, library, people, person, reviews, albums, places, phone,
TV) is one product: the same frame, the same parts, the same gestures. The tests below are
the contract; a new page that fails one of them is a bug, not a case for an exemption.

- ✅ DO: before any UI work on a page of photo tiles, load the `photo-picking-pages` skill
  (`review/templates/pick_*`); before any UI piece at all, find the shared part (`tile_view.*`,
  `pick_who.js.j2`, `combo_list.*`, `undo_toast`, `ask_dialog`, `apply_now`, `home_link.html.j2`,
  the frame's `mhSay`/`mhBusy`/`mhPlaceholders`) and reuse it. A page that needs more adds it
  **to the shared part**, so every page of the kind gets it in the same change
  (`tests/unit/test_same_features_on_pages.py`). ❌ DON'T: a page-local copy or a second
  version "for this page only": two versions drift apart within days.
- ✅ DO: register a page in the frame: `SHELL_PAGES` (`review/page_header.py`), its space and
  rail, the way back home from `home_link.html.j2` (it also carries the `/api/alive` pings),
  `#bar`/`#side` under the measured top bar (`tests/unit/test_page_frame.py`,
  `test_shell_pages.py`, `test_page_headers.py`). An exemption in a test's exclusion list is a
  divergence to justify in the test, never a default.
- ✅ DO: `nonce="{{ page_nonce }}"` on every `<script>` (`review/nonce.py`); the CSP allows
  `'self'`, the fonts, and the one tile host of `places` — no inline handler (`onclick=`), no
  `'unsafe-inline'`, no other host. Loopback `Host` only, `POST` bodies JSON only, the device
  address read from the socket (`Request.peer`), never from a header.
- ✅ DO: one declaration per top-level JS name on a page (`tests/unit/test_page_script_names.py`:
  the scripts of a page share one scope). Templates stay under 400 lines; one over it is in
  `OVERSIZED_TEMPLATES` (`tests/unit/test_page_frame.py`) and may only shrink: split it first,
  in its own step, rendered output identical.
- ✅ DO: the TV's `/screen` page (`slideshow/`) is ES5 only, no regular expressions: a 2012 TV's
  browser runs it (`tests/support/es5.py` checks). Phone or any LAN device: read-only, no
  writing route reachable (`review/lan_paths.py`); hide the write controls instead of showing
  buttons that end on 403.
- ✅ DO: every page that sets files aside or records a choice `clean --decisions` applies
  offers *Apply now* (`ApplyOffer`, the shared `apply_now` template, same place in the bar) once
  something is pending. An action acts only on what is shown, or on a count the button states
  ("Confirm these 20"); hidden rows stay untouched. A file set aside is a soft delete: every
  page, count and action ignores it, without asking.
- ✅ DO: a setting changed from a page is saved where it acts, read back from disk and shown
  (`tests/unit/test_page_settings.py`); a save is never "Saved" from memory. Pages are drawn per
  language and reload after a language change (0644–0647).
- ✅ DO: every user-facing string in a template goes through `_()`; after the change,
  `i18n_update` and the French `.po`. A changed page makes the documentation captures stale:
  say that `docs_screenshots` should run, never run it unasked.
- ✅ DO: a new route is weighed against `tests/measure/pages-budget.md` (`test_pages_budget.py`:
  +30 % warm time on the synthetic library fails); a new verb or page gets its entry in
  `cli/menu_catalog_*.py`, its `documentation/{en,fr}/commands/` page, `nav` of
  `.config/mkdocs/mkdocs.yml` (`test_menu_catalog.py`, `test_docs_commands.py`, `test_docs_site.py`).
- ✅ DO: tests of pages read templates as text: `tests_for.py` does not select them from a `.j2`
  change. After a template edit, run `pytest tests/unit -k "page or shell or home or same_features
  or script_names"` before the gate.
