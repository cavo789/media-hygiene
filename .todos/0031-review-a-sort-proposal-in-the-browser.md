# 0031 — Review a sort proposal in the browser, category by category

- **Priority**: Low — decide after using the HTML report of 0027
- **Batch**: review-ui
- **Depends**: 0027, 0029
- **Files**: `src/media_dedup/review/`, `src/media_dedup/services/reviewing.py`, `src/media_dedup/report/decisions.py`, `src/media_dedup/classify/workbook/`, `documentation/en/`, `documentation/fr/`

## Context

The Excel workbook (0027) is good for renaming in bulk, not for *looking* at photos. The static
HTML report of 0027 already shows thumbnails per category. A keyboard-driven page, like the
burst review (`review`, 0004), could go further: walk through the "to check" band, accept a
category, send a photo elsewhere or to "manual".

## Proposal

- Reuse `review/http.py` and the preview route. Add a session and a page for sort proposals.
- Decisions go to the decisions file under a new `sorts` key, next to `pairs` and `bursts`.
- `sort` applies them on top of the workbook. Precedence: page decision > workbook, and both
  are reported.
- Decide first whether the HTML report plus the workbook's "confirm" column (0027) is enough;
  close as unneeded if so.

## Acceptance

- [ ] Decision recorded (build / unneeded) after a real classify run.
- [ ] If built: keyboard-only walk through the "to check" band; decisions saved at each choice
      and applied by `sort`; documentation en + fr.
