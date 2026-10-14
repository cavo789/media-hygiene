# 2. Keep the cache

[Documentation](../README.md) › Start, step 2 of 3 · 🇫🇷 [Français](../../fr/start/02-keep-the-cache.md)

Your first audit read every photo, some of them in full. On a large library, and even more
through Docker on Windows, that takes minutes, sometimes much more. Without a cache, **every**
audit starts again from scratch.

The cache remembers what the tool learnt about each file: its fingerprint, whether it can be
read, what it looks like. The next audits only read the files that are new or have changed.

## Add the cache

Add one `-v` to the command of step 1:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene audit
```

In PowerShell, the backtick `` ` `` at the end of a line continues the command on the next one
(nothing may follow it, not even a space). The command is the same as a single line.

`media-hygiene-cache` is not a folder of yours: it is a *volume*, a storage space Docker manages by
itself. Nothing to create: Docker creates it the first time and keeps it between runs.

## What changes

- The first audit with the cache takes as long as before: it fills the cache.
- The next ones only read new or changed files: the *Duration* line of the summary shows the
  difference. A step with nothing left to do is skipped.
- The ⚙️ *To set once* line no longer suggests *"-v media-hygiene-cache:/cache (much faster next
  audits)"*.

A file is recognised by its path, its size and its modification date: change any of them and it
is read again. The results are the same, with or without the cache.

Even the walk through your folders gets shorter: a folder where no file was added, removed or
renamed since the last audit is taken from the cache, without looking at each of its files. The
audit says it in one line: *"851 unchanged folders taken from the index, 6 read."* A folder
where photos were added is read again, but only its new photos are examined one by one. A photo
changed **in place** by another program (same name) does not change its folder: it is seen at
the latest after `full_check_days` (7 days) in `[scan]`, when every folder is read in full, or
at once with `audit --full`.

The cache also keeps what each file says about itself, read while it is checked: the shooting
date, the GPS position, the device, the stars given in Windows, the length of a video… Nothing
more is read for it. `inventory` exports all of it to an Excel workbook, without reading your
photos again ([the inventory workbook](../reference-inventory.md)).

For the photos and videos found alike, it also keeps how colourful each one is (a black and
white edit is not a copy) and, for re-encoded videos, a fingerprint of their picture and sound:
the next audits, `review --near` and `clean` measure only what is new or changed.

It keeps the previews of your photos too, one per size: the small ones of the HTML reports,
the large ones of the review pages, the grid of `search`. A photo is decoded once; the next
reports and pages read its preview back. The previews take at most 2 GB: beyond, those not
shown for the longest time are removed, and made again if needed. To change that bound, set
`previews_max_gb` in the `[cache]` table of `config.toml` (`config --upgrade` adds it to an
older file).

## Good to know

- **Keep this `-v` in every command** from now on: `audit`, and later `clean`, `review`… all
  use the same cache.
- **An audit stopped halfway** (Ctrl+C, `docker stop`, the PC switched off) keeps what it
  already checked: the cache saves its work every few seconds, and the next audit goes on from
  there.
- **Start again from scratch**: `docker volume rm media-hygiene-cache`. Nothing is lost: the next
  audit just reads everything again.
- **After an update** of the tool, the first audit may read your photos once more, when the new
  version learns something new about them. When it only needs what a photo says about itself,
  it reads its header, not the whole picture: a few minutes for tens of thousands of photos,
  shown by a progress bar of its own.
- **The cache forgets the files that are gone**: deleted by `clean`, moved to the quarantine, or
  moved and deleted by hand. It only forgets where the audit could look: a disk not mounted this
  time, a folder it could not read, an excluded folder, or other types of files than those of
  `--ext` keep their place in the cache.

---

← [1. Your first audit](01-first-audit.md) · [Documentation](../README.md) · Next: **[3. Several folders and disks](03-several-folders.md)** →
