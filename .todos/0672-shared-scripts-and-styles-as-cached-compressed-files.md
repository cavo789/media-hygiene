# 0672 — Pages lighter: shared scripts and styles as cached files, text answers compressed

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/review/respond.py`, `src/media_hygiene/review/http.py`, `src/media_hygiene/review/home_assets.py`, `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/i18n/templates.py`, `tests/unit/`
- **Needs maintainer**: the load time of `/library` on the phone over Wi-Fi, before and after (a step of `mh-measure.ps1` or a stopwatch)

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

Every page carries all its JavaScript and CSS inline and is sent `Cache-Control: no-store`,
uncompressed. *Measured* (2026-11-10, devcontainer, demo tree, `curl` on the PC's door):

| Page | Sent | of which JS | of which CSS | gzip -9 |
|---|---|---|---|---|
| `/` (home) | 200,262 B | 128,776 | 52,086 | 52,493 B (−74 %) |
| `/library` | 324,792 B | 217,206 | 50,850 | 85,718 B (−74 %) |
| `/api/state` | 43,989 B | — | — | not measured |

On the PC's loopback the transfer is nothing (0.5 ms *measured*): the cost there is the
browser parsing and compiling 130–220 KB of script on **every** navigation, never cached
(*estimated* tens of ms on a laptop — to measure with the browser's performance trace
before ranking higher). On a phone the bytes count too: 325 KB over Wi-Fi and a TLS
connection per request (see the keep-alive TODO of the same review).

## Proposal

- The shared scripts and styles (`pick_*`, `page_frame`, `shell`, `theme`, `keys`) rendered
  once per language at server start, served as `/assets/app-<hash>.js|css` with
  `Cache-Control: private, max-age=31536000, immutable` (the hash in the name changes with
  the image or the language); the page keeps inline only its data (`TEXTS`, the state) as a
  JSON block. The browser then compiles the shared code once.
- `Content-Encoding: gzip` for HTML, JSON, JS, CSS over 1 KB when the browser accepts it
  (`gzip` of the standard library, level 5 or 6; pre-compressed once for the asset files).
- Goes with the strict CSP of the hostile-names TODO: files allow `script-src 'self'`.
- Keep the one-file reports as they are (they must open from the disk, without a server).

## Acceptance

- [ ] Bytes sent for `/` and `/library`, first visit and second visit, before / after, in
      the PR (*measured* the same way as above)
- [ ] Parse + compile time from a headless Chromium trace, before / after
- [ ] A language change (0644) still applies live: the asset name changes with the language

## Where the user gains

Estimated from the measures above: second and later page loads send about 325 KB → under
25 KB compressed for `/library` (the data only), and the 217 KB of script is compiled once
per session instead of once per page.

## Decided (2026-11-11, maintainer, review of the iterate of 2026-11-10)

- Once the scripts and styles are files (this TODO), drop `'unsafe-inline'` from `style-src`
  too (0671, commit c17741ae, kept it for 12 `style="…"` attributes and the styles scripts
  set): move those attributes into classes, and say how many are left if any.
