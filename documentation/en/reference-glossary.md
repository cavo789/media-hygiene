# Words of this guide

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-glossary.md)

The words you meet in the guides and on screen, in plain language, from A to Z. Each one links
to the page that shows it in use.

### Audit

The tool reads your folders and lists what it finds: duplicates, broken files, photos taken in
bursts. It changes nothing: like a doctor's check-up before any treatment.
[First audit](start/01-first-audit.md)

### Burst series

Shots taken a second or so apart, say ten photos of the same jump. They are not duplicates: the
tool lists them and only sets aside the shots **you** choose.
[Cleaning, step 10](clean/10-review-bursts.md#what-is-a-burst-series)

### Cache

A small file where the tool notes what it has already read about each photo, so that the next
audit takes seconds instead of hours, like a bookmark.
[Keep the cache](start/02-keep-the-cache.md)

### Container

The tool running for one command, inside Docker, then gone. Whatever it writes outside the
folders you mount disappears with it.
[Install Docker](start/00-install-docker.md)

### Decisions file

`decisions.json`: the choices you make in your browser (which burst shots to set aside, what to
do with near duplicates), saved as you go. `clean --decisions` applies them.
[Cleaning, step 10](clean/10-review-bursts.md#step-7-apply-your-choices)

### Docker image

The tool packed with everything it needs, downloaded once (`cavo789/media-hygiene`). Each
`docker run` starts a [container](#container) from it.
[Install Docker](start/00-install-docker.md)

### Excluded folder

A folder the tool never reads, for a real backup that must stay a second copy (`--exclude`).
[Cleaning, step 5](clean/05-choose-the-kept-copy.md#exclude-a-folder)

### Fingerprint (SHA-256)

A long code computed from every byte of a file. Two files with the same fingerprint are
identical, byte for byte: that is how the tool proves a copy is a copy.
[What counts as a duplicate](reference-safety.md#what-counts-as-a-duplicate)

### GPS cluster

Photos taken within about 200 metres of each other, shown as one circle on the map of `places`,
so that you can name the place once: "Grandma's house".
[Sorting, step 9](sort/09-places-from-gps.md#name-your-places-on-a-map)

### Hard link

A second name for the same file, in another folder, taking no extra space. Albums are made of
hard links: the photo is in "Christmas" and in its year folder, stored once.
[Sorting, step 12](sort/12-albums.md#what-a-hard-link-is-in-windows)

### Journal

A written trace of every file a `clean` or a `sort` moved, line by line. It is what makes `undo`
possible, so these commands refuse to run without it.
[Cleaning, step 8](clean/08-clean.md#two-more-folders-the-journal-and-the-quarantine)

### Kept copy

Of several identical files, the one that stays where it is. The others are the extra copies,
set aside by `clean`.
[Cleaning, step 5](clean/05-choose-the-kept-copy.md)

### Mount, mount point

Lending a folder of your computer to the tool: `-v "C:\Photos:/data/c/Photos"`. The left side is
your folder, the right side (the mount point) is where the tool sees it. The tool sees nothing
else.
[Mount points](reference-mount-points.md)

### Near duplicate

The same photo saved again, but not byte for byte: resized for WhatsApp, recompressed for an
e-mail. Left alone unless you ask (`--tier near`).
[Cleaning, step 11](clean/11-near-duplicates.md)

### Orphan sidecar

A [sidecar](#sidecar) whose photo is gone: an `IMG_1.xmp` with no `IMG_1.jpg` next to it. `clean`
moves it to the quarantine.
[Sidecar files](reference-sidecars.md)

### Plan

What the tool proposes before it acts: which copy stays, which go (the `plan.csv` of a report),
or where each photo would be sorted (the `plan.json` of `classify`).
[Cleaning, step 4](clean/04-html-report.md)

### Port

A door number the browser pages use, `8088`: `http://127.0.0.1:8088/` opens the page of `review`,
`places` or `people` on your computer only.
[Cleaning, step 10](clean/10-review-bursts.md#step-2-open-the-page)

### Protected folder

A folder never modified, whose files are always the copies kept, say your master library
(`--protect`).
[Cleaning, step 5](clean/05-choose-the-kept-copy.md#protect-a-folder)

### Quarantine

A folder where `clean` *moves* the extra copies instead of deleting them, like a recycle bin you
control. `undo` puts them back; `purge` empties it for good.
[Cleaning, step 8](clean/08-clean.md#two-more-folders-the-journal-and-the-quarantine)

### Re-encoded video

The same video saved again by a phone or an app: same length, same pictures, another file. A
kind of [near duplicate](#near-duplicate).
[Cleaning, step 11](clean/11-near-duplicates.md#videos-too-re-encoded-copies)

### Read-only (`:ro`)

Added at the end of a `-v`, it tells the system itself to forbid any change to that folder: the
strongest guarantee for the commands that only read.
[How your photos stay safe](reference-safety.md#our-promise-these-commands-never-change-your-photos)

### Run

One execution of a command, named by its date and time (`20261011-204239`). `history` lists
them; `undo` takes one back.
[Cleaning, step 9](clean/09-undo-history-purge.md#see-what-was-done-history)

### Sidecar

A small file next to a photo holding its edits or metadata: `.xmp` (Lightroom), `.aae`
(iPhone), `.thm`. It follows its photo.
[Sidecar files](reference-sidecars.md)

### Tier

How far `clean` goes: `exact` (byte-for-byte copies, the default), `near` (also the sure near
duplicates), `near-all` (every near duplicate).
[Cleaning, step 11](clean/11-near-duplicates.md#move-them-clean---tier-near-or---tier-near-all)

### Vision model

A program that looks at a photo and describes it ("a beach, two children"), running on your own
computer with Ollama: nothing is sent online.
[Sorting, step 8](sort/08-subjects-from-a-local-model.md)

### Volume

A storage place Docker keeps for you, by name rather than by folder: the cache lives in the
`media-hygiene-cache` volume.
[Keep the cache](start/02-keep-the-cache.md)

### Workbook

`classify.xlsx`: the Excel (or LibreOffice) file where you correct the proposal of `classify`
before `sort` moves anything.
[Sorting, step 5](sort/05-review-the-proposal.md#the-workbook-edit-the-yellow-cells)

---

← [Documentation](README.md)
