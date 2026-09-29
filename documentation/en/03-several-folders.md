# 3. Several folders and disks

[Documentation](README.md) › Step 3 of 13 · 🇫🇷 [Français](../fr/03-several-folders.md)

Duplicates rarely stay in one folder: an old disk, a phone backup, a copy on `D:`. Give the tool
every folder to compare, and it finds the copies across all of them in one run.

## One `-v` per folder

Each folder gets its own `-v`. The rule: **`X:\path` becomes `/data/x/path`**, the drive letter
in lowercase.

| On your computer | In the command |
|---|---|
| `C:\Photos` | `-v "C:\Photos:/data/c/Photos:ro"` |
| `D:\Old disk` | `-v "D:\Old disk:/data/d/Old disk:ro"` |

The quotes make paths with spaces work. Here are both folders, with the cache of step 2:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene audit
```

The result now compares the two disks:

<!-- capture: audit.txt|Audit summary|└ -->
```text
Audit summary
┌──────────────────────────────────────────────────────┬─────────┐
│ Media files scanned                                  │      83 │
│ Groups of identical files                            │      20 │
│ Extra copies that can be deleted                     │      32 │
│ Space that can be freed                              │ 13.9 MB │
│ Broken files (empty or unreadable)                   │       3 │
│ Orphan sidecars (.xmp, .aae, .thm) to move           │       1 │
│ Near duplicates (moved only with --tier near)        │       2 │
│ Burst series (moved only if set aside with 'review') │       3 │
│ Duration                                             │     1 s │
└──────────────────────────────────────────────────────┴─────────┘
```

<!-- capture: audit.txt|Folders sharing|<blank> -->
```text
Folders sharing identical files
• 12 files are both in C:\Photos\2019\Seaside holidays (kept) and in D:\Old
  disk\Photos 2019 (deleted), 3.5 MB freed. D:\Old disk\Photos 2019 holds
  nothing else: it is entirely a copy of C:\Photos\2019\Seaside holidays.
• 3 files are both in C:\Photos\Phone (kept) and in D:\Old disk\Phone (deleted),
  3.0 MB freed. D:\Old disk\Phone holds nothing else: it is entirely a copy of
  C:\Photos\Phone.
• 1 file is both in C:\Photos\Videos (kept) and in D:\Old disk\Videos (deleted),
  2.9 MB freed.
• 8 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\Old phone (deleted), 2.2 MB freed. C:\Photos\Old phone holds nothing
  else: it is entirely a copy of C:\Photos\2019\Seaside holidays.
• 4 files are both in C:\Photos\2020\Christmas (kept) and in D:\Old
  disk\Christmas 2020 (deleted), 1.2 MB freed. D:\Old disk\Christmas 2020 holds
  nothing else: it is entirely a copy of C:\Photos\2020\Christmas.
• 3 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\2019\New folder (deleted), 864.7 KB freed. C:\Photos\2019\New folder
  holds nothing else: it is entirely a copy of C:\Photos\2019\Seaside holidays.
• 1 file is present several times in C:\Photos\2019\Seaside holidays: one copy
  is kept (287.5 KB freed).
```

Every path is shown the way Windows writes it: `/data/d/Old disk` is displayed as `D:\Old disk`.

## Mount each folder only once

A folder already includes its subfolders: `C:\Photos` is enough for `C:\Photos\2019`. Mounting
both would show each photo twice, and the tool **refuses** it rather than taking a photo for a
duplicate of itself. Watch out for case: Windows sees `C:\Photos` and `C:\photos\2019` as the
same folder, Docker does not.

## A real backup? Leave it out

If `D:\backup` must stay a second copy of your photos, do not mount it, or
[exclude it](05-choose-the-kept-copy.md#exclude-a-folder). Otherwise the tool, rightly, sees its
files as duplicates.

## The current folder

In PowerShell, `cd` into a folder, then use `${PWD}` (the current folder) as the source:

```powershell
docker run --rm -it -v "${PWD}:/data/current:ro" cavo789/media-hygiene audit
```

The tool still shows the real Windows path. In the old `cmd.exe` console, write `%cd%` instead
of `${PWD}`.

## From WSL

In a WSL (or Linux) terminal, write Linux paths, `\` continues a line, and add
`--user "$(id -u):$(id -g)"` so that the files the tool creates later belong to you:

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "/mnt/c/Photos:/data/c/Photos:ro" \
  -v "/mnt/d/Old disk:/data/d/Old disk:ro" \
  -v media-hygiene-cache:/cache \
  cavo789/media-hygiene audit
```

The rest of this guide shows PowerShell commands; the WSL version follows the same pattern.

---

← [2. Keep the cache](02-keep-the-cache.md) · [Documentation](README.md) · Next: **[4. The HTML report](04-html-report.md)** →
