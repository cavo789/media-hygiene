# `launcher`: write your folders once, then type `mh`

[Documentation](../README.md) › [Commands](../reference-commands.md) › `launcher` · 🇫🇷 [Français](../../fr/commands/launcher.md)

## In short

**Type `mh audit` instead of a long `docker run`: your folders are written once, with the right
mounts for every command.**

The `docker run` commands grow with every folder, and each command needs slightly different
mounts (`:ro` or not, the [journal](../reference-glossary.md#journal), a port for the browser). `launcher` prints a short script
defining `mh`, a command that remembers your folders, given as Explorer shows them: no `-v` to
write. Then `mh audit`, `mh clean`, `mh review`… are all you type.

**When**: once you know which folders you work on; again when you add one.

**Try it**:

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene launcher --photos "C:\Photos" > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: it only prints a script. |
| Needs | Your folders, one `--photos` each. |
| Recommended | `--quarantine` on the photos' disk, if it is not `C:`. |
| Writes | Nothing itself: you redirect what it prints to a file. |
| Undo | Delete the file. |

## Run it

**Without `-it`**, and with `>` to save what it prints:

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene launcher `
  --photos "C:\Photos" `
  --photos "D:\Old disk" `
  --quarantine "D:\quarantine" `
  > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
mh audit
```

From WSL:

```bash
mkdir -p ~/media-hygiene
docker run --rm cavo789/media-hygiene launcher --photos /mnt/c/Photos > ~/media-hygiene/mh.sh
source ~/media-hygiene/mh.sh
mh audit
```

## What `mh` does for each command

- **It checks your folders first**: a disk not plugged in is said, and nothing runs (Docker
  would mount an empty folder in its place).
- **Your folders read-only** (`:ro`) for every command that never changes them, writable only for
  `clean`, `sort`, `album`, `undo`, `purge` and `xmp`.
- **The cache** (the `media-hygiene-cache` volume) and the `reports`, `config`, `journal` and
  `quarantine` folders of `$HOME\media-hygiene`, created when missing; the folder of
  `--quarantine`, or a tool folder you mounted yourself with `-v` when running `launcher`, is
  kept instead.
- **The port of the browser page** (`-p 127.0.0.1:8088:8088`) for `review`, `review-sort`,
  `places`, `search` and `people`, and **your browser opens on that page** as soon as it
  answers: no address to copy. Ctrl+C in the window still stops it.
- **Your computer stays awake during the long commands** (`audit`, `clean`, `inventory`,
  `classify`, `sort`, `tags`, `people`, `undo`): Windows does not go to sleep before they end,
  and may again after (the screen may still turn off). From Linux, `mh.sh` uses
  `systemd-inhibit`, from macOS `caffeinate`; from WSL, Windows decides.
- **The window title says when a long command ends**: `mh audit...` while it runs, then
  `mh audit: done` (or `failed`) with a sound, so a minimised window shows it in the taskbar.
  Your own title is back at the next `mh`.
- **Accents and emojis readable** in every console, the old one of Windows PowerShell 5.1
  too: `mh.ps1` reads the tool's output in UTF-8, then gives the console its own encoding back.
- **The commands the tool suggests** at the end of a run are written as `mh …` too.
- **Your time zone, asked at each run**: `mh.ps1` asks Windows (`Get-TimeZone`), `mh.sh` the
  system (`/etc/localtime`), so the reports are dated in your local time, abroad too. A
  `[general] timezone` in `config.toml`, or a `-e TZ=…` given to `launcher`, wins.
- **Your language**: a `--locale fr` given to `launcher` is written into the script, so `mh`
  speaks French.
  A language set in `config.toml` is left to the file (an edit of it still counts). `launcher`
  ends with one line saying what `mh` remembers: folders, language, time zone.

## Options

| Option | What it does |
|---|---|
| `--photos "C:\Photos"` | A folder of photos and videos, as Explorer shows it (`/mnt/c/Photos` from WSL). Repeat it for several folders; not a folder inside another one. |
| `--quarantine "D:\quarantine"` | Where the copies set aside go. Default: `$HOME\media-hygiene\quarantine`. |
| `--shell powershell` | A PowerShell script (`mh.ps1`), for Windows. |
| `--shell bash` | A bash script (`mh.sh`), for WSL, Linux, macOS. |

By default, the shell is guessed from the folders: a Windows folder (`C:\…`) gives PowerShell.
The `-v` of earlier guides still work, alongside `--photos`.

## Good to know

- **In a new terminal**, load it again: `. "$HOME\media-hygiene\mh.ps1"`. To have `mh` in every
  terminal, write that line into your PowerShell profile, once (the profile and its folder are
  created when missing; `notepad $PROFILE` then shows the line):

  ```powershell
  New-Item -ItemType Directory -Force (Split-Path $PROFILE) | Out-Null
  Add-Content $PROFILE '. "$HOME\media-hygiene\mh.ps1"'
  ```

  In bash, add the `source` line to `~/.bashrc`.
- **Another folder?** Run `launcher` again with one more `--photos`, saving to the same file. For
  one command only: `mh --photos "E:\USB key" audit` adds it to your folders.
- **A network folder** (`\\NAS\photos`) is refused by `--photos`: copy the photos to a local
  disk, or mount it yourself with `-v`.
- **A refused folder** (inside another one, network, relative): `launcher` says why on screen, and
  loading the file stops with the same sentence.
- **With `-it`**, Docker sends the messages into the file too: `launcher` writes no launcher,
  and loading the file stops with the right command to run (without `-it`).
- PowerShell refuses to load the file (*running scripts is disabled*)? Once:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- **Accented folders** (`C:\Photos\Vidéos`) are safe: `mh.ps1` holds ASCII characters only, so
  that `>` cannot garble them, whatever the console's code page. An `é` of a folder is written
  `$([char]0x00E9)`, which PowerShell turns back into `é`; the comments lose their accents.

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
