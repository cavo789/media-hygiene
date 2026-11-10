# 0671 — Pages resist hostile names: a test with poisoned file names and EXIF, CSP without `unsafe-inline`

- **Priority**: High
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/review/http.py`, `src/media_hygiene/review/respond.py`, `src/media_hygiene/i18n/templates.py`, `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/home.html.j2`, `tests/support/demo.py`, `tests/support/pages_walk.py`, `tests/unit/`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

Every page builds HTML in the browser from data the library holds: file and folder names,
EXIF fields, album names, tags written by a local AI model, town and landmark names, names
typed for people. *Measured* (2026-11-10, `grep` over the templates): **44** `innerHTML`
sites, each relying on a hand call of `esc(...)`; the policy sent with every page is
`script-src 'unsafe-inline'` (`REVIEW_POLICY`, `review/http.py`), so one forgotten `esc`
runs a script. No test feeds a hostile name to the pages (`grep` over `tests/` for
`onerror=` / `<script>alert`: nothing).

Why it matters here: a script running in the PC's page may call the write routes (set
aside, *Apply now*, save settings) as the user; on a paired phone it reads the library.
The names come from outside: a photo received by mail or WhatsApp, a NAS folder (Linux
allows `<` `>` `"` in names; Windows does not, EXIF and XMP allow anything).

No inline event handler is used (*measured*: zero `onclick=` and the like in the
templates), so a strict policy is within reach.

## Proposal

1. **The test first**: a hostile fixture in the demo tree — a folder and a file named
   `<img src=x onerror=window.__pwned=1>`, the same in EXIF `ImageDescription`, `Artist`,
   `Model`, in an XMP sidecar's keywords, in an album name, a person's name, a tag, a place
   name — then the browser walk opens every page and asserts `window.__pwned` is undefined
   and no CSP violation is reported. Fix what it finds.
2. **CSP with a nonce**: each `<script>` and `<style>` block gets `nonce="…"` (drawn per
   response), the policy becomes `script-src 'nonce-…'; style-src 'nonce-…'` (or `'self'`
   once the shared scripts are files — see the page-weight TODO of the same review). An
   injected `<script>` or `onerror=` then does nothing even where an `esc` is missing.
   Inline `style="…"` attributes: count them first; `style-src-attr` may have to stay.
3. A lint in the tests: an `innerHTML` assignment whose template literal holds a `${…}` not
   wrapped in `esc(`, `icon(`, `number(`… (a short allow-list) fails.

## Acceptance

- [ ] The hostile fixture walk passes on every page, PC and phone doors
- [ ] No `'unsafe-inline'` in `script-src`; the places page's own policy included
- [ ] The lint over the 44 sites, exceptions named

## Where the user gains

Before: 44 hand-escaped sites and a policy that runs any injected script (measured). After:
two independent locks (escaping tested, policy refusing), checked in CI.
