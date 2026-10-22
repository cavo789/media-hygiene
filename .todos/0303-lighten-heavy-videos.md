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
