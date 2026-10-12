# 0078 — `review --near`: play the re-encoded videos in the page

- **Priority**: Low
- **Batch**: near
- **Depends**: —
- **Files**: `src/media_hygiene/review/http.py`, `src/media_hygiene/review/files.py`, `src/media_hygiene/review/near_views.py`, `src/media_hygiene/review/templates/near_review.html.j2`, `tests/integration/test_near_review.py`

## Context

TODO 0069 added the `review --near` page. For a group of re-encoded videos, it shows no
preview, only a "↗ original" link that downloads the file: `REVIEW_POLICY` in
`review/http.py` has no `media-src`, and the server answers no video media type. Deciding which
version of a video to keep without seeing it means opening two downloads side by side.

## Steps

- [ ] Add `media-src 'self'` to the policy of the near page only (the burst page shows photos).
- [ ] Serve the original of a video with its media type (`video/mp4`, `video/quicktime`,
  `video/x-matroska`…, from a `ContentType` entry, not inline strings), still limited to the
  files of the plan, as the image route is.
- [ ] Support `Range` requests (`206 Partial Content`, `Accept-Ranges: bytes`): without it,
  browsers cannot seek and Safari refuses to play. Stream the file in chunks, never read it whole.
- [ ] `<video controls preload="metadata">` for the kept version and the copy, muted by default.
- [ ] Integration tests: the video route answers the media type, a `Range` request gets `206`
  with the right bytes, a path outside the plan is refused.

## Acceptance

- In `review --near`, both versions of a re-encoded video play side by side, and seeking works.
- The burst review page keeps its stricter policy.
