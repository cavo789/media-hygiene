# `menu`: every step, the next one first

[Documentation](../README.md) › [Commands](../reference-commands.md) › `menu` · 🇫🇷 [Français](../../fr/commands/menu.md)

## In short

**Lost? Type `mh` alone: every step of the guides, the next one proposed, Enter runs it.**

You do not need to remember any command name. `mh` typed alone shows the steps of the three
guides ([clean](../clean/quick-guide.md), [sort](../sort/quick-guide.md),
[find](../find/quick-guide.md)) in order, each with its full `mh …` command, and proposes **one**:
the step [`status`](status.md) would give. Press Enter to run it, or type the number of another
step. The command chosen is then shown once more, *Next time, type it directly: mh clean*: you
learn the commands while using them.

**When**: whenever you no longer know what comes next.

**Try it** (once `mh` is written, [step 0 of the guides](../clean/quick-guide.md#0-once-write-the-mh-command)):

```powershell
mh
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 The menu itself never changes them, not even reads them. The step you choose says what it risks: 🔒, ↩️ or ⚠️. |
| Needs | `mh`: the menu runs the step you choose through it, with the right folders. |
| Writes | Nothing. |
| Undo | Nothing to undo; each step keeps its own undo. |
| With `mh` | `mh` alone. |

## What it shows

Under *Where you are* (the last audit, the quarantine), one line per step:

- **👉** the step proposed, the one Enter runs; **✅** a step the tool's folders prove done (an
  audit seen, no copy left, a sort applied, tags or faces found). Nothing is marked when the tool
  cannot tell.
- the **number** to type, then the **command** you will later type yourself;
- what the step does, and its badge: 🔒 photos untouched, ↩️ can be undone, ⚠️ for good,
  *optional*; 🤖 next to `classify` and `tags` when a local model is set (`[classify.ai] model`).
- A step the tool fills from what it knows takes its argument (`mh purge <run>`, `mh undo <run>`);
  with nothing to purge or undo, it has no number. An album needs words only you know
  (`mh album "Christmas" --category …`): type it yourself.

While a clean step is proposed, the sort and find steps are dimmed: they come after.

<!-- capture: menu.txt -->
```text
──────────────────────── media-hygiene — where you are ─────────────────────────
Last audit: 2026-10-11 17:43 (4 days ago) — 29 files, 9 extra copies (46.3 KB),
3 broken.
Quarantine: empty.

      Clean the duplicates
✅  1 mh audit                          Find the duplicates and the  🔒
                                        broken files
👉  2 mh clean                          Set the extra copies aside   ↩️
                                        (asks first)
    3 mh history                        What each run did            🔒
      mh undo                           Put back the files of the    ↩️
                                        last run (nothing to do yet)
    4 mh review                         Choose the best shots of     🔒 optional
                                        each burst, in your browser
    5 mh clean --tier near --decisions  Apply your choices: what you ↩️ optional
                                        set aside goes to the
                                        quarantine
      mh purge                          Free the space of the        ⚠️
                                        quarantine, for good
                                        (nothing to do yet)
      Sort the photos
    6 mh classify                       Propose a tidy tree, in a    🔒
                                        workbook you correct
    7 mh review-sort                    Name the events in your      🔒 optional
                                        browser
    8 mh places                         Name your places on a map    🔒 optional
    9 mh people                         Name the faces               🔒 optional
   10 mh sort                           Move the photos as the       ↩️
                                        workbook says
      mh album "Christmas" --category … Gather a selection into an   ↩️ optional
                                        album of links (type it
                                        yourself)
      Find a photo
✅ 11 mh tags                           Give your photos words       🔒
   12 mh search                         Find a photo by its words,   🔒
                                        in your browser
   13 mh xmp                            Carry the words into other   ↩️ optional
                                        photo software
   14 mh inventory                      Every photo and video in an  🔒 optional
                                        Excel workbook

🤖 classify and tags can also ask a local AI model: set [classify.ai] model in
config.toml (mh config).
A step to type yourself takes words only you know:
https://cavo789.github.io/media-hygiene/sort/quick-guide/
Enter runs step 2 (mh clean). Another number runs that step. Ctrl+C leaves.
⚠️  The menu runs its steps through mh: write it once with 'launcher' (step 0 of
the guides), then type mh alone.
```

## Good to know

- `menu` has no option.
- The menu never answers for you: `clean`, `sort` and `purge` still ask before acting.
- After the step, the menu does not come back: type `mh` again, it shows where you are now.
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
