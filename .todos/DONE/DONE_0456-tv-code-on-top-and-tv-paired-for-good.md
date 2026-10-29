# 0456 — The TV's code field on top of the remote when a TV waits; a TV paired for good

- **Priority**: High
- **Batch**: slideshow
- **Depends**: —
- **Status**: DONE (2026-10-29): field on top while a TV waits (`tvWaiting` in the remote state); TVs kept in `/lan/tvs.json`, listed and forgotten on the PC card as **TV**. Captures stale: `docs_screenshots`.
- **Files**: `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/slideshow/screens.py`, `src/media_hygiene/slideshow/door.py`, `src/media_hygiene/services/slideshow_here.py`, `src/media_hygiene/review/lan_phones.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Why

Maintainer, 2026-10-29, on a real phone and TV: after `mh --lan` restarted, the TV showed a
pairing code while the phone's remote already ran the show, and the phone showed nowhere to
type it. The field exists (`#pair`, "The code the TV shows") but sits in the side column,
which a phone puts **below every thumbnail** (`review_side.css.j2`: `#side { order: 2 }`).
And the TV had to pair again only because `mh` restarted: TVs are paired in memory
(`Screens`), phones are paired for good (`phones.json`, 0431).

## What

1. **The code field where it is seen**: on the remote, when a TV waits for its code (the
   server knows: a TV asked `/screen` unpaired in the last minute), the pairing form shows at
   the **top** of the page (above the controls and the thumbnails), on a phone and on the PC;
   once paired, it goes back to its place. Without a waiting TV, it stays where it is.
2. **A TV paired for good**: a TV paired under HTTPS `mh --lan` gets a durable token, kept in
   `/lan/` beside `phones.json` (same rules: a file of `/lan`, atomic save, read back); after a
   restart of `mh` the TV shows the show at once, no code. Forget it as a phone is forgotten
   (the PC's card). Plain HTTP without `/lan`: in memory as today.

## Explicit NON-goals

- No pairing from the TV's side, no new port, no change to the phones' pairing.

## Tests

A TV waiting → the remote's state says so (the form on top); paired → no more; a TV paired,
the server rebuilt from the same `/lan` → still paired; a token not in the file → the code;
the file corrupt → codes again, nothing raised.

## Docs (both languages)

`slideshow.md`: the code on top of the remote when the TV asks for it; the TV stays paired
across restarts. Captures stale: `docs_screenshots`.
