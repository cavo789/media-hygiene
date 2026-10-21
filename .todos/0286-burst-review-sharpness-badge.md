# 0286 — Show each shot's sharpness as a badge on the burst review

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/review/templates/review.html.j2, src/media_hygiene/review/views.py, src/media_hygiene/review/templates/review_compare.css.j2 (or the stylesheet holding the shot number badge), documentation/en|fr (the burst review page and its screenshots)

## Context

On the burst review page (`media-hygiene review`, "Tri des rafales"), the sharpness score is the
figure the maintainer relies on most to keep or set aside a shot, yet it sits in the middle of the
metadata line under each picture (`2268 × 4032 · 4,3 Mo · netteté 1.293 · 2019:07:16 …`, built in
`views.py` as `sharpness {value}`): every time, the eye has to hunt for it. The picture already
carries a number badge (1, 2, 3…, the key that sets it aside); the score should get its own
badge next to it, separate from the number so the two are not confused.

## Acceptance

- [ ] Each shot's picture shows a second badge, next to the number badge but visually distinct
      (e.g. "🔍 1.293" or "netteté 1.293"), readable at a glance on light and dark themes and
      over any picture (opaque background).
- [ ] The sharpest shot of the series stands out in that badge (e.g. bold / ⭐ / accent colour);
      consider showing the share of the best (`share`, already computed: "92 %") as well or
      instead — decide which reads faster, and say so in the commit.
- [ ] When "faces sharpest" decides (`faces`), the badge shows the figure that was compared
      (face sharpness) or says which one it is, so the badge never contradicts the proposal.
- [ ] The sharpness is no longer repeated in the metadata line (or kept there in a lighter
      form — choose one, no duplicate emphasis).
- [ ] Same treatment considered for the other pages that show a sharpness (`near_review`,
      the board view `review_board.js.j2`) — consistent or explicitly left out.
- [ ] Every new string through `_()`, `i18n_update`, French translated; tests of the page updated.
- [ ] Documentation en + fr updated if a sentence describes where the score is;
      `docs_screenshots` to run (captures of the review page change).
