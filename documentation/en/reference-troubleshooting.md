# Troubleshooting

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-troubleshooting.md)

## Docker answers instead of the tool

*'docker' is not recognized*, *command not found*, *error during connect*, *Cannot connect to
the Docker daemon*, *permission denied … docker.sock*: the tool has not started yet, Docker
itself is missing or stopped. Open Docker Desktop and wait for *Engine running* (Windows), or
follow [install Docker](start/00-install-docker.md#if-it-does-not-work) (Windows and Linux).

**Docker Desktop closed, on Windows**, `docker run` prints:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

**`mh` starts it for you** (Windows, `mh.ps1`): *Docker Desktop is not started: starting it (up
to 3 minutes)…*, then it waits for Docker Desktop to answer (`docker desktop start`).

- `mh` alone, the *Media Hygiene* shortcut and the right-click entry check Docker Desktop first:
  once it answers, the home page opens as usual. After a restart of the computer, nothing to do.
- Any other command (`mh audit`, `mh clean`…) is never run a second time by itself: a `clean`
  may have stopped in the middle. Once Docker Desktop is started, `mh` says *Docker Desktop is
  ready: type the command again (↑ then Enter)*.
- **When it cannot start it** (a Docker Desktop too old to know `docker desktop start`, a start
  that fails or takes more than 3 minutes), `mh` says: *Docker Desktop is not started: start it
  from the Start menu, wait until it says it is running, then type the command again.* Do so;
  if Docker Desktop does not start from the Start menu either, see
  [install Docker](start/00-install-docker.md#if-it-does-not-work).

From WSL or Linux, `mh.sh` only says that Docker is not started: Docker Engine is a service, and
`mh` never runs `sudo`.

## A real backup is seen as duplicates

If `D:\backup` must remain a second copy of your photos, mark it a backup:
`--backup "D:\backup"` ([compare it](clean/05-choose-the-kept-copy.md#compare-a-backup-or-an-old-disk)).
It is then compared, never changed, and says what it lacks. To not even read it,
[exclude it](clean/05-choose-the-kept-copy.md#exclude-a-folder) (or do not mount it).

## A folder is refused because it is mounted twice

A folder already includes its subfolders: mount `C:\Photos` alone, not `C:\Photos` **and**
`C:\Photos\2019`. Windows ignores case, Docker does not: `C:\Photos` plus `C:\photos\2019` is the
same folder twice. The tool refuses it rather than taking a photo for a duplicate of itself.

## OneDrive "Files On-Demand"

With Files On-Demand, a photo can live in OneDrive's cloud only: Windows 11 often puts
*Pictures* in OneDrive when it is set up with a Microsoft account. Reading such a file downloads
it, so analysing that folder downloads all of it.

On Windows, `mh` checks first. Before a command that reads your photos (`audit`, `review`,
`clean`, `crosscheck`, `classify`, `tags`, `people`, `search`), for each photo folder under
OneDrive (the folders named by the `OneDrive`, `OneDriveConsumer` and `OneDriveCommercial`
variables), it counts the files Windows marks as not stored on the PC (the attributes
*recall on data access* and *offline*: listing them reads no photo), then asks:

```text
1,234 files (45.2 GB) of C:\Users\you\OneDrive\Pictures are in OneDrive's cloud only: reading them downloads them onto this PC (120 GB free on C:). To keep them here: right-click the folder, then Always keep on this device.
Continue? (y/N)
```

`N` (or Enter) runs nothing. The count is made once per PowerShell window, and a `y` is not asked
again in it. `mh folders add` of a folder under OneDrive says the same line once. To keep the
photos on the PC, right-click the folder in Explorer, then **Always keep on this device**; or
leave that folder out. A folder outside OneDrive is never listed.

Still to check: whether Docker Desktop, reading through its file sharing, downloads such a file as
Windows does (not documented). If you use OneDrive, a report of what you see is welcome (an issue
on GitHub).

## Files "could not be read this time"

The audit lists them in the console and in its report: the disk, the network or the cloud did not
give them (a USB disk unplugged, a network drive gone, an online-only OneDrive file while
offline). They are not broken: `clean` leaves them where they are, and the next audit reads them
again. Plug the disk back in, or make the OneDrive files available offline, then run `audit`
again. A file listed audit after audit lies on a failing disk: copy it elsewhere while you still
can.

## Windows drives are slow through Docker

The first audit reads every image and every file that shares its size with another one. With
[`-v media-hygiene-cache:/cache`](start/02-keep-the-cache.md) the next audits only read new or changed
files. Tens of thousands of files take a few minutes just to be listed:
[every step shows its progress](start/01-first-audit.md#what-you-see-while-it-runs).

## The computer is sluggish during an audit

The tool uses every processor to go faster. To leave some for your other work:
[limit the processors used](reference-advanced.md#limit-the-processors-used).

## The analysis stopped overnight

The computer went to sleep: Docker Desktop pauses with it, and the run stops where it was. Run
it with [`mh`](commands/launcher.md#what-mh-does-for-each-command), which keeps the computer
awake until a long command ends, or set *Sleep* to *Never* in the Windows settings for that
night. Run the command again: what was already read is in the cache.

## `mh.ps1` cannot be written: "Access to the path … is denied"

Your antivirus blocks that file: after it has flagged something in a folder, some (Avast) refuse
any new file at the same path, without a new alert, until Windows restarts. Look in its
quarantine and its history for `mh.ps1` and restore it, or restart Windows, then run the
`launcher` line of [step 0](clean/quick-guide.md) again. No exception is needed: see
[below](#an-antivirus-stopped-mh-started-by-the-shortcut-or-the-right-click) for what an
older `mh` started.

## An antivirus stopped `mh` started by the shortcut or the right-click

The page opens, then *Run* does nothing, or the antivirus says it blocked `mh.ps1` (Avast:
*IDP.HELU.PSD11*). The *Media Hygiene* shortcut and right-click entry of an older `mh` started
PowerShell with `-ExecutionPolicy Bypass`, a start some antiviruses stop. Type `mh update` (or
run the `launcher` line of [step 0](clean/quick-guide.md) again and load `mh.ps1`): `mh` writes
the shortcut and the entry it finds again, without that option, and says so in one line each.
Do not add an antivirus exception: nothing in `mh` needs one. If a line says *Could not write*
with *Access refused*, restart Windows (the antivirus locks a path it has flagged until then),
then type `mh shortcut` or `mh explorer` again.

## "Cannot ask for confirmation without an interactive terminal"

Run with `-it`: without a terminal, `clean`, `sort`, `undo` (of a sort run several times) and
`purge` cannot ask for confirmation, and colours are off. In a script, add `--yes` instead.

## Folders the tool cannot write to

When a folder given to `-v` does not exist yet, Docker creates it for the administrator
(`root`), and the tool (which does not run as `root`) cannot write there. The command then stops
before the analysis and names the folder.

- Create your folders **before** `docker run` (`mkdir …`).
- From WSL or Linux, add `--user "$(id -u):$(id -g)"`; a folder Docker already created is yours
  again with `sudo chown "$(id -u):$(id -g)" <folder>`.
- A `:ro` on `/journal`, `/quarantine`, `/reports` or `/cache` stops it the same way. Only
  `config.toml` is optional: it is then not created.
- If the report alone fails after an audit, a warning says so and the results stay on screen.

## C: is full after a clean

The photos were on another drive than the quarantine: each file set aside was copied to the
quarantine's drive (with `mh`, `C:`). `clean` says it before asking, and refuses when the files
would not fit ([cleaning, step 8](clean/08-clean.md#photos-on-another-drive-than-the-quarantine)).
To get the space back, check the files set aside, then `purge` them
([step 9](clean/09-undo-history-purge.md)). For the next clean, give that drive its own
quarantine: `mh` does it for each drive of its photo folders (`mh folders add`), or
`-v "E:\media-hygiene\quarantine:/quarantine/e"`.

## `undo` asks to plug in a drive that is plugged in

`undo` or `purge <run>` says *set … files aside in the quarantine of E:, which is not mounted*
while the USB drive is plugged in: Windows gave it another letter. Keep one of its photo folders
in `mh` (`mh folders add "F:\Photos"`, which also mounts `F:`'s quarantine): the run is then
found in `F:`'s quarantine, and `undo` says so. If it says the run is in two quarantines, one is
a copy made by hand: keep one.

## A Windows path in `config.toml` is refused

Write Windows paths between **single quotes**: `'D:\backup'`. In double quotes, TOML turns the
`\b` of `"D:\backup"` into a control character, and the tool refuses such a path rather than
ignoring it ([cleaning, step 7](clean/07-configuration-file.md#fill-it-in)).

## A setting of `config.toml` is unknown to this version

```text
❌ 'timezon' in [general] of config.toml is unknown to version 0.3.0: a typo, or a setting of a
newer version? Did you mean 'timezone'?
💡 Correct or remove it, or update the image to the latest version:
docker pull cavo789/media-hygiene
```

A typo is named with the setting it looks like. A setting copied from a newer documentation needs
the newer image: `docker pull cavo789/media-hygiene`. The same goes for a variable
`MEDIA_HYGIENE_<SECTION>__<KEY>` passed with `-e`. A refused value (`verbosity = "loud"`) says
what is expected instead. Several problems at once are listed one per line, under a single
heading. A problem inside a `[[classify.rules]]` entry, a place or a person names it by its
number and its `name`: `'match' in [[classify.rules]] number 2 ('Birthday') of config.toml: this
setting is required.`

## The review page does not open

- With `mh review`, your browser opens on the page by itself, once it answers.
- Did you publish the port? The command needs `-p 127.0.0.1:8088:8088`: the same number on both
  sides, or the address the review prints is not the right one
  ([cleaning, step 10](clean/10-review-bursts.md#step-2-open-the-page)).
- A page window closed with its X leaves the page running, port 8088 held. The next `mh` page
  stops it by itself (*An mh page left open by a closed window was stopped.*); a page still open
  in another window is left alone: close it there with Ctrl+C. `mh` knows a window by its
  process number and the time it started, so a number Windows has given to another program
  since does not keep a dead page alive.
- Another program uses 8088 (another local server, a preview of your editor): `mh` names it
  before the page, with its process number (*The port of the mh pages is used by another
  program, python (process 4242): close it, then type the command again.*), and runs nothing.
  Close that program; if you cannot, give the pages another port: `port = 9000` under
  `[review]` in `config.toml`, then `mh update` (it writes the new port into `mh`). On Windows it asks Windows which program listens;
  in WSL or Linux, `ss` tells it for your own programs only, and Docker says *address already in
  use* for the others.
- *port is already allocated* with `docker run` typed by hand: choose another number, the same
  three times: `-p 127.0.0.1:9000:9000` and `review --port 9000`.
- Open it with `127.0.0.1` or `localhost`: the page refuses other host names.
- *"The review is not running any more"*: the review window was closed or stopped with Ctrl+C.
  Start it again; your choices are kept.

## Accents look wrong with `type` in PowerShell

`type .\decisions.json` shows `DÃ©cembre` instead of `Décembre`: the file is fine. The tool
writes it in UTF-8, as JSON expects, and Windows PowerShell 5.1 reads a file without a
byte order mark in the old Windows code page. To see it right:

```powershell
Get-Content -Encoding UTF8 .\decisions.json
```

PowerShell 7 and Notepad show it right as is. The tool also reads back the files Windows tools
rewrite: "UTF-8 with BOM" from Notepad, `Set-Content -Encoding UTF8`, or the UTF-16 of `>` and
`Out-File`. The same goes for `config.toml`.

## `mh` mounts an empty folder instead of an accented one

A `mh.ps1` written by an older image holds `Vid├®os` where your folder is `Vidéos`: PowerShell
decoded the tool's output in the console's old code page before `>` saved it. `mh` then mounts a
folder that does not exist, Docker Desktop creates it empty, and the audit finds nothing there.
Run `launcher` again, with the same folders, to the same file: the new script is ASCII only
and keeps every accent.

## A USB stick is seen empty: "missing from the backup", 0 files

*Docker Desktop cannot see D:\Backup (a removable drive, such as a USB stick)*: the folder is on a
drive Windows calls removable, usually a USB stick or a memory card. WSL, which Docker Desktop
runs on, shares fixed drives only: in place of the stick, Docker Desktop mounts an empty folder
of its own. An audit would then say your photos are missing from a backup that holds them all,
so the tool stops before it compares anything.

- With `mh`, nothing to do: before each command it shares a removable drive with Docker Desktop
  and says so (*D: is a removable drive: shared with Docker Desktop.*). If sharing fails, it
  stops with the advice below. After the command, it stops sharing the drive, so Windows'
  *Safely Remove Hardware* can eject it. A drive another `mh` window still uses stays shared
  (*D: stays shared with Docker Desktop: another mh window uses it.*) until Docker Desktop
  stops; to eject it once that window's command has ended, type
  `wsl -d docker-desktop umount /mnt/host/d` first.
- With `mh` in WSL (`mh.sh`): WSL mounts the drives present when it starts, never a stick
  plugged in later, so `/mnt/d` is missing. `mh` never runs `sudo` itself: it stops and says the
  line to type once per plug-in, then the command again (↑ then Enter):

  ```bash
  sudo mkdir -p /mnt/d && sudo mount -t drvfs D: /mnt/d -o uid=1000,gid=1000
  ```

  (`mh` writes your own `uid` and `gid`.) Before ejecting the stick, type `sudo umount /mnt/d`; if
  Windows still says *This device is currently in use*, type `wsl --shutdown` in PowerShell (it
  stops Docker Desktop too: start it again after): WSL keeps the stick until it stops (measured).
  With the Windows interop of WSL turned off (`/etc/wsl.conf`), `mh` cannot ask Windows which
  drives it has: mount the stick yourself with the same line.
- With `docker run` typed by hand, share the drive once (here `D:`), then run the command again:

  ```powershell
  wsl -d docker-desktop sh -c "mkdir -p /mnt/host/d && mount -t drvfs D: /mnt/host/d"
  ```

  It lasts until Docker Desktop stops; to eject the stick before that:
  `wsl -d docker-desktop umount /mnt/host/d`.
- Or copy the folder to a fixed disk. Most external hard disks and SSDs are fixed drives:
  Docker Desktop sees them as they are.

## A command the guide shows is unknown

*No such command*, or `mh` runs the image's help instead: your image is older than the guide.
Type `mh update`: it downloads the new version and writes `mh` again with your folders. A `mh`
older than `mh update` itself does not know it: run the `launcher` line of
[the guide](clean/quick-guide.md#0-once-write-the-mh-command) once more, with your folders.

## "Unexpected error during …"

A bug of the tool, not something you did wrong. The message says what failed and whether your
photos were touched: a read-only command never touches them; after `clean` or `sort`, what was
already done is in the journal, and `undo` puts it back.

Please [open an issue](https://github.com/cavo789/media-hygiene/issues) with the version, the
command you typed and the message: the last 💡 line holds all three. For more details, run the
same command again with `-e MEDIA_HYGIENE_DEBUG=1` after `docker run`: it then shows where the
error happened (the Python traceback), to paste in the issue too.
