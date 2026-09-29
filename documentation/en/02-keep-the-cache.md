# 2. Keep the cache

[Documentation](README.md) › Step 2 of 13 · 🇫🇷 [Français](../fr/02-keep-the-cache.md)

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
- The tip *"Add -v media-hygiene-cache:/cache: the next audits will be much faster."* no longer
  appears.

A file is recognised by its path, its size and its modification date: change any of them and it
is read again. The results are the same, with or without the cache.

The cache also keeps what each file says about itself, read while it is checked: the shooting
date, the GPS position, the device, the stars given in Windows, the length of a video… Nothing
more is read for it.

## Good to know

- **Keep this `-v` in every command** from now on: `audit`, and later `clean`, `review`… all
  use the same cache.
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

← [1. Your first audit](01-first-audit.md) · [Documentation](README.md) · Next: **[3. Several folders and disks](03-several-folders.md)** →
