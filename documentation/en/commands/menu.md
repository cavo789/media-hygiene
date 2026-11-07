# `menu`: every step, the next one first

[Documentation](../README.md) › [Commands](../reference-commands.md) › `menu` · 🇫🇷 [Français](../../fr/commands/menu.md)

## In short

**Lost? Type `mh menu`: every step of the guides in the terminal, the next one proposed, Enter
runs it.** `mh` alone shows the same steps on the [home page](home.md), in your browser.

You do not need to remember any command name. `mh menu` shows every action of the tool, grouped
as the cycle goes: **import** (from a phone, from your NAS or an old disk), **clean**
([guide](../clean/quick-guide.md)), **sort** ([guide](../sort/quick-guide.md)), **find**
([guide](../find/quick-guide.md)), **back up** (planned), then the tools: history and undo,
reports, settings. Each line has its full `mh …` command, and the menu proposes **one**: the step
[`status`](status.md) would give. Press Enter to run it, or type the number of another step. The
command chosen is then shown once more, *Next time, type it directly: mh clean*: you learn the
commands while using them.

**When**: whenever you no longer know what comes next.

**Try it** (once `mh` is written, [step 0 of the guides](../clean/quick-guide.md#0-once-write-the-mh-command)):

```powershell
mh menu
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 The menu itself never changes them, not even reads them. The step you choose says what it risks: 🔒, ↩️ or ⚠️. |
| Needs | `mh`: the menu runs the step you choose through it, with the right folders. |
| Writes | Nothing. |
| Undo | Nothing to undo; each step keeps its own undo. |
| With `mh` | `mh menu`. |

## What it shows

Under *Where you are* (the last audit, the quarantine), one line per step:

- **👉** the step proposed, the one Enter runs; **✅** a step the tool's folders prove done (an
  audit seen, no copy left, a sort applied, tags or faces found). Nothing is marked when the tool
  cannot tell. A done step that would only answer "nothing to do" has no number: its reason and
  date stand in its place (*Nothing to set aside since the audit of …*, *Already done: the
  proposal of … was applied on … (n files moved)*), the same on the home page, where its button
  is off. The audit, `classify`, tags and faces stay on: running them again gives a new result.
- the **number** to type, then the **command** you will later type yourself;
- what the step does, and its badge: 🔒 photos untouched, ↩️ can be undone, ⚠️ for good,
  *optional*; 🤖 next to `classify` and `tags` when a local model is set (`[classify.ai] model`).
  The line under the table recalls what 🔒, ↩️ and ⚠️ mean.
- A step the tool fills from what it knows takes its argument (`mh purge <run>`, `mh undo <run>`);
  with nothing to purge or undo, it has no number. A step that needs words only you know (an
  album's name, your NAS's folder, a folder to remove, how many reports to keep) shows an example,
  *(type it yourself)*: `mh album "Crete 2023"`. On the
  [home page](home.md), its form fills them in. `mh push` shows as *(planned)*.

Each action is listed once, numbered across the spaces, under the space where it first comes:
`mh open`, `mh history`, `mh undo` and `mh purge` sit in the clean guide, where they come. While a
step is proposed, the other spaces are dimmed. The menu takes the width of your window; *Reading
where you are…* shows while it counts the quarantine, which takes a few seconds when it holds
thousands of files.

The phone, `mh shortcut` (an icon on the Desktop) and `mh explorer` (the right-click of a folder)
are for Windows: the bash `mh` leaves them out. `mh` runs `open`, `folders`, `update`, `import --phone`,
`shortcut` and `explorer` itself: [what `mh` does by itself](launcher.md#what-mh-does-by-itself).
A command that has no place in the menu yet still shows, last, under *Other commands*.

<!-- capture: menu.txt -->
```text
──────────────────────── media-hygiene — where you are ─────────────────────────
Last audit: 2026-11-07 10:14 (today) — 10 files, 4 extra copies (5.9 MB), 1
broken.
Quarantine: empty.

      Import photos
      From a phone
    1 mh import --phone                               Copy the new   🔒
                                                      photos of the
                                                      phone
    2 mh import --phone --free                        Make room on   ⚠️ optional
                                                      the phone
      From your NAS or an old disk
      mh folders add --backup "\\NAS\Photos"          Plug in your   🔒
                                                      NAS or an old
                                                      disk (type it
                                                      yourself)
      mh import --pick                                See what only  ↩️
                                                      the NAS or the
                                                      disk holds,
                                                      then copy it
                                                      (nothing to do
                                                      yet)
      mh import                                       Get back what  ↩️ optional
                                                      only the NAS
                                                      or the disk
                                                      holds (nothing
                                                      to do yet)
      Go further
      mh import --pick "E:\DCIM"                      See what a USB ↩️
                                                      disk, an SD
                                                      card or a
                                                      folder holds,
                                                      then copy it
                                                      (type it
                                                      yourself)
      mh import "E:\DCIM"                             Import a USB   ↩️
                                                      disk, an SD
                                                      card or any
                                                      folder (type
                                                      it yourself)
    3 mh folders add                                  Add a photo    🔒
                                                      folder
      Clean the duplicates
      The guide
✅  4 mh audit                                        Find the       🔒
                                                      duplicates and
                                                      the broken
                                                      files
    5 mh open                                         Read the       🔒
                                                      reports in
                                                      your browser
👉  6 mh clean                                        Set the extra  ↩️
                                                      copies aside
    7 mh history                                      See what each  🔒
                                                      run did
      mh undo                                         Put back the   ↩️
                                                      files of the
                                                      last run
                                                      (nothing to do
                                                      yet)
    8 mh review                                       Choose the     🔒 optional
                                                      best shots of
                                                      each burst
    9 mh clean --tier near --decisions                Apply your     ↩️ optional
                                                      choices
      mh purge                                        Free the room  ⚠️
                                                      of the
                                                      quarantine
                                                      (nothing to do
                                                      yet)
      Go further
   10 mh upkeep                                       Run the        ⚠️ optional
                                                      regular upkeep
   11 mh undo --pick                                  Put back a few ↩️ optional
                                                      photos of the
                                                      quarantine
   12 mh review --near                                Settle the     🔒 optional
                                                      near
                                                      duplicates
   13 mh review --pairs                               Decide folder  🔒 optional
                                                      by folder
   14 mh review --junk                                Set the failed 🔒 optional
                                                      photos aside
   15 mh review --gone                                Look again at  🔒 optional
                                                      the photos
                                                      gone
   16 mh review --intruders                           Set the        🔒 optional
                                                      intruder files
                                                      aside
   17 mh crosscheck                                   Ask for a      🔒 optional
                                                      second opinion
   18 mh shrink --try                                 Lighten the    ↩️ optional
                                                      heavy videos
   19 mh clean --delete                               Delete the     ⚠️ optional
                                                      copies at once
      Sort the photos
✅ 20 mh classify                                     Propose a tidy 🔒
                                                      tree
   21 mh places                                       Name your      🔒 optional
                                                      places on a
                                                      map
   22 mh people                                       Name the faces 🔒 optional
   23 mh sort                                         Move the       ↩️
                                                      photos into
                                                      the proposed
                                                      folders
      Find a photo
      The guide
   24 mh tags                                         Give your      🔒
                                                      photos words
   25 mh spots                                        Name where     🔒
                                                      your photos
                                                      were taken
   26 mh library                                      Library: find  🔒
                                                      a photo
      Go further
   27 mh xmp                                          Carry the      ↩️ optional
                                                      words into
                                                      other photo
                                                      software
   28 mh inventory                                    All your       🔒 optional
                                                      photos in
                                                      Excel
      Back up to the NAS
      The guide
      mh push --to "\\NAS\backup_photos"              Choose the     🔒
                                                      backup folder
                                                      on the NAS
                                                      (type it
                                                      yourself)
   29 mh push                                         Back up what   ↩️
                                                      the NAS lacks
      Share your photos
      The commands
      mh slideshow --folder "C:\Photos\2026 Holidays" Show your      🔒 optional
                                                      photos on the
                                                      TV (type it
                                                      yourself)
      mh slideshow --album "Crete 2023" --lan         Show an album  🔒 optional
                                                      on the TV
                                                      (type it
                                                      yourself)
      mh share --album "Crete 2023"                   Prepare an     🔒 optional
                                                      album for
                                                      sending (type
                                                      it yourself)
      mh album "Crete 2023"                           A folder of    ↩️ optional
                                                      links on the
                                                      disk (type it
                                                      yourself)
      Reports
   30 mh reports                                      List the       🔒
                                                      reports
      mh reports --prune 10                           Keep only the  🔒 optional
                                                      recent reports
                                                      (type it
                                                      yourself)
      Settings
      Your folders
   31 mh folders                                      See your       🔒
                                                      folders
      mh folders remove "E:\Archives"                 Remove a       🔒 optional
                                                      folder (type
                                                      it yourself)
      Update
   32 mh update                                       Install the    🔒
                                                      new version
      Backup
   33 mh backup                                       Back up the    🔒
                                                      index and the
                                                      settings
   34 mh restore                                      Restore the    ↩️
                                                      index
      Windows
   35 mh shortcut                                     An icon on the 🔒 optional
                                                      Desktop and in
                                                      the Start menu
   36 mh explorer                                     Media Hygiene  🔒 optional
                                                      in the
                                                      Explorer's
                                                      right-click
   37 mh explorer --remove                            Remove Media   🔒 optional
                                                      Hygiene from
                                                      the
                                                      right-click
      Privacy
   38 mh people --forget                              Forget every   🔒 optional
                                                      face
      Advanced
   39 mh config                                       See each       🔒
                                                      setting and
                                                      where it comes
                                                      from
   40 mh config tidy                                  Tidy           🔒 optional
                                                      config.toml
   41 mh status                                       Where am I, in 🔒 optional
                                                      the console
   42 mh menu                                         The menu in    🔒 optional
                                                      the console
   43 mh launcher                                     Write mh again 🔒 optional
   44 mh home                                         The home page  🔒 optional

🔒 your photos are not touched · ↩️ can be undone · ⚠️ for good
🤖 classify and tags can also ask a local AI model: set [classify.ai] model in
config.toml (mh config).
A step to type yourself takes words only you know:
https://cavo789.github.io/media-hygiene/reference-commands/
Enter runs step 6 (mh clean). Another number runs that step. Ctrl+C leaves.
⚠️  The menu runs its steps through mh: write it once with 'launcher' (step 0 of
the guides), then type mh menu.
```

## Good to know

- `menu` has no option.
- The menu never answers for you: `clean`, `sort` and `purge` still ask before acting.
- After the step, the menu does not come back: type `mh menu` again, it shows where you are now.
  The [home page](home.md) (`mh` alone) does come back after each step.
- For a remote session, a slow PC or no browser: `mh menu` opens no page.
- `docker run … cavo789/media-hygiene` with no command still prints the `--help`: only `mh` can
  run the step chosen with the right folders.
- `docker run -it … menu` shows the menu but cannot run a step: write `mh` first.

## Go further

- [`status`](status.md): where you are, in detail.
- [`launcher`](launcher.md): write `mh`.

## The built-in help

<details>
<summary><code>menu --help</code></summary>

<!-- capture: help-menu.txt -->
```text
 Usage: media-hygiene menu [OPTIONS]

 🔒 Read-only: never changes your photos. Every step of the guides with its
 command, the next one first: what 'mh' alone shows, Enter runs it.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help  -h        Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
