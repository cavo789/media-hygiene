# 0338 — After "Delete from the phone", the tab goes back to the home page by itself, whatever `mh` wrote it

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/phone_review.js.j2`, `src/media_hygiene/review/templates/home_link.html.j2`, `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/services/launcher_stamp.py`, `src/media_hygiene/cli/templates/mh_phone_free.ps1.j2`, `tests/integration/test_phone_review.py`, `tests/unit/test_launcher_phone.py`

## Why

The maintainer, 2026-10-23, home page → *Make room on the phone*, ticked, pressed *Delete*: the
console ended well —

```text
Téléphone libéré : 466 fichiers supprimés (2.38 Go), chacun vu parti du téléphone et retrouvé entier sur le PC.
👉 Et ensuite : mh history (le passage du téléphone, et ce qu'il a supprimé).
⚠️  Ce mh a été écrit par l'image 0.4.0 (construction fde56c87f64c), celle-ci est 0.4.0 (construction dc93ffa2a001) :
tapez mh update pour le réécrire, avec les mêmes dossiers.
✅ Accueil prêt, ouvrez http://127.0.0.1:8088/ dans votre navigateur. Ctrl+C l'arrête.
```

— but the tab stayed on the page's waiting state ("Switch to the PowerShell window…"): no
refresh, the user believes it is still busy, possibly for a long time.

## Cause (read in the code, 2026-10-23; to confirm)

The page follows the home page back only when it knows it was opened from the home page:
`window.mhAwaitHome` (`home_link.html.j2`) exists only when the server got
`MEDIA_HYGIENE_LAUNCHER_STEPS`, which `mh_phone_free.ps1.j2` passes since d19fb7e (0332:
`if ($global:MediaHygieneRelay) { $page += '-e', '{{ relay }}=1' }`). That line lives in **`mh`
on the user's PC**, written by an older build (the ⚠️ line above): the image was new, the
script was not, so the page took itself for a console run and kept waiting.

## What

1. **Never depend on `mh`'s age for this**: once *Delete* (or *Leave*) is accepted, the page
   always watches its server (as `home_link.html.j2`'s poll: seen gone, then answering) and,
   when the address answers again, goes there — the home page when `mh` brought it back. From
   the console (nothing comes back), after the server is gone it says "Done: see the PowerShell
   window" instead of the endless waiting line.
2. **The waiting state tells progress**, not just "switch to PowerShell": the time elapsed
   against the estimate ("about 4 min" → "2 min of about 4"), so a long wait reads as normal.
3. **A stale `mh` is said where it matters**: a page served by an image newer than the `mh`
   that started it (the build stamp, `launcher_stamp.py`) shows the same ⚠️ line on the page (the
   console's is printed at the end, after the fact); consider whether the home page should
   offer `mh update` in one click (a step that already exists?) — say it, do not build it here.
4. Test the page's behaviour without the relay (the old `mh`): headless Chromium, a mocked
   server going away then answering as the home page: the tab lands there.

## Tests

- Integration/browser: *Delete* accepted, server gone, then a server answering on the same
  address: the tab reloads to it, with and without `mhAwaitHome`.
- The waiting line counts the minutes.

## Docs

The launcher page's section on freeing the phone (both languages): what the tab does after
*Delete*; `docs_screenshots` should run afterwards (not unasked).

## Status — PARTIAL (2026-10-26)

Done: after *Delete* or *Leave* accepted, `follow()` (phone_review.js.j2) always watches the
address (1 s poll, 2 s answer limit, as home_link's): seen gone then answering, or another run
id, the tab goes to `/`, with or without `mhAwaitHome` (an older `mh`). The waiting line counts
the minutes against the estimate (*2 min gone by, of about 4*); once the server is gone it adds
that the PowerShell window says when it is done. Docs both languages.

Left: item 3 (the stale-`mh` ⚠️ line on the page: the build stamp is not passed to the page's
server today; the home page could offer `mh update` — not built); item 4 (headless Chromium
test: no browser test harness in the repo; the rendered script is checked as text instead).
