# 3. Several folders and disks

[Documentation](../README.md) › Start, step 3 of 3 · 🇫🇷 [Français](../../fr/start/03-several-folders.md)

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
│ Media files scanned                                  │      85 │
│ Groups of identical files                            │      20 │
│ Extra copies that can be set aside                   │      32 │
│ Space that can be freed                              │ 14.0 MB │
│ Broken files (empty or unreadable)                   │       3 │
│ Orphan sidecars (.xmp, .aae, .thm) to move           │       1 │
│ Near duplicates (moved only with --tier near)        │       3 │
│ Re-encoded videos (moved only with --tier near)      │       1 │
│ Burst series (moved only if set aside with 'review') │       3 │
│ Duration                                             │     2 s │
└──────────────────────────────────────────────────────┴─────────┘
```

<!-- capture: audit.txt|Folders sharing|<blank> -->
```text
Folders sharing identical files
• 12 files are both in C:\Photos\2019\Seaside holidays (kept) and in D:\Old
  disk\Photos 2019 (copies 'clean' moves to the quarantine), 3.6 MB to free with
  'purge'. D:\Old disk\Photos 2019 holds nothing else: it is entirely a copy of
  C:\Photos\2019\Seaside holidays.
• 3 files are both in C:\Photos\Phone (kept) and in D:\Old disk\Phone (copies
  'clean' moves to the quarantine), 3.0 MB to free with 'purge'. D:\Old
  disk\Phone holds nothing else: it is entirely a copy of C:\Photos\Phone.
• 1 file is both in C:\Photos\Videos (kept) and in D:\Old disk\Videos (a copy
  'clean' moves to the quarantine), 2.9 MB to free with 'purge'.
• 8 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\Old phone (copies 'clean' moves to the quarantine), 2.3 MB to free
  with 'purge'. C:\Photos\Old phone holds nothing else: it is entirely a copy of
  C:\Photos\2019\Seaside holidays.
• 4 files are both in C:\Photos\2020\Christmas (kept) and in D:\Old
  disk\Christmas 2020 (copies 'clean' moves to the quarantine), 1.2 MB to free
  with 'purge'. D:\Old disk\Christmas 2020 holds nothing else: it is entirely a
  copy of C:\Photos\2020\Christmas.
• 3 files are both in C:\Photos\2019\Seaside holidays (kept) and in
  C:\Photos\2019\New folder (copies 'clean' moves to the quarantine), 872.9 KB
  to free with 'purge'. C:\Photos\2019\New folder holds nothing else: it is
  entirely a copy of C:\Photos\2019\Seaside holidays.
• 1 file is present several times in C:\Photos\2019\Seaside holidays: one copy
  is kept (292.0 KB to free).
```

Every path is shown the way Windows writes it: `/data/d/Old disk` is displayed as `D:\Old disk`.

## Mount each folder only once

A folder already includes its subfolders: `C:\Photos` is enough for `C:\Photos\2019`. Mounting
both would show each photo twice, and the tool **refuses** it rather than taking a photo for a
duplicate of itself. Watch out for case: Windows sees `C:\Photos` and `C:\photos\2019` as the
same folder, Docker does not.

## A real backup? Leave it out

If `D:\backup` must stay a second copy of your photos, do not mount it, or
[exclude it](../clean/05-choose-the-kept-copy.md#exclude-a-folder). Otherwise the tool, rightly, sees its
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

## From Linux

On a Linux desktop, the rule is the same: `/data` followed by the **full path** of the folder.
Your pictures in `~/Pictures` and a USB disk under `/media`:

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "$HOME/Pictures:/data$HOME/Pictures:ro" \
  -v "/media/$USER/Disk/Photos:/data/media/$USER/Disk/Photos:ro" \
  -v media-hygiene-cache:/cache \
  cavo789/media-hygiene audit
```

The tool then shows `/home/<you>/Pictures/…` and `/media/<you>/Disk/…`, the paths you know, and
the commands it suggests (👉 *What next*, the `mh` launcher) type the same `-v` again, even when
`/home` or the disk is a partition of its own. Mounted elsewhere (`-v "$HOME/Pictures:/data/pictures"`),
the analysis is the same, but the paths shown are no longer yours.

The rest of this guide shows PowerShell commands; the WSL and Linux versions follow the same
pattern.

## Write your folders once: `mh`

The commands grow with every folder, and each step of the guides needs a slightly different one
(`:ro` or not, the journal, the quarantine, a port for the browser). Write them **once**: the
`launcher` command writes a short PowerShell command, `mh`, that remembers the folders mounted
when you created it.

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm `
  -e TZ=Europe/Brussels `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  cavo789/media-hygiene launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

No `-it` here: what `launcher` prints goes into the file. The `-e TZ=…` is kept too: `mh` dates
its reports in your local time (put your own zone if it is not `Europe/Brussels`). Then every command is short: `mh audit`,
`mh clean`, `mh review`, `mh undo`, `mh status`… `mh` picks the right mounts for each one: your
folders read-only (`:ro`) unless the command changes them (`clean`, `sort`, `album`, `undo`,
`purge`, `xmp`), the cache, and the `reports`, `config`, `journal` and `quarantine` folders of
`$HOME\media-hygiene` (created when missing), plus the port of the browser pages for `review`,
`review-sort`, `places`, `search` and `people`. The commands the tool suggests at the end of a run become `mh …` too.

- **In a new terminal**, load it again: `. "$HOME\media-hygiene\mh.ps1"`; or add that line to your
  profile (`notepad $PROFILE`) to have `mh` everywhere.
- **Another folder?** Run the `launcher` command again with one more `-v`.
- PowerShell refuses to load the file (*running scripts is disabled*)? Once:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **From WSL or Linux**: add `--shell bash` and save to `~/media-hygiene/mh.sh`, then
  `source ~/media-hygiene/mh.sh` (in `~/.bashrc` for every terminal).

---

← [2. Keep the cache](02-keep-the-cache.md) · [Documentation](../README.md) · Next, to clean: **[4. The HTML report](../clean/04-html-report.md)** → · to sort: **[4. Propose a tidy tree](../sort/04-classify.md)** →
