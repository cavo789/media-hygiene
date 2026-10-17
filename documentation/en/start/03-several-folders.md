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

## A real backup? Leave it out

If `D:\backup` must stay a second copy of your photos, do not add it, or
[exclude it](../clean/05-choose-the-kept-copy.md#exclude-a-folder). Otherwise the tool, rightly, sees its
files as duplicates.

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
