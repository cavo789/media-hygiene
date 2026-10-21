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

- **It starts Docker Desktop when it is not running** (Windows): `mh` alone, the shortcut and
  the right-click entry wait for it, then open the home page; after any other command that
  failed because Docker Desktop was stopped, `mh` starts it and asks you to type the command
  again, never running it twice by itself
  ([troubleshooting](../reference-troubleshooting.md#docker-answers-instead-of-the-tool)).
- **It checks your folders first**: a disk not plugged in is said, and nothing runs (Docker
  would mount an empty folder in its place).
- **Your folders read-only** (`:ro`) for every command that never changes them, writable only for
  `clean`, `sort`, `album`, `undo`, `purge` and `xmp`.
- **Your backups read-only for every command**, `clean` included (`launcher --backup`, `mh
  folders add --backup`): Windows itself refuses any change in them. The commands that compare
  (`audit`, `review`, `clean`, `crosscheck`) get each one as `--backup`.
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
  ends with one line saying what `mh` remembers: folders, backups (read-only), language, time zone.

## What `mh` does by itself

These commands are not commands of the image: `mh` runs them on your computer, without Docker.
So `--help` of the image does not list them; this page and the `mh` menu do.

| Command | What it does |
|---|---|
| `mh open` | Opens `index.html`, the list of every report, in your browser (the newest at its top). No report yet: it says to run `mh audit` first. |
| `mh shortcut` | Windows: puts a *Media Hygiene* icon on your Desktop and in the Start menu. A double-click opens the home page in your browser and a PowerShell window, minimised in the taskbar: keep it open (closing it stops Media Hygiene, and the page says so within 10 seconds); each step chosen on the page runs in it. Run again, it rewrites both; a shortcut made by an older `mh` is rewritten minimised the next time `mh.ps1` is loaded. |
| `mh explorer` | Windows: adds *Media Hygiene* to the right-click menu of every folder in Explorer, and of the empty space inside an open folder: the home page opens on that folder. Your account only, no administrator. `mh explorer --remove` takes both away. On Windows 11, it may sit under *Show more options*. |
| `mh folders` | Lists your photo folders and the quarantines, each *found* or *not found* (a disk not plugged in); a quarantine not created yet is said so: the first `clean` creates it. `add` and `remove` change them: [below](#change-your-folders-mh-folders). |
| `mh update` | Downloads the new version of the image, then writes `mh` again with the same folders: [below](#a-new-version-mh-update). |
| `mh phone` | Windows: copies only the **new** photos and videos of a phone plugged in over USB; with `--free`, then deletes from the phone what the PC holds, proven by its content: [below](#a-phone-copy-only-its-new-photos-mh-phone). |
| `mh backup` | Windows: copies your photo folders into a folder of their own on the NAS, only what it lacks; Windows writes it (robocopy), the container decides: [`backup`](backup.md). |
| `mh --lan` | Windows: the home page, as `mh` alone, that a phone of the same Wi-Fi may open too with a code (or its QR code), until `mh` stops; from the phone, the audit and the reports only: [`home`](home.md#from-a-phone-on-the-home-wi-fi-mh---lan). |

`mh shortcut` and `mh explorer` read back what they wrote (the `.lnk` files, the registry keys
`HKCU\Software\Classes\Directory\shell\MediaHygiene` and
`HKCU\Software\Classes\Directory\Background\shell\MediaHygiene`) and confirm it in one line. A failure is shown with its
reason; *access refused* often comes from an antivirus, which may lock a path it has flagged until
Windows restarts. Both show the *Media Hygiene* icon: Docker copies it from the image to
`media-hygiene.ico`, next to `mh.ps1`; if it cannot, they say so in one line and keep
PowerShell's icon. From WSL, Linux or macOS,
`mh open` uses `wslview`, `explorer.exe`, `xdg-open` or `open`; `mh shortcut`, `mh explorer` and
`mh phone` say they are for Windows; `mh backup` says why (Windows writes to the NAS 7 times faster)
and the command to type in Windows PowerShell.

**What the icon and the right-click start**: Windows PowerShell, `-NoExit -Command`, loading
`mh.ps1` under your own execution policy (the `Set-ExecutionPolicy -Scope CurrentUser
RemoteSigned` line of step 1), then `mh`. Nothing overrides that policy, so an antivirus has no
reason to stop it, and you never need to add an exception. If PowerShell still refuses the file,
the window says that one line to type. A shortcut or a right-click entry made by an older `mh`
started PowerShell with `-ExecutionPolicy Bypass`, which an antivirus may stop
([troubleshooting](../reference-troubleshooting.md#an-antivirus-stopped-mh-started-by-the-shortcut-or-the-right-click)):
the next time `mh.ps1` is loaded (after `mh update`, `mh folders add`, or the `launcher` line),
each one that starts this same `mh.ps1` is written again, read back and said in one line:
*Brought up to date, read back from …: it starts this mh.*

**`mh --photos "E:\Folder"` alone** opens the home page on that folder: *Where you are* names it (*This page also
analyses: E:\Folder*), and the step you choose analyses it too, as `mh --photos "E:\Folder" audit` would. That is what the
right-click of `mh explorer` runs.

## Change your folders: `mh folders`

```powershell
mh folders                          # your folders, found or not
mh folders add                      # one more, chosen in a window (Windows)
mh folders add "D:\Old disk"        # one more, typed
mh folders remove "D:\Old disk"     # one less
mh folders add --backup "E:\Backup" # a backup: read-only, whatever the command
```

**`mh folders add` alone** (Windows) opens Windows' folder window, in front of the console,
starting at *This PC*: choose the folder, then *OK*; no path to type, no quotes. *Cancel* says
*No folder chosen: nothing changed.* The folder chosen is checked as a typed one: a library, a
phone or a network place without a drive letter is refused, and so is a folder already listed.
`mh.sh` (WSL, Linux, macOS) has no window: give the folder.

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

**When**: when the tool tells you. Once a day at most, the [home page](home.md) and `mh menu`
ask Docker Hub whether a newer version is published; when one is, the home page shows it next
to the version, with *See what changes* and *Update*, and `mh menu` ends with *A new version,
0.5.0: mh update*. That request carries no data about your photos: Docker Hub sees your address
and the image's name, as with a `docker pull`. Without a network nothing is shown and nothing
waits; `check_updates = false` in `[general]` of `config.toml` turns it off
([the setting](../clean/07-configuration-file.md#a-new-version-check_updates)). The notes of
each version are on [GitHub](https://github.com/cavo789/media-hygiene/releases); `mh update`
prints that link after an update.

A `mh` written before `mh update` existed does not know it: run the `launcher` line of the
guides once more, with your folders; from then on, `mh update` is enough. An image you built
yourself (`media-hygiene`) has nothing to download: `mh update` says so, then writes `mh` again
from that image as it is, with the same folders, and lists them as read back from the file.

**A `mh` older than its image says so.** The image can change without `mh update`: pulled by
Docker Desktop or `docker pull`, or built again on your computer. `mh.ps1` then stays as the
previous image wrote it, and some of what it does (the home page's steps, a long run's window)
may no longer match. So `mh` passes, at each command, the stamp of the image that wrote it,
and the image compares it with its own, without any extra Docker call. When they differ, every
command starts with one line, and nothing is blocked:

```text
⚠️  This mh was written by the image 0.5.0 (build 1a2b3c4d5e6f), this one is 0.6.0 (build
4d5e6f7a8b9c): type mh update to write it again, with the same folders.
```

The stamp is the version and a build: the start of the digest of every file the image installs.
The same version built again with other code is another build; the same code built twice is
the same one. A `mh` written before this check passes no stamp: the line says *written by an
older image* (this also covers a `mh.ps1` that no longer understands the home page's steps);
with an image you built yourself, the `mh update` of a `mh` that old only says *nothing to
pull*: run the `launcher` line once more. After `mh update`, the line is gone. Re-pulling `latest` while nothing changed keeps the same
build: nothing is said.

## A phone? Copy only its new photos: `mh phone`

```powershell
mh phone                       # into <your first photo folder>\Phone\<the phone's name>
mh phone --to "D:\From phones" # elsewhere, then a folder per phone
mh phone --only Camera         # only the folder DCIM\Camera of the phone
mh phone --free                # then free the phone: below
```

Plug the phone in over USB, unlock it and choose *File transfer* (iPhone: *Trust this
computer*). `mh phone` finds it (several phones: it asks which one), lists its `DCIM` folder
(about 30 seconds per 1,000 files), then copies **only** what your library does not hold yet:

- **already in your library**: a file of the same name (case ignored) and the same size that an
  audit has seen, on any of your disks, plugged in or not;
- **set aside on purpose before**: a burst shot, a near copy, a photo you chose to remove
  ([cleaning, step 9](../clean/09-undo-history-purge.md#what-you-set-aside-stays-set-aside)),
  whether its quarantine is still there or purged;
- **already copied** into that folder by an earlier `mh phone`.

It ends with what it read back from the folder: *New photos and videos copied: 212 (1.40 GB,
18.5 MB/s)*, then each count left out, and *👉 What next: `mh audit`*. 🔒 Without `--free`, the
phone is only read: nothing on it is deleted, moved or renamed.

- **Run `mh audit` once first**: the library is what the cache knows. Without an audit, every
  photo of the phone is new (it says so).
- **The phone only gives a name and a size**, not its content. A different photo that happens to
  have the name and size of one of yours stays on the phone, not copied; a photo copied twice
  under another name is found by the next audit as an identical copy, which `clean` handles.
- **Unplugged in the middle?** The file being copied is removed, the import stops and says how
  many were copied. Type `mh phone` again: what is already copied is skipped.
- **Never a Windows question**: each file is copied into an empty folder
  (`.mh-phone-<date>`), then moved to its place; a name already taken gets `_1`, said on screen.
  That folder is removed at the end.
- The phone's folders below `DCIM` are kept (`Camera`, `Screenshots`). Other folders of the phone
  (WhatsApp) are not read. With `--to` outside your photo folders, `mh folders add` it for the
  audits to see it.
- Windows only: from WSL, Linux or macOS, Docker and bash cannot reach a phone over USB.

### Free the phone: `mh phone --free`

After the import, a page opens in your browser with what the PC may hold, in three groups:

- **📚 Already in your library** and **📥 Copied by `mh phone`** (now or before): ticked for you;
- **⚠️ Set aside before, on purpose**: never ticked for you. While its quarantine is there, the
  tile shows the photo itself (its copy in the quarantine, only read) and says *Set aside on
  <date>, still recoverable with `mh undo <run>` until `mh purge`*; once purged, *Purged on
  <date>: it is nowhere else. Deleted from the phone, it is lost for good* (a purge older than
  this version gives no date: *purged since*).

Every tick is saved at once in `phone-decisions.json` (in your reports folder), read back from the
disk and shown. **Nothing leaves the phone before you press *Delete N files from the phone***;
*Leave everything on the phone* ends it with nothing deleted. Then, for each file ticked:

1. it is **copied again** from the phone into an empty folder (`.mh-phone-<date>`);
2. its **content is proven** (SHA-256) equal to a file of your library that is still there, to
   the import's own copy, or to what you set aside before; **otherwise it stays on the phone**,
   with its reason (*Not the same content as `2025\07\IMG_0001.jpg`*). A name and a size are
   never enough;
3. only then is it **moved off the phone** into a PC folder (`.mh-moved-<date>`), the phone's
   folder listed again to see it gone, and that moved copy dropped once equal to the proven one
   (one that differs is kept there, said on screen).

It says the time first (each file is read twice from the phone, about 24 MB/s: *about 6 min for
4.2 GB*), and ends with what it saw gone: *Phone freed: 4,980 files deleted (21.3 GB)*, then the
files kept on the phone and why. Each deletion is written in the journal before and after it
happens (a run of kind `phone` in `mh history`).

- ⚠️ **Deleted over USB, a file is gone for good from the phone**: the phone's gallery has no
  trash for it, and `undo` cannot put a file back on a phone (it says so). Its content is on the
  PC: that is what was proven.
- **Unplugged in the middle?** It stops and says what was deleted; the rest is still on the
  phone. Type `mh phone --free` again: it starts over from a fresh listing.

## Options

| Option | What it does |
|---|---|
| `--photos "C:\Photos"` | A folder of photos and videos, as Explorer shows it (`/mnt/c/Photos` from WSL). Repeat it for several folders; not a folder inside another one. |
| `--quarantine "D:\quarantine"` | Where the copies set aside go, from every drive. Default: `$HOME\media-hygiene\quarantine`, with one quarantine per photo drive. |
| `--backup "E:\Backup"` | A backup or an old disk: mounted read-only for every command, `clean` included, and given as `--backup` to the commands that compare ([compared, never changed](../start/03-several-folders.md#a-backup-or-an-old-disk-compare-it)). Repeatable; not a photo folder, nor inside or around one. |
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
- **A new `mh.ps1` written?** A window keeps the `mh` it loaded: after `launcher` or `mh update`
  from another window, the file on disk is newer than the one this window runs. Before each
  command, `mh` compares the file's write time with the one it recorded at load time (one
  check, no Docker call) and says, in one line, `mh changed on disk since this window loaded
  it: type . 'C:\...\mh.ps1' (or open a new window).` The command still runs; type the line, or
  open a new window, to run the new version. Nothing is said when the file was moved or removed.
  `mh folders` and `mh update` load the file again themselves.
- **Another folder?** `mh folders add "E:\Folder"`: `mh` writes itself again. For one command
  only: `mh --photos "E:\USB key" audit` adds it to your folders.
- **A network folder** (`\\NAS\photos`) is refused by `--photos`: copy the photos to a local
  disk, or mount it yourself with `-v`.
- **A refused folder** (inside another one, network, relative): `launcher` says why on screen, and
  loading the file stops with the same sentence.
- **With `-it`**, Docker sends the messages into the file too: `launcher` writes no launcher,
  and loading the file stops with the right command to run (without `-it`).
- PowerShell refuses to load the file (*running scripts is disabled*)? Once:
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. The window the shortcut or the
  right-click opens says this line too.
- **Accented folders** (`C:\Photos\Vidéos`) are safe: `mh.ps1` holds ASCII characters only, so
  that `>` cannot garble them, whatever the console's code page. An `é` of a folder is written
  `$([char]0x00E9)`, which PowerShell turns back into `é`; the comments lose their accents.

## Go further

- [1. Your first audit: write `mh`](../start/01-first-audit.md#write-mh-once)
- [3. Several folders and disks: `mh folders add`](../start/03-several-folders.md#add-a-folder-mh-folders-add)
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
│ --shell               <powershell|bash>  The shell of the script:            │
│                                          'powershell' (Windows) or 'bash'    │
│                                          (WSL, Linux, macOS). Default:       │
│                                          guessed from the mounted folders.   │
│ --photos              <str>              A folder of photos and videos, as   │
│                                          Explorer shows it: "C:\Photos" (or  │
│                                          /mnt/c/Photos in WSL). Repeat it    │
│                                          for several folders. No -v needed.  │
│ --quarantine          <str>              Where the copies set aside go,      │
│                                          once: best on the photos' disk (a   │
│                                          move, not a copy). Default: the     │
│                                          quarantine folder of your home.     │
│ --backup              <str>              A backup or an old disk, as         │
│                                          Explorer shows it: "E:\Backup".     │
│                                          Mounted read-only for every         │
│                                          command, clean included, and given  │
│                                          as --backup: compared, never        │
│                                          changed. Repeatable.                │
│ --help        -h                         Show this message and exit.         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
