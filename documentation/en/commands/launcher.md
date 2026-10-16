# `launcher`: write your folders once, then type `mh`

[Documentation](../README.md) › [Commands](../reference-commands.md) › `launcher` · 🇫🇷 [Français](../../fr/commands/launcher.md)

## In short

**Type `mh audit` instead of a long `docker run`: your folders are written once, with the right
mounts for every command.**

The `docker run` commands grow with every folder, and each command needs slightly different
mounts (`:ro` or not, the [journal](../reference-glossary.md#journal), a port for the browser). `launcher` prints a short script
defining `mh`, a command that remembers your folders, given as Explorer shows them: no `-v` to
write. Then `mh audit`, `mh clean`, `mh review`… are all you type.

**When**: once you know which folders you work on. Later, `mh folders add` adds one and `mh update`
brings the new version: both write the file again for you.

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
| Good to know | Each photo drive gets its own quarantine: what `clean` sets aside stays on its drive. |
| Writes | Nothing itself: you redirect what it prints to a file. |
| Undo | Delete the file. |

## Run it

**Without `-it`**, and with `>` to save what it prints:

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene launcher `
  --photos "C:\Photos" `
  --photos "D:\Old disk" `
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
- **One quarantine per photo drive** (without `--quarantine`): for each drive of your photo
  folders other than the quarantine's (`C:`), `X:\media-hygiene\quarantine` mounted on `/quarantine/x` and created
  when missing. `clean` sets each file aside on its own drive: cleaning `E:` never fills `C:`
  ([cleaning, step 8](../clean/08-clean.md#photos-on-another-drive-than-the-quarantine)). A
  photo folder that is a whole drive (`E:\`) gets one too: the audit never reads a
  `media-hygiene` folder. `mh folders add` with a folder of a new drive adds its quarantine too.
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

## What `mh` does by itself

These commands are not commands of the image: `mh` runs them on your computer, without Docker.
So `--help` of the image does not list them; this page and the `mh` menu do.

| Command | What it does |
|---|---|
| `mh open` | Opens `index.html`, the list of every report, in your browser (the newest at its top). No report yet: it says to run `mh audit` first. |
| `mh shortcut` | Windows: puts a *Media Hygiene* icon on your Desktop and in the Start menu. A double-click opens a PowerShell window on the `mh` menu, which stays open. Run again, it rewrites both. |
| `mh explorer` | Windows: adds *Media Hygiene* to the right-click menu of every folder in Explorer: the `mh` menu opens on that folder. Your account only, no administrator. `mh explorer --remove` takes it away. On Windows 11, it may sit under *Show more options*. |
| `mh folders` | Lists your photo folders and the quarantines, each *found* or *not found* (a disk not plugged in); a quarantine not created yet is said so: the first `clean` creates it. `add` and `remove` change them: [below](#change-your-folders-mh-folders). |
| `mh update` | Downloads the new version of the image, then writes `mh` again with the same folders: [below](#a-new-version-mh-update). |

`mh shortcut` and `mh explorer` read back what they wrote (the `.lnk` files, the registry key
`HKCU\Software\Classes\Directory\shell\MediaHygiene`) and show it. A failure is shown with its
reason; *access refused* often comes from an antivirus, which may lock a path it has flagged until
Windows restarts. From WSL, Linux or macOS,
`mh open` uses `wslview`, `explorer.exe`, `xdg-open` or `open`; the other two say they are for
Windows.

**`mh --photos "E:\Folder"` alone** opens the menu on that folder: it says which folder, and the
step you choose analyses it too, as `mh --photos "E:\Folder" audit` would. That is what the
right-click of `mh explorer` runs.

## Change your folders: `mh folders`

```powershell
mh folders                          # your folders, found or not
mh folders add "D:\Old disk"        # one more
mh folders remove "D:\Old disk"     # one less
```

`add` and `remove` run `launcher` again, through the image, with the folders `mh` holds plus or
minus that one, and the same quarantine, language and settings. The new script goes into a file
beside `mh.ps1`, which it replaces only when `launcher` accepted it: a refused folder (inside
another one, a network folder) leaves your `mh` as it was, with the reason on screen. `mh` then
loads the new file in this terminal and shows the folders it read back from it, so what you see
is what is saved. Other terminals see it once they load the file again (a new terminal does,
with the line in your profile).

- **A folder renamed or moved** (in Explorer): `mh` says it cannot find it. `mh folders remove`
  the old name, even though it is gone, then `mh folders add` the new one. The next audit reads
  its files again: the cache knows them by their path.
- **The last folder** cannot be removed: `mh` needs at least one. Add the new one first.
- **A folder of a disk not plugged in** can be removed; one to add must be there.
- Windows ignores case: `C:\photos` is `C:\Photos`, already one of your folders.

## A new version: `mh update`

```powershell
mh update
```

It downloads the new image (`docker pull`, its progress shown as it is), writes `mh` again with
the same folders exactly as `mh folders` does, then says the versions: *Updated: media-hygiene
0.5.0 → media-hygiene 0.6.0*, or *Already the latest version*. The previous image still takes
room on your disk: `mh update` says how much, and the command freeing it, `docker image prune`;
it never runs it for you.

**When**: once a month, or when a guide shows a command your `mh` does not know. The tool
never looks for a new version by itself: nothing leaves your computer unless you ask. The
published versions are listed on [Docker Hub](https://hub.docker.com/r/cavo789/media-hygiene/tags).

A `mh` written before `mh update` existed does not know it: run the `launcher` line of the
guides once more, with your folders; from then on, `mh update` is enough. An image you built
yourself (`media-hygiene`) has nothing to download: `mh update` says so.

## Options

| Option | What it does |
|---|---|
| `--photos "C:\Photos"` | A folder of photos and videos, as Explorer shows it (`/mnt/c/Photos` from WSL). Repeat it for several folders; not a folder inside another one. |
| `--quarantine "D:\quarantine"` | Where the copies set aside go, from every drive. Default: `$HOME\media-hygiene\quarantine`, with one quarantine per photo drive. |
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
- **Another folder?** `mh folders add "E:\Folder"`: `mh` writes itself again. For one command
  only: `mh --photos "E:\USB key" audit` adds it to your folders.
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
