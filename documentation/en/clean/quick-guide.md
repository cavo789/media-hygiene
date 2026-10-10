# Clean in short: the whole path

[Documentation](../README.md) › Clean in short · 🇫🇷 [Français](../../fr/clean/quick-guide.md)

Every command of the clean, in order, ready to paste into **PowerShell**. Each step links to its
detailed page, should you want to understand. Replace `C:\Photos` with your folder (or add more:
[several folders and disks](../start/03-several-folders.md)).

No hurry: you can stop after any step, and everything `clean` does can be undone until `purge`.
Back after a few days? `mh status` says where you are and what comes next.

## 0. Once: write the `mh` command

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm `
  -v "C:\Photos:/data/c/Photos" `
  cavo789/media-hygiene launcher > "$HOME\media-hygiene\mh.ps1"
. "$HOME\media-hygiene\mh.ps1"
```

This is the only long command: it writes `mh`, a short command that remembers your folders and
mounts, for each step, exactly what it needs. Its folders, in `$HOME\media-hygiene`, are created
by `mh` itself the first time:

| Folder | What it receives |
|---|---|
| `reports` | The HTML reports, to open in your browser. |
| `config` | `config.toml`, your settings. |
| `journal` | The journal of each clean: what makes `undo` possible. |
| `quarantine` | The files set aside, until you erase them. |

In a new terminal, load `mh` again with the last line above (or add it to `notepad $PROFILE`).
PowerShell refuses to load it? See [write your folders once](../start/03-several-folders.md#write-your-folders-once-mh).

## 1. Audit and look at the report

```powershell
mh audit
```

Nothing is modified: `mh` mounts your folders read-only (`:ro`) for every command that does not
change them. The first audit reads everything; thanks to the cache, the next ones take seconds.
At the end, Ctrl+click the path of `report.html` (or open `index.html` in
`$HOME\media-hygiene\reports`).

In the report, look above all at **the folder pairs**: for each one, which folder keeps its
copies. You disagree? See [choose which copy stays](05-choose-the-kept-copy.md) (`--prefer`,
`--protect`), then run the audit again. Details: [the HTML report](04-html-report.md).

## 2. Set the exact duplicates aside

```powershell
mh clean
```

For `clean`, `mh` mounts your folders writable (`clean` moves files) and adds the journal and the
quarantine. `clean` audits again, says what it will do and asks for confirmation: answer `y`. The
extra copies go to the quarantine, never over another file. Details: [clean](08-clean.md).

## 3. Check, or undo

```powershell
explorer "$HOME\media-hygiene\quarantine"
```

The quarantine mirrors your folders, under one folder per clean. You change your mind?
`mh undo`: everything goes back to its place. Details: [undo, history, purge](09-undo-history-purge.md).

## 4. Near duplicates (optional)

Shrunk or recompressed copies (WhatsApp, e-mail…) and re-encoded videos are not identical to the
original: look at them first in the report of step 1, sections *Near duplicates* and *Re-encoded
videos*. Then:

```powershell
mh clean --tier near
```

`--tier near` moves the **sure** groups only (same picture and sound, identical fingerprints, a
smaller copy in a messaging folder) and says how many groups to check stay in place: decide them
one at a time in your browser with `mh review --near`, then `mh clean --tier near --decisions`;
or `--tier near-all` moves them all. The highest resolution stays, everything goes to the
quarantine: `undo` if a group does not suit you. Details: [near duplicates](11-near-duplicates.md).

## 5. Bursts (optional)

Series of photos taken seconds apart: you choose which ones to keep, in your browser.

```powershell
mh review
```

Open the address it prints, `http://127.0.0.1:8088/`, in your browser (Ctrl+click) and sort
with the keyboard. Each choice is saved at once in `decisions.json`, in your reports folder;
**Ctrl+C** stops, the next `review` resumes where you were. Then `--decisions` moves the
discarded photos to the quarantine:

```powershell
mh clean --decisions
```

Details: [sort burst series in your browser](10-review-bursts.md).

## 6. Free the space, for good

So far, nothing is erased: the quarantine still takes the space. Once you have checked:

```powershell
mh purge
```

It asks for confirmation. After `purge`, `undo` can no longer bring these files back.

## 7. Check the result

`mh audit` again: it should say *Nothing to clean*. Its remaining near duplicates and bursts are
the ones you chose to keep.

What next? Your library is ready to be sorted: [sort in short](../sort/quick-guide.md).

<details>
<summary>Without <code>mh</code>: the full commands</summary>

Each `mh` command is a `docker run` with the same folders. Step 1, read-only:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene audit
```

Steps 2, 3, 4, 6 and `--decisions`: `:ro` is gone, `/journal` and `/quarantine` are added; replace
`clean` with `undo`, `purge` or `clean --tier near` as the step says:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean
```

Step 5, `review`: the command of step 1 with `-p 127.0.0.1:8088:8088` after `-it`. Create the
four folders before the first run (`mkdir "$HOME\media-hygiene\reports", …`): a folder Docker
creates by itself belongs to the administrator, and the tool could not write there.

</details>

---

[Documentation](../README.md) · Step by step: **[4. The HTML report](04-html-report.md)** →
