# 0303 — Lighten heavy videos: re-encode, the original in quarantine (undo)

- **Priority**: Medium
- **Batch**: videos
- **Depends**: —
- **Files**: `Dockerfile`, `src/media_hygiene/cli/cmd_shrink.py` (new, name to decide), `src/media_hygiene/services/shrink.py` (new), `src/media_hygiene/scan/tool_run.py`, `src/media_hygiene/actions/`, `src/media_hygiene/config/`, `src/media_hygiene/cli/menu_catalog_*.py`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/`, `documentation/fr/commands/`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: decisions (verb name, codec, quality levels), then a measurement on Windows + Docker Desktop (encoding speed, files played in Windows Photos and on the phone)

## Why

Proposal P6/F1 of 2026-10-17 (`.claude/plans/proposals-2026-10-17-competitors.md`): an estimate
was given, the proposal was not chosen yet, and nothing was filed. The maintainer asked for it
again on 2026-10-22, after `browse` (0301, 0302): the goal is to free disk space on big
videos, especially the ones the children shot, already of lower quality.

Measured on the maintainer's index (2026-10-17, read-only): 1,531 videos = **98.3 GB, 40.8 %** of
240.9 GB. H.264: 1,187 clips, 72.7 GB, 9.7 Mb/s on average. **MJPEG: 325 clips, 24.4 GB**, 12.7 Mb/s
on average (171 under 720 lines, 154 at 720). Estimated (target bit rates assumed, no encode was
run): MJPEG alone 24.4 → 2.8–4.2 GB; all videos 63–74 GB saved.

## What "without loss" can and cannot give (the maintainer's question)

- **`.mov` → `.mp4` without re-encoding (remux, `ffmpeg -c copy`)** copies the image and sound
  streams bit for bit into another container. No loss, but **no gain** either: only the
  container's few kilobytes change. It helps compatibility (a `.mov` holding H.264 is already
  served as `video/mp4`, 0292), never the disk. The page must not suggest it as a saving.
- **Truly lossless re-encoding** (lossless H.264 or FFV1) usually makes a file *larger* than
  the camera's own compressed video: not an option.
- **"Visually identical" re-encoding** is lossy but invisible for most clips. It is where the
  big gain is: MJPEG stores every frame as a separate JPEG, and H.264/AV1 store the changes
  between frames. Estimated 6–9× smaller (see above). For phone videos already in H.264 at
  ~10 Mb/s the gain is much smaller, and a second lossy generation shows. They are left alone
  by default.
- So: no "lossless shrink". The wording must say **"lighter, same visible quality"** or
  **"lighter, smaller picture"**, never "lossless". The verb name follows from that: `shrink`
  is accurate (size goes down, quality may too). Alternatives: `lighten`, `compact`. French
  docs: « alléger les vidéos ». **Maintainer decides.**

## What

- **Two quality levels** (names to decide):
  - *same picture*: same resolution and frame rate, visually transparent quality (x264 CRF ~18
    or the equivalent; to calibrate on real clips). The default.
  - *lighter*: at most 720 lines, a stronger compression (CRF ~23). For the children's clips,
    chosen per folder or per selection, never by default.
- **Smart selection, dry run first** (like `audit` before `clean`): `mh shrink` alone lists the
  candidates with their estimated gain and changes nothing (🔒). The index already has codec,
  bit rate, width, height and frame rate. Bits per pixel per frame
  (`bit_rate / (width × height × fps)`) tells a badly compressed clip (MJPEG, DV, old
  camera MPEG-4) from an efficient one. Candidates: the codecs of a list (`mjpeg`, `dvvideo`,
  `mpeg4`, `msmpeg4*`, `wmv*`, `mpeg2video` to start) or bits per pixel above a threshold. Then a
  `--apply` (or picked in 0302's view, set aside "to lighten": to decide). Thresholds and the
  codec list go in `config.toml` (`[shrink]`), as the reviews usually ask.
- **Keep only a real gain**: after encoding, if the new file is not at least X % smaller
  (setting, 30 % to start), throw it away, keep the original, and remember "not worth it" in
  the index so it is not tried again.
- **Safety, like `clean`**: protected folders are never touched; excluded ones are not even
  listed; `:ro` mounts and a missing `/journal` are refused. Write-ahead journal (`pending` →
  `done`) with the digests of both files. The new file is written beside the original
  (temporary name, same drive), checked, then renamed. The original goes to its drive's
  quarantine (`QuarantineRoute`). `undo` removes the new file (only if its digest matches the
  journal) and brings the original back. Space is freed only by `purge`: say so on the last
  line.
- **Check before keeping**: `ffprobe` on the result: same duration (± 0.5 s), as many audio
  tracks, the frames decodable (reuse `keyframes`).
- **Keep what the file knows**: `creation_time` and Apple's local date
  (`-map_metadata 0`, `-movflags use_metadata_tags` for the mp4 muxer: to check), GPS
  (`location`), rotation; the file's mtime set back to the original's (the dates of
  `classify`/`sort` read it when no metadata exists). Sidecars (`.thm` of old Canon AVI,
  `.xmp`) are renamed along when the extension changes (`.avi` → `.mp4`), so the keep policy's
  "has a sidecar" still pairs them.
- **Stored by path** (workflow rule): the extension changes. List and test what refers to the
  old path: index row (pruned like `clean` does, the new file indexed at once with its facts
  re-read), `decisions.json`, `sort-decisions.json` / `plan.json`, people, albums. And the
  user's moves afterwards (a folder renamed in Explorer).
- **Docker image**: today's `ffmpeg` decodes only (`--enable-encoder=rawvideo`,
  `--disable-swresample`). It needs a video encoder, `aac`, the `mp4` muxer and probably
  `swresample` (PCM sound of old AVI → AAC). Candidates, licences to check:
  - `libx264`: GPL. The image would ship a GPL `ffmpeg` binary next to the MIT code. Check what
    that requires (the pinned sources are already in the build).
  - `libsvtav1`: BSD + AOM patent licence. Smaller files, but not everything plays AV1:
    Windows needs the free "AV1 Video Extension" when it is missing (proposal notes); phones and
    TVs to check.
  - `libopenh264`: BSD (Cisco), lower quality for the size.
  - HEVC: a paid extension on Windows (source in the proposal notes): not chosen.
  Recommendation: H.264 (plays everywhere, including the review pages and the slideshow 0292).
  Measure the image size before and after (`dive_ci`).
- **Time**: re-encoding is slow, and the maintainer's PC suffers under load. Measured: none yet.
  An `mh-measure.ps1` step encodes one 60 s MJPEG clip and one 60 s phone clip at each level
  and writes the seconds and sizes. This gives the time per hour of film. A progress bar with
  the remaining time and Ctrl+C keeping what is done (the journal makes that safe).

## Tests

- Remux not offered as a gain; a clip without enough gain discarded and remembered; protected
  folder untouched; `.avi` → `.mp4` with its `.thm` renamed; mtime and `creation_time` kept;
  `undo` restores and refuses when the new file was changed; interrupted run (pending entry)
  recovered. Synthetic clips only (`ffmpeg` test patterns generated in the test, never real
  videos).

## Docs

A command page in both languages, `reference-commands.md`, `COMMANDS_TOO`, the menu catalog,
mkdocs `nav`. In the clean guide, a step "lighten the heavy videos" after the duplicates, with
the honest wording above.

## Related

0302 (finding the heaviest videos), 0292 (which codecs the slideshow plays), Czkawka 12's Video
Optimizer (proposal notes: SVT-AV1). Compare its choices before calibrating.

## Status — PARTIAL (2026-10-23)

Decisions taken with the maintainer on 2026-10-23: verb `shrink`, H.264 (libx264), the two
levels as proposed (`same` CRF 18, `--lighter` CRF 23 at most 720 lines). Added by the
maintainer during the run: an original set aside by `shrink` must never come back through a
phone import (it is remembered: done, tested).

### Done
- `media-hygiene shrink` (`cli/cmd_shrink.py`, `services/shrink.py`, `shrink/`,
  `actions/shrink.py`, `actions/shrink_sidecars.py`, `actions/not_worth.py`): the list from the
  index alone (codecs of `[shrink] codecs`, or bits per pixel above `bits_per_pixel`; never a
  protected, excluded or backup folder; `--folder`), the gain estimated and said as such;
  `--apply` encodes beside the original under `.media-hygiene.tmp`, proves the result (length
  ± 0.5 s, sound tracks, date and place, frames decode), keeps it only when at least
  `min_gain_percent` % lighter (else a `mark-not-worth` journal mark: never tried again while
  unchanged; `undo` forgets it), moves the original to its drive's quarantine
  (`quarantine-shrunk`, in `REMEMBERED`), renames to `.mp4` with the original's mtime, then
  moves a `clip.avi.xmp` sidecar to `clip.mp4.xmp`. `undo` removes the lighter video while its
  SHA-256 matches, then brings the original back (an edited one is kept, the original comes back
  beside it). The originals' index rows are parked like `clean`'s.
- `[shrink]` settings (`config/shrink_settings.py`, `config.toml`); `CleanSettings` moved to
  `config/clean_settings.py` (settings.py at its cap).
- Dockerfile: x264 built from its `stable` branch pinned by commit, ffmpeg with `--enable-gpl`,
  libx264, aac, mp4 muxer, swresample, the sound decoders of old cameras (PCM, ADPCM, MP3, AC-3,
  WMA) and `dvvideo`. Measured: the `ffmpeg` stage builds; its binary encodes an MJPEG + ADPCM AVI
  and an MJPEG + PCM MOV to H.264 + AAC; it grows from 5.7 MB to 8.9 MB (+3.2 MB, measured on the
  binaries). README / README_FR licences updated (ffmpeg GPL with x264; the image was already
  GPL as a whole through x265).
- Phone import: `known_of` sees the original as set aside (tested); `clean` sets a copy that came
  back aside again (tested).
- Docs: `commands/shrink.md` (en, fr), `reference-commands.md`, mkdocs `nav`, `COMMANDS_TOO`, the
  menu catalog (clean stage, "Go further", icon `film`), a pointer in `clean/09`.
- `tests/measure/mh-measure.ps1` step 34: two of the maintainer's videos encoded at both
  levels (time, size, seconds per minute of film), the real `shrink --apply` on a copy, and the
  playback questions (Windows, phone).

### Not done
- The measurement on Windows + Docker Desktop (step 34 of `mh-measure.ps1`): encoding time per
  minute of film, real sizes, playback in Windows Photos and on the phone.
  **Reason:** only the maintainer's machine can run it; it calibrates `_SAME_BITS` /
  `_LIGHTER_BITS` of `shrink/estimate.py` (estimated today) and maybe `same_crf`.
- The lighter video is not indexed at once: the next audit reads it (its folder's listing is
  forgotten so it is read again).
  **Reason:** kept simple; indexing needs the audit's probe and fingerprint pipeline.
- Paths stored elsewhere are not rewritten when `.avi` becomes `.mp4`: an album's entry, a
  `decisions.json` choice, a classify `plan.json` row naming the original now name a file in the
  quarantine (each feature already says "missing" for a file gone).
  **Reason:** a follow-up worth its own TODO (rewrite or follow by `former_names`); measured
  rarely relevant for old MJPEG clips (estimated: few are in albums).
- A "to lighten" pick in 0302's heaviest view, and a dedicated clean-guide step: the command page
  and a pointer in `clean/09` instead.
  **Reason:** scope; the CLI's `--folder` covers the choice per folder.
- `docs_screenshots` and `e2e` not run (image build, heavy): the `--help` captures of the new page
  were written from the CLI by hand.

### Measured on the maintainer's PC (2026-10-23, `mh-measure.ps1` step 34)
- `shrink` on C:\Photos lists 344 videos, 23.0 GB (the estimate then said 2.9 GB after: far too
  optimistic, recalibrated below).
- Two Panasonic MJPEG 1280x720 clips with PCM sound (215 s, 574.8 MB; 43 s, 117.5 MB): default
  level 69 % and 66 % of their size, `--lighter` 29 % and 26 %; 10.5 and 8.1 s per minute of
  film, 16 threads of 32 (the "default" was then CRF 18, "--lighter" CRF 23 on these
  720-line clips). Plays in Windows and on the phone with its date; no visible difference at
  either level (the maintainer's eyes).
- Found and fixed: the final rename used `renameat2` alone, refused on Docker Desktop's mount
  (EINVAL): the original went to the quarantine and the lighter video stayed under its
  temporary name. Now `move_no_replace` (link, else proven copy), tested by a run without
  `renameat2`. The result line counted the originals set aside, not the videos replaced: fixed.
- At CRF 18 the result spends about 0.55 bit per pixel (30 fps assumed), above
  `bits_per_pixel`: a video written by `shrink` is never a candidate again (journal `shrunk`
  lines, like the not-worth marks).
- Estimated for the 23.0 GB listed (the two clips' ratios applied to all): CRF 18 about
  15.5 GB after (7.5 GB freed), CRF 23 about 6.2 GB after (16.8 GB freed); at 8 to 11 s
  per minute of film, an estimated 147 min of film takes 20 to 26 min to encode.
- Decided by the maintainer (2026-10-23): CRF 23 by default (`same_crf`), since CRF 18 gained
  only a third (close to `min_gain_percent`) with no visible difference; `--lighter` keeps
  CRF 23 and only fits the picture into 720 lines. One estimate now: `_BITS` 0.22.
- Rerun after the fix (2026-10-23, `measures-20261023-1238`, image `sha256:9cf835f2…`): the
  real `shrink --apply` on a copy of the 215 s clip ran in 55.4 s, 574.8 MB -> `P1050240.mp4`
  167.5 MB (-71 %, 407.3 MB saved, as the line says), the original's modification time kept, no
  temporary file left, the original in the quarantine: the link/copy move works on Docker
  Desktop's mount (measured). The estimate now says 22.9 GB -> about 6.1 GB after, for 341
  videos (the measured ratios, 26-29 %, give 6.0-6.6 GB). Plays in Windows and on the phone,
  no visible difference (the maintainer's eyes).

## Inbox (2026-10-27)

- Paths stored elsewhere when `.avi` becomes `.mp4` → 0418 reusing the rewrite of 0382 (done for sort/undo). The not-indexed-at-once item, the *to lighten* pick and the clean-guide step: kept as they are. The measure is done (step 34, 2026-10-23); `docs_screenshots` remains to run. Closed to DONE (maintainer, 2026-10-27).
