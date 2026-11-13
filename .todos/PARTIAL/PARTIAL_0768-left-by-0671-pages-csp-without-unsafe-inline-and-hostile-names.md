# 0768 — What 0671 left: Pages resist hostile names: a test with poisoned file names and EXIF, CSP without `unsafe-inline`

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `.todos/DONE/0671-pages-csp-without-unsafe-inline-and-hostile-names.md`, `src/media_hygiene/review/http.py`, `src/media_hygiene/review/respond.py`, `src/media_hygiene/i18n/templates.py`, `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/home.html.j2`, `tests/support/demo.py`

Split from section 0671 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0671-pages-csp-without-unsafe-inline-and-hostile-names.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The hostile fixture in the demo tree (folder/file/EXIF/XMP/album/person/tag/place names)
- JSON answers are not checked with hostile data (served `application/json` + `nosniff`,
- The hostile fixture walk passes on every page, PC and phone doors
- No `'unsafe-inline'` in `script-src`; the places page's own policy included
- The lint over the 44 sites, exceptions named

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- *No `'unsafe-inline'` in `script-src`*: already done by 0671 (nonce policy, places page
  included; `test_no_policy_allows_inline_scripts`). Closed.
- *The lint over the 44 sites, exceptions named*: already done by 0671
  (`tests/support/html_sinks.py`, `EXCEPTIONS` in `tests/unit/test_hostile_names.py`). Closed.
- JSON answers with hostile data: `test_a_json_answer_carries_a_hostile_name_as_data` — a
  `json_response` holding the hostile name, written on the wire, is `application/json`,
  `nosniff`, nonce policy, and parses back to the same string.

### Not done
- The hostile fixture in the demo tree (folder/file/EXIF/XMP/album/person/tag/place names),
  walked in the browser on every page, PC and phone doors, asserting `window.__pwned`.
  **Reason:** the browser walk needs Docker + Playwright (CI e2e only, not runnable here), and
  adding names to the demo tree shifts counts many tests assert; the server-side rendering test
  and the lint already cover templates and scripts. To do as a CI-side change with the demo's
  counts updated in the same commit.
