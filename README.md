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

![An audit in the terminal: 83 media files scanned, 20 groups of identical files, 32 extra copies, 13.9 MB to free, then the folders sharing identical files, each pair saying which folder keeps its copies](documentation/en/images/terminal-audit.webp)

## Quick start

With Docker installed ([how to install it](documentation/en/start/00-install-docker.md), on
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
[Your first audit](documentation/en/start/01-first-audit.md) explains this command and its result, part
by part.

What it finds:

- **Exact duplicates** — same size and same SHA-256, across folders *and* disks (`C:` and `D:`
  in the same run).
- **Broken files** — empty files, images and RAW files that cannot be decoded (truncated JPEG,
  …), videos that cannot be opened.
- **Orphan sidecars** — a sidecar file (`.xmp`, `.aae`, `.thm`) left without its photo.
- **Burst series and near duplicates** (re-encoded videos included) — shown side by side in an
  HTML report; `review` then lets you choose the best shots of each burst [with the keyboard, in your browser](documentation/en/clean/10-review-bursts.md).

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
[how your photos stay safe](documentation/en/reference-safety.md).

## Documentation

The [documentation](documentation/en/README.md) walks you through, one step at a time. Each step
adds one thing to the command of the step before.

**Start here** — the same three first steps, whatever you do next (no Docker yet?
[Install Docker](documentation/en/start/00-install-docker.md) first):

1. [Your first audit](documentation/en/start/01-first-audit.md) — one folder, one command, and how to
   read the result.
2. [Keep the cache](documentation/en/start/02-keep-the-cache.md) — the next audits take seconds instead
   of minutes.
3. [Several folders and disks](documentation/en/start/03-several-folders.md) — `C:` and `D:` together,
   the current folder, WSL.

**Clean the duplicates** — in a hurry? [Clean in short](documentation/en/clean/quick-guide.md), every command on one page.

4. [The HTML report](documentation/en/clean/04-html-report.md) — the pictures, the folder pairs, the
   proof.
5. [Choose which copy stays](documentation/en/clean/05-choose-the-kept-copy.md) — `--prefer`,
   `--protect`, `--exclude`.
6. [Only some file types](documentation/en/clean/06-file-types.md) — `--ext`, and files other than
   photos.
7. [The configuration file](documentation/en/clean/07-configuration-file.md) — write your choices once,
   in `config.toml`.
8. [Clean](documentation/en/clean/08-clean.md) — set the extra copies aside in the quarantine,
   with a journal.
9. [Undo, history, purge](documentation/en/clean/09-undo-history-purge.md) — change your mind, see what
   was done, empty the quarantine to free the space.
10. [Sort burst series in your browser](documentation/en/clean/10-review-bursts.md) — keep the best
    shots of each burst, with the keyboard.
11. [Near duplicates](documentation/en/clean/11-near-duplicates.md) — resized and recompressed copies
    (`--tier near`).
12. [Decide pair by pair](documentation/en/clean/12-decide-pair-by-pair.md) — swap or leave alone a
    folder pair, from the report.
13. [A second opinion](documentation/en/clean/13-second-opinion.md) — compare with Czkawka, an
    independent tool.

**Sort the photos** (clean the duplicates first) — in a hurry? [Sort in short](documentation/en/sort/quick-guide.md), every command on one page.

4. [Propose a tidy tree](documentation/en/sort/04-classify.md) — `classify` proposes a place
   for every file, and changes nothing.
5. [Review the proposal](documentation/en/sort/05-review-the-proposal.md) — correct it in a
   workbook, look at the photos in the report.
6. [Write down what you know](documentation/en/sort/06-write-down-what-you-know.md) — rules for
   your trips, birthdays, folders and cameras, applied at every run.
7. [Sort](documentation/en/sort/07-sort.md) — `sort` moves the files as the workbook says,
   journaled and undoable.
8. [Name the subjects with a local model](documentation/en/sort/08-subjects-from-a-local-model.md) —
   a vision model on your computer says what the loose photos show (optional).
9. [Places and trips from the GPS](documentation/en/sort/09-places-from-gps.md) — name your
   places on a map; the GPS of recent phones sorts home, family and trips, offline (optional).
10. [Sort by person](documentation/en/sort/10-sort-by-person.md) — name the faces found in
    your photos; a rule files the events where someone appears, offline (optional).
11. [Name the events in your browser](documentation/en/sort/11-name-events-in-the-browser.md) —
    one event at a time with its photos, named with the keyboard (optional).
12. [Albums](documentation/en/sort/12-albums.md) — one photo in several folders, as hard links:
    no copy, no space used (optional).

**Every command has its own page** — first what it gives you, when, and a command to try; then
the folders it needs, its options, examples:
[`audit`](documentation/en/commands/audit.md), [`status`](documentation/en/commands/status.md),
[`clean`](documentation/en/commands/clean.md), [`undo`](documentation/en/commands/undo.md),
[`history`](documentation/en/commands/history.md), [`purge`](documentation/en/commands/purge.md),
[`review`](documentation/en/commands/review.md), [`reports`](documentation/en/commands/reports.md),
[`crosscheck`](documentation/en/commands/crosscheck.md), [`config`](documentation/en/commands/config.md),
[`launcher`](documentation/en/commands/launcher.md), [`classify`](documentation/en/commands/classify.md),
[`review-sort`](documentation/en/commands/review-sort.md), [`sort`](documentation/en/commands/sort.md),
[`album`](documentation/en/commands/album.md), [`places`](documentation/en/commands/places.md),
[`inventory`](documentation/en/commands/inventory.md), [`tags`](documentation/en/commands/tags.md),
[`search`](documentation/en/commands/search.md), [`xmp`](documentation/en/commands/xmp.md),
[`people`](documentation/en/commands/people.md). Not sure which one?
[Which command?](documentation/en/reference-commands.md#which-command)

**Reference** — [words of this guide](documentation/en/reference-glossary.md),
[commands and options](documentation/en/reference-commands.md),
[mount points](documentation/en/reference-mount-points.md),
[how your photos stay safe](documentation/en/reference-safety.md),
[sidecar files](documentation/en/reference-sidecars.md),
[troubleshooting](documentation/en/reference-troubleshooting.md),
[the inventory workbook](documentation/en/reference-inventory.md),
[tags](documentation/en/reference-tags.md),
[people](documentation/en/reference-people.md),
[advanced usage](documentation/en/reference-advanced.md).

**For developers** — [build the image, the devcontainer, releases](documentation/en/development.md).

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
