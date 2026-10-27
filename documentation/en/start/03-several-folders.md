# 3. Several folders and disks

[Documentation](../README.md) › Start, step 3 of 3 · 🇫🇷 [Français](../../fr/start/03-several-folders.md)

Duplicates rarely stay in one folder: an old disk, a phone backup, a copy on `D:`. Give the tool
every folder to compare, and it finds the copies across all of them in one run.

## Add a folder: `mh folders add`

Give the folder as Explorer shows it:

```powershell
mh folders add "D:\Old disk"
mh audit
```

Or type `mh folders add` alone: Windows' folder window opens, choose the folder in it, then *OK*
(no quotes, no path to type).

`mh` writes itself again with that folder, then shows your folders read back from its file.
`mh folders` alone lists them, each *found* or *not found* (a disk not plugged in);
`mh folders remove "D:\Old disk"` takes one out, a renamed folder too. Several folders from the
start? One `--photos` each in the `launcher` line of [step 1](01-first-audit.md#write-mh-once):
`--photos "C:\Photos" --photos "D:\Old disk"`.

The result now compares the two disks:

<!-- capture: audit.txt|Audit summary|└ -->
```text
Audit summary
┌──────────────────────────────────────────────────────┬─────────┐
│ Media files scanned                                  │      89 │
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

Each disk of your photos gets its own quarantine (`D:\media-hygiene\quarantine`): what `clean`
sets aside later stays on its disk, a simple rename. Rather one quarantine for everything? Add
`--quarantine "D:\quarantine"` to the `launcher` line: it receives the files of every disk.

## Just once: `mh --photos`

For one command only, `mh --photos "E:\USB key" audit` adds a folder to yours: the copies of your
photos on the key are found too, and your folders stay as they are. `mh --photos "E:\USB key"`
alone opens the menu on it; `mh explorer` puts that on the right-click of every folder in
Explorer: right-click, *Media Hygiene*, then choose the step.

A disk not plugged in? `mh` says which folder it cannot find and runs nothing: Docker would
otherwise mount an empty folder, and the audit would find nothing.

## Give each folder only once

A folder already includes its subfolders: `C:\Photos` is enough for `C:\Photos\2019`. Giving
both would show each photo twice, and the tool **refuses** it rather than taking a photo for a
duplicate of itself.

## A backup or an old disk? Compare it

Added like any folder (above), `D:\backup` would be seen, rightly, as duplicates of your photos. Mark it
a **backup** instead: the tool reads it and compares it, never changes it, and never sets a copy
aside because the backup has it too.

```powershell
mh folders add --backup "D:\backup"
mh audit
```

`mh` writes itself again with that backup: from then on, it is mounted **read-only for every
command, `clean` included**, so Windows itself refuses any change in it, and given to the
commands that compare (`audit`, `review`, `clean`, `crosscheck`). `mh folders` lists it apart,
under *Your backups, compared, never changed*; `mh folders remove "D:\backup"` takes it out.
From the start: `--backup "D:\backup"` in the `launcher` line of [step 1](01-first-audit.md#write-mh-once).

The audit then answers the two questions, in two lines:

```text
🗄️ D:\backup: 37 files of your photos are not in this backup (412.0 MB).
   5 files are only in it, never in your photos (18.3 MB): 'import' copies them into them.
   2 other files are ones you set aside or deleted before: not proposed.
```

- **Is my backup complete?** The first line: the files of your photos it lacks.
- **Can I wipe this old disk?** The second line: its files that are nowhere else.
  [`mh import`](../commands/import.md) copies them into your photos, each one checked; the
  ones you set aside or deleted on purpose are never proposed.

### Your NAS: get back what only it holds

A share of a NAS is a backup too: `mh folders add --backup \\NAS\Photos` (its address, then the
name of the shared folder). `mh` asks the user name and the password once, checks it can read the
share, and offers to keep the password, encrypted for your Windows account only, on this PC.
Before each command it mounts the share read-only (SMB 3) and unmounts it after; a NAS powered
off is said in one line, and the command runs without it. `mh folders` tells whether it
answers; `mh folders remove \\NAS\Photos` forgets it and its password.

Through Docker Desktop a NAS is read at about 15 MB/s (measured). A backup is never read whole:
of a file the same size as one of your photos, the audit reads its first and last 64 KB (128 KB
per file), so a first audit of a large NAS takes minutes, not hours; the next ones read only what
changed. A Synology that offers only an older SMB:
*Control Panel → File Services → SMB → Advanced Settings → Maximum SMB protocol: SMB3*.

The report lists both, and `backup-missing.csv` and `backup-only.csv`, next to `plan.csv`, list
every file ([Compare a backup or an old disk](../clean/05-choose-the-kept-copy.md#compare-a-backup-or-an-old-disk)).
A folder that must not even be read is [excluded](../clean/05-choose-the-kept-copy.md#exclude-a-folder) instead.

### Your NAS: back up your photos to it

The other way round: `mh push --to \\NAS\backup_photos` copies every photo folder of `mh`
into a shared folder **of its own** on the NAS (create it once in DSM), only what it lacks, at
the speed of Windows (about 100 MB/s, against 15 MB/s through Docker: measured). A photo moved
by `sort` is renamed there, not sent again; a photo deleted by mistake on the PC is never
deleted from the NAS: only what you purged or confirmed deleted is set aside, in `.removed`.
The next times, `mh push` alone. Windows PowerShell only: [`push`](../commands/push.md).

## A phone? Copy only its new photos

Plugging a phone in and copying everything each time brings back every photo you already have,
and the cleaning that follows. On Windows, `mh import --phone` copies only the photos and videos your
library does not hold yet, nor the ones you set aside on purpose before:

```powershell
mh import --phone
mh audit
```

They land in `<your first photo folder>\Phone\<the phone's name>` (`--to` chooses another
folder); the phone itself is only read. How it decides, and what to do when the cable comes
out: [`mh import --phone`](../commands/import.md#from-a-phone-mh-import---phone).

To make room on the phone too, `mh import --phone --free` then shows on a page what the PC holds, and
deletes from the phone only what you tick, each file proven on the PC by its content first:
[free the phone](../commands/import.md#free-the-phone-mh-import---phone---free).

## Good to know

- **A Google Photos Takeout** is one more folder: extract its ZIP files, then add the extracted
  folder. Its `.json` files travel with their photos and date those without a date of their own
  ([Google Photos Takeout](../reference-sidecars.md#google-photos-takeout)).
- **A new terminal** knows `mh` through your PowerShell profile (step 1). Without that line,
  load it again: `. "$HOME\media-hygiene\mh.ps1"`.
- **A new version**: `mh update` downloads it and writes `mh` again with your folders.
- PowerShell refuses to load the file (*running scripts is disabled*)? Once:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

??? note "Without `mh`: one `-v` per folder, from PowerShell, WSL or Linux"

    Each folder gets its own `-v`. The rule: **`X:\path` becomes `/data/x/path`**, the drive
    letter in lowercase. The quotes make paths with spaces work:

    | On your computer | In the command |
    |---|---|
    | `C:\Photos` | `-v "C:\Photos:/data/c/Photos:ro"` |
    | `D:\Old disk` | `-v "D:\Old disk:/data/d/Old disk:ro"` |

    ```powershell
    docker run --rm -it `
      -v "C:\Photos:/data/c/Photos:ro" `
      -v "D:\Old disk:/data/d/Old disk:ro" `
      -v media-hygiene-cache:/cache `
      cavo789/media-hygiene audit
    ```

    Watch out for case: Windows sees `C:\Photos` and `C:\photos\2019` as the same
    folder, Docker does not. The current folder of PowerShell is `${PWD}`
    (`-v "${PWD}:/data/current:ro"`); in the old `cmd.exe` console, `%cd%`.

    **From WSL**, write Linux paths, `\` continues a line, and add `--user "$(id -u):$(id -g)"`
    so that the files the tool creates later belong to you:

    ```bash
    docker run --rm -it --user "$(id -u):$(id -g)" \
      -v "/mnt/c/Photos:/data/c/Photos:ro" \
      -v "/mnt/d/Old disk:/data/d/Old disk:ro" \
      -v media-hygiene-cache:/cache \
      cavo789/media-hygiene audit
    ```

    **From Linux**, the rule is the same: `/data` followed by the **full path** of the folder.
    Your pictures in `~/Pictures` and a USB disk under `/media`:

    ```bash
    docker run --rm -it --user "$(id -u):$(id -g)" \
      -v "$HOME/Pictures:/data$HOME/Pictures:ro" \
      -v "/media/$USER/Disk/Photos:/data/media/$USER/Disk/Photos:ro" \
      -v media-hygiene-cache:/cache \
      cavo789/media-hygiene audit
    ```

    The tool then shows `/home/<you>/Pictures/…` and `/media/<you>/Disk/…`, the paths you know.
    Mounted elsewhere (`-v "$HOME/Pictures:/data/pictures"`), the analysis is the same, but the
    paths shown are no longer yours. `mh` exists for bash too: give the folders as bash sees
    them (`launcher --shell bash --photos /mnt/c/Photos`), save to `~/media-hygiene/mh.sh`, then
    `source ~/media-hygiene/mh.sh` (in `~/.bashrc` for every terminal).

---

← [2. Keep the cache](02-keep-the-cache.md) · [Documentation](../README.md) · Next, to clean: **[4. The HTML report](../clean/04-html-report.md)** → · to sort: **[4. Propose a tidy tree](../sort/04-classify.md)** →
