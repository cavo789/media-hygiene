# 0332 — The phone page has "Back to the home page", at the same place as every other page

- **Priority**: Critical
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/review/templates/phone_review.js.j2`, `src/media_hygiene/review/page_header.py`, `src/media_hygiene/review/templates/page_header.html.j2`, `src/media_hygiene/review/templates/home_link.html.j2`, `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/cli/templates/mh_phone_free.ps1.j2`, `tests/unit/test_page_headers.py`, `tests/integration/test_home_page.py`, `tests/integration/test_phone_review.py`

## Why

The maintainer, 2026-10-23, on the page of *Make room on the phone*, opened from the home page:
"how do I go back to the home page? The other pages have a *Back to the home page* button, not
this one. Once again a divergence. All our pages should have the same layout and the same
features, at the same place, where possible and where they apply."

The phone page is left out on purpose today (0248): `page_header("phone_review.html.j2").home`
is false (`test_the_phone_page_keeps_its_own_way_out`), and `test_home_page.py` exempts it from
including `home_link.html.j2` ("ends into `mh phone`, never the home page"). Its only way out is
*Leave everything on the phone*. Leaving that fragment out also leaves out the page's
`/api/alive` pings: the likely cause of the 405 of 0331.

## What

1. **Check first** what `mh` does after the phone step when it was run from the home page: does
   the home page come back on the same port, as after the other steps (0280)? Read
   `mh_phone_free.ps1.j2` and the home step's relay; if not, make it so (the home page is where
   the user came from).
2. The phone page includes `home_link.html.j2` like every other page: the pings (0262), the
   *Back to the home page* link in `page_header.html.j2`, at its usual place. Opened from the
   home page, the link ends the page **as *Leave everything on the phone*** (nothing deleted:
   `POST /api/stop`, nothing printed for `mh`), and the home page comes back. Say it on the
   link's title ("Nothing is deleted from the phone").
3. Opened from the console (`mh phone --free`), no home page to go back to: the link is not
   shown, as on the other pages (`page_header`'s `home` follows how it was opened).
4. Remove the exemptions: `test_the_phone_page_keeps_its_own_way_out` becomes the opposite, the
   phone page leaves the exclusion lists of `test_page_headers.py` and `test_home_page.py`.
5. **Every page, same features at the same place** (the maintainer's rule): list the pages
   still exempted from the shared header parts (the exclusion sets of `test_page_headers.py`
   and `test_home_page.py`: today `lan_pair.html.j2`, a phone not paired yet), and say for each
   whether the exemption still applies; file one follow-up per page that should not be exempt.

## Tests

- `test_page_headers.py`: opened from the home page, the phone page offers the way back.
- Integration: through the real server (`serve_phone_review`), `POST /api/stop` from the link
  ends the page with nothing printed for `mh` (`results == [()]`).

## Docs

The launcher page's section on freeing the phone (both languages): the way back to the home
page; `docs_screenshots` should run afterwards (not unasked).

## Explicit NON-goals

- *Apply now* and coming back to the page after a round (0315).
- The 405 itself (0331), beyond the pings this fragment brings.
