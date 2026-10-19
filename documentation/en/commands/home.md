# `home`: the home page, in your browser

[Documentation](../README.md) › [Commands](../reference-commands.md) › `home` · 🇫🇷 [Français](../../fr/commands/home.md)

## In short

**One page in your browser: where you stand, the next step as a big button, every step of the
guides, your reports.**

`home` shows in your browser what [`status`](status.md) and [`menu`](menu.md) show in the
terminal: the last audit, the quarantine, the runs you can still undo, the reviews not applied;
the step that comes next as a big button; every step of the three guides
([clean](../clean/quick-guide.md), [sort](../sort/quick-guide.md), [find](../find/quick-guide.md))
with its `mh` command and its badges; your reports, and a few pictures the last audit found. It
can also run the audit itself, its progress shown in the page.

**When**: whenever you prefer clicking to typing, or no longer know what comes next.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene home
```

![The home page: the next step as a big button, the audit run in the page with the time of each step, where you are, a few pictures the audit found, the reports, then the steps of the three guides](../images/home.webp)

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed by the page: mount them `:ro`. The audit run from the page only reads them. |
| Needs | The tool's folders (`/reports`, `/journal`, `/quarantine`, `/cache`), as `status` does; your folders for the audit; `-p 127.0.0.1:8088:8088` for the page. |
| Writes | Nothing by itself; the audit run from the page writes its cache and its report, as `audit` does. |
| Undo | Nothing to undo; each step keeps its own undo. |
| With `mh` | `mh home`. |

## What the page shows

- **Next step**: why, and the full command as a big button: *the last audit found extra copies:
  'clean' sets them aside*, **mh clean**. When everything is applied, the page says so.
- **Audit in this page** 🔒: **Audit now** reads your folders as `mh audit` does, with the same
  settings. Each step (listing, fingerprints, comparing, proving identity…) shows with its counts
  as it goes; at the end, the audit's figures, the time each step took (*Time per step: listing
  1.2 s · checks 3.4 s · …*, the line `mh --verbosity verbose audit` prints), *What you can do*,
  and a link to the new report. One audit at a time; **Stop the audit** stops it between two files: the cache keeps what it
  has read, and the next audit starts from there.
- **Where you are**: the lines of [`status`](status.md), and the run `mh undo` still puts back.
  Opened by a right-click on a folder (or `mh --photos "E:\Folder"`), it names that folder
  first, in bold: *This page also analyses: E:\Folder*, one line per folder; the audit of the
  page and every step run from it analyse it too.
- **What the last audit found**: a few previews of its report.
- **Reports**: the last audit and the last clean, and *Every report* (`index.html`), opened in
  a new tab from the page itself.
- **The steps of the three guides**, numbered as in [`mh menu`](menu.md): **👉** the step
  proposed, **✅** a step the tool's folders prove done, the badges 🔒 photos untouched, ↩️ can be
  undone, ⚠️ for good, *optional*, 🤖 when a local model is set. A step `mh` cannot fill for you
  (`mh album "Christmas" --category …`) shows the command to type.

## Run a step

The page never changes your photos itself. What a step's button does depends on the `mh` that
opened the page:

- **`mh` alone** (and so the Desktop shortcut and the right-click of a folder), which runs the
  steps of the page and says so to it: **Run** (or the big
  button) closes the page and hands the step to `mh`, in the window where `mh` runs (PowerShell on Windows), with the folders
  that step needs. The page says where: *mh audit runs in the PowerShell window of mh (in the taskbar): this page
  comes back by itself when it ends*. That window is often behind the browser: a step asking a
  question waits for your answer there, so after 30 seconds the page adds *Nothing moves? Look at
  the PowerShell window of mh (in the taskbar) (Alt+Tab)*. When `mh` opens the home page again, the page reloads on its own. The step chosen is the
  command's exit code, `100 + n` for step `n` of `mh menu`: that is how `mh` knows what to run.
- **Otherwise** (`mh home` typed, an older `mh`, or `docker run` alone): the button reads **Copy**. It copies the
  command (*Copied: mh clean*) and the page keeps running; stop it with Ctrl+C in the window where `mh` runs (PowerShell on Windows),
  paste the command there (right click) and press Enter. When the browser refuses to
  copy (the page opened at an address other than `127.0.0.1` or `localhost`), the command is
  selected: press Ctrl+C yourself.

Every other page ([`review`](review.md), [`review-sort`](review-sort.md),
[`places`](places.md), [`search`](search.md), [`browse`](browse.md), [`people`](people.md))
carries a **⌂ Home** link at the bottom right: it closes that page (what you decided there is
already saved) and waits for the home page on the same address.

## Options

| Option | What it does |
|---|---|
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- The page answers only at `127.0.0.1` or `localhost`, and only to its own buttons: another
  site cannot choose a step for you.
- Ctrl+C in the terminal closes the page; an audit running stops between two files.
- The steps are read again from the tool's folders each time the page loads: what another
  window did shows at the next reload. A button of a page drawn before such a change is refused
  (*The steps changed since the page was shown*) and the page shows the steps again.

## Go further

- [`menu`: the same steps in the terminal](menu.md)
- [`status`: where you are, in one second](status.md)

## The built-in help

<details>
<summary><code>home --help</code></summary>

<!-- capture: help-home.txt -->
```text
 Usage: media-hygiene home [OPTIONS]

 🔒 Read-only: never changes your photos. The home page in your browser: where
 you are, the next step as a button, every step of the guides, the reports.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port of the page. docker run publishes   │
│                                     it under the same number on your         │
│                                     computer: -p 127.0.0.1:9000:9000 for     │
│                                     --port 9000. Default: 8088.              │
│ --help  -h                          Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
