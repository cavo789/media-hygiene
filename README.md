# media-hygiene

Clean, sort and explore the photos and videos spread over several folders and disks — from one
`docker run`, on Windows (PowerShell) or WSL. Everything runs on your computer, and every change
is journaled and can be undone.

- **Clean the duplicates**: identical copies, resized or recompressed ones, burst series.
- **Sort**: a tidy tree proposed by date, event, place (GPS, offline), subject (a local vision
  model) and person, that you correct before anything moves.
- **Find the people**: the faces are found and grouped on your computer; name them once, then
  find someone's photos by name and sort them by person, without a photo server such as Immich.

[![Docker Hub](https://img.shields.io/docker/v/cavo789/media-hygiene?sort=semver&label=Docker%20Hub)](https://hub.docker.com/r/cavo789/media-hygiene)
[![Pulls](https://img.shields.io/docker/pulls/cavo789/media-hygiene)](https://hub.docker.com/r/cavo789/media-hygiene)

The image: [**cavo789/media-hygiene** on Docker Hub](https://hub.docker.com/r/cavo789/media-hygiene) (amd64 and arm64).

🇫🇷 [Version française](README_FR.md)

![An audit in the terminal: 83 media files scanned, 20 groups of identical files, 32 extra copies, 14.0 MB to free, then the folders sharing identical files, each pair saying which folder keeps its copies](documentation/en/images/terminal-audit.webp)

## Quick start

With Docker installed ([how to install it](https://cavo789.github.io/media-hygiene/start/00-install-docker/), on
Windows or Linux), one command audits a folder. In **PowerShell**:

```powershell
docker run --rm -it -v "C:\Photos:/data/c/Photos:ro" cavo789/media-hygiene audit
```

In a **WSL** (or Linux) terminal, the same folder is written `/mnt/c/Photos`:

```bash
docker run --rm -it -v "/mnt/c/Photos:/data/c/Photos:ro" cavo789/media-hygiene audit
```

It lists the duplicate and broken photos and videos of `C:\Photos`, and changes nothing: `:ro`
(read-only) makes Docker itself forbid any write. The first run downloads the image [from Docker Hub](https://hub.docker.com/r/cavo789/media-hygiene) by itself.
[Your first audit](https://cavo789.github.io/media-hygiene/start/01-first-audit/) explains this command and its result, part
by part.

**Then, `mh`.** One line writes an `mh` command that knows your folders: `mh` alone opens a menu
that proposes the next step, and `mh shortcut` puts a *Media Hygiene* icon on your Desktop
([Clean in short, step 0](https://cavo789.github.io/media-hygiene/clean/quick-guide/)).

What it finds:

- **Exact duplicates** — same size and same SHA-256, across folders *and* disks (`C:` and `D:`
  in the same run).
- **Broken files** — empty files, images and RAW files that cannot be decoded (truncated JPEG,
  …), videos that cannot be opened.
- **Orphan sidecars** — a sidecar file (`.xmp`, `.aae`, `.thm`) left without its photo.
- **Burst series and near duplicates** (re-encoded videos included) — shown side by side in an
  HTML report; `review` then lets you choose the best shots of each burst [with the keyboard, in your browser](https://cavo789.github.io/media-hygiene/clean/10-review-bursts/).

Then, when you decide to, `clean` sets the extra copies and the broken files aside; bursts and
near duplicates only when you ask for it.

## Your photos are safe

**We guarantee it: these commands never modify, move nor delete a photo or a video** —
`audit`, `crosscheck`, `classify`, `review`, `review-sort`, `places`, `inventory`, `tags`,
`search`, `people`, `history`, `reports`, `config`, `status`, `launcher`. They only write their own files (reports, cache, `config.toml`). Run them
with your folders mounted `:ro`: then the operating system itself forbids any change.

**The commands that act never erase anything.** `sort` moves files (on one disk, a simple
rename: no copy, no space used), `album` adds second names, `xmp` writes small `.xmp` sidecars next to the photos, `clean` moves the duplicate copies
to the quarantine after comparing them byte for byte with the copy kept, `undo` puts things
back. Never over another file, every step journaled, all undoable.

**Only `purge` erases**: the quarantine, for good, after asking you (and `clean --delete`, if
you ask for it: the copy kept stays). More in
[how your photos stay safe](https://cavo789.github.io/media-hygiene/reference-safety/).

## Documentation

The [documentation](https://cavo789.github.io/media-hygiene/) walks you through, one step at a
time, with a search box. Each step adds one thing to the command of the step before.

**Three guides, one page each**, the strict minimum first:

- 🧹 [Clean in short](https://cavo789.github.io/media-hygiene/clean/quick-guide/) — free the space of the duplicate copies, safely.
- 🗂️ [Sort in short](https://cavo789.github.io/media-hygiene/sort/quick-guide/) — a tidy tree, proposed, corrected by you, then moved.
- 🔎 [Find in short](https://cavo789.github.io/media-hygiene/find/quick-guide/) — find a photo by a person, a place, a year or a word.

Or step by step, one option at a time:

**Start here** — the same three first steps, whatever you do next (no Docker yet?
[Install Docker](https://cavo789.github.io/media-hygiene/start/00-install-docker/) first):

1. [Your first audit](https://cavo789.github.io/media-hygiene/start/01-first-audit/) — one folder, one command, and how to
   read the result.
2. [Keep the cache](https://cavo789.github.io/media-hygiene/start/02-keep-the-cache/) — the next audits take seconds instead
   of minutes.
3. [Several folders and disks](https://cavo789.github.io/media-hygiene/start/03-several-folders/) — `C:` and `D:` together,
   the current folder, WSL.

**Clean the duplicates**

4. [The HTML report](https://cavo789.github.io/media-hygiene/clean/04-html-report/) — the pictures, the folder pairs, the
   proof.
5. [Choose which copy stays](https://cavo789.github.io/media-hygiene/clean/05-choose-the-kept-copy/) — `--prefer`,
   `--protect`, `--exclude`.
6. [Only some file types](https://cavo789.github.io/media-hygiene/clean/06-file-types/) — `--ext`, and files other than
   photos.
7. [The configuration file](https://cavo789.github.io/media-hygiene/clean/07-configuration-file/) — write your choices once,
   in `config.toml`.
8. [Clean](https://cavo789.github.io/media-hygiene/clean/08-clean/) — set the extra copies aside in the quarantine,
   with a journal.
9. [Undo, history, purge](https://cavo789.github.io/media-hygiene/clean/09-undo-history-purge/) — change your mind, see what
   was done, empty the quarantine to free the space.
10. [Sort burst series in your browser](https://cavo789.github.io/media-hygiene/clean/10-review-bursts/) — keep the best
    shots of each burst, with the keyboard.
11. [Near duplicates](https://cavo789.github.io/media-hygiene/clean/11-near-duplicates/) — resized and recompressed copies
    (`--tier near`).
12. [Decide pair by pair](https://cavo789.github.io/media-hygiene/clean/12-decide-pair-by-pair/) — swap or leave alone a
    folder pair, from the report.
13. [A second opinion](https://cavo789.github.io/media-hygiene/clean/13-second-opinion/) — compare with Czkawka, an
    independent tool.

**Sort the photos** (clean the duplicates first)

4. [Propose a tidy tree](https://cavo789.github.io/media-hygiene/sort/04-classify/) — `classify` proposes a place
   for every file, and changes nothing.
5. [Review the proposal](https://cavo789.github.io/media-hygiene/sort/05-review-the-proposal/) — correct it in a
   workbook, look at the photos in the report.
6. [Write down what you know](https://cavo789.github.io/media-hygiene/sort/06-write-down-what-you-know/) — rules for
   your trips, birthdays, folders and cameras, applied at every run.
7. [Sort](https://cavo789.github.io/media-hygiene/sort/07-sort/) — `sort` moves the files as the workbook says,
   journaled and undoable.
8. [Name the subjects with a local model](https://cavo789.github.io/media-hygiene/sort/08-subjects-from-a-local-model/) —
   a vision model on your computer says what the loose photos show (optional).
9. [Places and trips from the GPS](https://cavo789.github.io/media-hygiene/sort/09-places-from-gps/) — name your
   places on a map; the GPS of recent phones sorts home, family and trips, offline (optional).
10. [Sort by person](https://cavo789.github.io/media-hygiene/sort/10-sort-by-person/) — name the faces found in
    your photos; a rule files the events where someone appears, offline (optional).
11. [Name the events in your browser](https://cavo789.github.io/media-hygiene/sort/11-name-events-in-the-browser/) —
    one event at a time with its photos, named with the keyboard (optional).
12. [Albums](https://cavo789.github.io/media-hygiene/sort/12-albums/) — one photo in several folders, as hard links:
    no copy, no space used (optional).

**Every command has its own page** — first what it gives you, when, and a command to try; then
the folders it needs, its options, examples:
[`audit`](https://cavo789.github.io/media-hygiene/commands/audit/), [`status`](https://cavo789.github.io/media-hygiene/commands/status/),
[`clean`](https://cavo789.github.io/media-hygiene/commands/clean/), [`undo`](https://cavo789.github.io/media-hygiene/commands/undo/),
[`history`](https://cavo789.github.io/media-hygiene/commands/history/), [`purge`](https://cavo789.github.io/media-hygiene/commands/purge/),
[`review`](https://cavo789.github.io/media-hygiene/commands/review/), [`reports`](https://cavo789.github.io/media-hygiene/commands/reports/),
[`crosscheck`](https://cavo789.github.io/media-hygiene/commands/crosscheck/), [`config`](https://cavo789.github.io/media-hygiene/commands/config/),
[`launcher`](https://cavo789.github.io/media-hygiene/commands/launcher/), [`classify`](https://cavo789.github.io/media-hygiene/commands/classify/),
[`review-sort`](https://cavo789.github.io/media-hygiene/commands/review-sort/), [`sort`](https://cavo789.github.io/media-hygiene/commands/sort/),
[`album`](https://cavo789.github.io/media-hygiene/commands/album/), [`places`](https://cavo789.github.io/media-hygiene/commands/places/),
[`inventory`](https://cavo789.github.io/media-hygiene/commands/inventory/), [`tags`](https://cavo789.github.io/media-hygiene/commands/tags/),
[`search`](https://cavo789.github.io/media-hygiene/commands/search/), [`xmp`](https://cavo789.github.io/media-hygiene/commands/xmp/),
[`people`](https://cavo789.github.io/media-hygiene/commands/people/). Not sure which one?
[Which command?](https://cavo789.github.io/media-hygiene/reference-commands/#which-command)

**Reference** — [words of this guide](https://cavo789.github.io/media-hygiene/reference-glossary/),
[commands and options](https://cavo789.github.io/media-hygiene/reference-commands/),
[mount points](https://cavo789.github.io/media-hygiene/reference-mount-points/),
[how your photos stay safe](https://cavo789.github.io/media-hygiene/reference-safety/),
[sidecar files](https://cavo789.github.io/media-hygiene/reference-sidecars/),
[troubleshooting](https://cavo789.github.io/media-hygiene/reference-troubleshooting/),
[the inventory workbook](https://cavo789.github.io/media-hygiene/reference-inventory/),
[tags](https://cavo789.github.io/media-hygiene/reference-tags/),
[people](https://cavo789.github.io/media-hygiene/reference-people/),
[advanced usage](https://cavo789.github.io/media-hygiene/reference-advanced/).

**For developers** — [build the image, the devcontainer, releases](https://cavo789.github.io/media-hygiene/development/).

## The complete command

Once through the guide, most people end up with this command: two folders, the cache, the
reports, the configuration, the journal and the quarantine. It cleans; to audit, add `:ro` to
your folders and write `audit` instead of `clean`.

```powershell
mkdir -Force "$HOME\media-hygiene\reports", "$HOME\media-hygiene\config", "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean
```

From WSL, write Linux paths and run as yourself, so that new files belong to you:

```bash
mkdir -p ~/media-hygiene/{reports,config,journal,quarantine}
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "/mnt/c/Photos:/data/c/Photos" \
  -v "/mnt/d/Old disk:/data/d/Old disk" \
  -v media-hygiene-cache:/cache \
  -v ~/media-hygiene/reports:/reports \
  -v ~/media-hygiene/config:/config \
  -v ~/media-hygiene/journal:/journal \
  -v ~/media-hygiene/quarantine:/quarantine \
  cavo789/media-hygiene clean
```

`undo` instead of `clean` puts everything back.

## Update

`docker pull cavo789/media-hygiene` fetches the latest version; a tag such as
`cavo789/media-hygiene:0.3.0` pins one.

### Coming from media-dedup

Up to version 0.2, the tool was called **media-dedup** (`cavo789/media-dedup`); it is
media-hygiene since version 0.3.0. Nothing of yours is lost:

- Write `cavo789/media-hygiene` instead of `cavo789/media-dedup` in your commands: the old
  image is no longer on Docker Hub (Docker then answers *pull access denied*).
- Keep your folders and volumes: `$HOME\media-dedup\journal`, `media-dedup-cache` and the
  others are yours, whatever their name. Keep writing them in your `-v` options: `undo`,
  `history` and the cache find everything they hold.
- The `MEDIA_DEDUP_…` environment variables still work until version 0.4.0, with a warning:
  rename them `MEDIA_HYGIENE_…`.

## Licences

The tool itself is under the [MIT licence](LICENSE). The Docker image also contains other
people's work, each under its own licence:

| Component | Licence |
|---|---|
| [x265](https://github.com/Multicorewareinc/x265) (HEIC support, bundled by `pillow-heif`) | GPL-2.0-or-later |
| [libheif](https://github.com/strukturag/libheif), [libde265](https://github.com/strukturag/libde265) (HEIC, bundled by `pillow-heif`) | LGPL-3.0-or-later |
| [FFmpeg](https://ffmpeg.org/legal.html) (`ffprobe`, `ffmpeg`, built without `--enable-gpl`) | LGPL-2.1-or-later |
| [LibRaw](https://www.libraw.org/) (RAW files, through `rawpy`) | LGPL-2.1 or CDDL-1.0 |
| [Czkawka](https://github.com/qarmin/czkawka) (`czkawka_cli`, the second opinion of `crosscheck`) | MIT |
| [GeoNames](https://www.geonames.org/) towns (`geo/data`, see its `ATTRIBUTION.txt`) | CC BY 4.0 |
| [Leaflet](https://leafletjs.com/) (the `places` map) | BSD-2-Clause |
| Python, Pillow, NumPy, ONNX Runtime and the other Python packages, with the libraries their wheels bundle (libjpeg, libpng, libtiff, libwebp, OpenBLAS…) | PSF, MIT, BSD, Apache-2.0 and similar permissive licences |
| The Debian packages of the `python:3.14-slim` base image | Their own licences (`/usr/share/doc/*/copyright`) |

Because of x265, the image **as a whole** is covered by the GPL when you redistribute it. Every
component is the unmodified upstream release pinned in `Dockerfile` and `uv.lock`: its sources
are those of that release. The face models of `people` are not in the image: they are downloaded
on first use from [OpenCV Zoo](https://github.com/opencv/opencv_zoo) (YuNet: MIT, SFace:
Apache-2.0).
