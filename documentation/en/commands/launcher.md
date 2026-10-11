# `launcher`: write your folders once, then type `mh`

[Documentation](../README.md) › [Commands](../reference-commands.md) › `launcher` · 🇫🇷 [Français](../../fr/commands/launcher.md)

The `docker run` commands grow with every folder, and each command needs slightly different
mounts (`:ro` or not, the journal, a port for the browser). `launcher` writes them **once**: it
prints a short script defining `mh`, a command that remembers the folders mounted when you made
it. Then `mh audit`, `mh clean`, `mh review`… are all you type.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: it only prints a script. |
| Needs | Your folders, one `-v` each, as you want `mh` to mount them. |
| Recommended | Your own tool folders, if they are not those of `$HOME\media-hygiene`. |
| Writes | Nothing itself: you redirect what it prints to a file. |
| Undo | Delete the file. |

## Run it

**Without `-it`**, and with `>` to save what it prints:

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  cavo789/media-hygiene launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

From WSL:

```bash
mkdir -p ~/media-hygiene
docker run --rm \
  -v "/mnt/c/Photos:/data/c/Photos" \
  cavo789/media-hygiene launcher --shell bash > ~/media-hygiene/mh.sh
source ~/media-hygiene/mh.sh
mh audit
```

## What `mh` does for each command

- **Your folders read-only** (`:ro`) for every command that never changes them, writable only for
  `clean`, `sort`, `album`, `undo`, `purge` and `xmp`.
- **The cache** (the `media-hygiene-cache` volume) and the `reports`, `config`, `journal` and
  `quarantine` folders of `$HOME\media-hygiene`, created when missing; a tool folder you mounted
  yourself when running `launcher` is kept instead.
- **The port of the browser page** (`-p 127.0.0.1:8088:8088`) for `review`, `review-sort`,
  `places`, `search` and `people`.
- **The commands the tool suggests** at the end of a run are written as `mh …` too.

## Options

| Option | What it does |
|---|---|
| `--shell powershell` | A PowerShell script (`mh.ps1`), for Windows. |
| `--shell bash` | A bash script (`mh.sh`), for WSL, Linux, macOS. |

By default, the shell is guessed from the folders mounted: a Windows folder (`C:\…`) gives
PowerShell.

## Good to know

- **In a new terminal**, load it again: `. "$HOME\media-hygiene\mh.ps1"`; add that line to your
  profile (`notepad $PROFILE`) to have `mh` everywhere. In bash, add the `source` line to
  `~/.bashrc`.
- **Another folder?** Run `launcher` again with one more `-v`, saving to the same file.
- **With `-it`**, the script would land on the screen instead of the file: `launcher` refuses it
  and gives the right command.
- PowerShell refuses to load the file (*running scripts is disabled*)? Once:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Go further

- [3. Several folders and disks: `mh`](../start/03-several-folders.md#write-your-folders-once-mh)
- [Mount points](../reference-mount-points.md)

## The built-in help

<details>
<summary><code>launcher --help</code></summary>

<!-- capture: help-launcher.txt -->
```text
 Usage: media-hygiene launcher [OPTIONS]

 🔒 Read-only: never changes your photos. Write 'mh', a short command holding
 your folders: mh audit, mh clean.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --shell          <powershell|bash>  The shell of the script: 'powershell'    │
│                                     (Windows) or 'bash' (WSL, Linux, macOS). │
│                                     Default: guessed from the mounted        │
│                                     folders.                                 │
│ --help   -h                         Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
