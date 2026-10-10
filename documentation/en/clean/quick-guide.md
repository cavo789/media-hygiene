# Clean in short: the whole path

[Documentation](../README.md) › Clean in short · 🇫🇷 [Français](../../fr/clean/quick-guide.md)

Every command of the clean, in order, ready to paste into **PowerShell**. Each step links to its
detailed page, should you want to understand. Replace `C:\Photos` with your folder (or add more:
[several folders and disks](../start/03-several-folders.md)).

No hurry: you can stop after any step, and everything `clean` does can be undone until `purge`.

## 0. Once: create your folders

```powershell
mkdir "$HOME\media-hygiene\reports", "$HOME\media-hygiene\config", "$HOME\media-hygiene\journal", "$HOME\media-hygiene\quarantine"
```

| Folder | What it receives |
|---|---|
| `reports` | The HTML reports, to open in your browser. |
| `config` | `config.toml`, your settings. |
| `journal` | The journal of each clean: what makes `undo` possible. |
| `quarantine` | The files set aside, until you erase them. |

Create them **before** the first run: a folder Docker creates by itself belongs to the
administrator, and the tool could not write there.

## 1. Audit and look at the report

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene audit
```

Nothing is modified (`:ro`). The first audit reads everything; thanks to the cache (`/cache`),
the next ones take seconds. At the end, Ctrl+click the path of `report.html` (or open
`index.html` in `$HOME\media-hygiene\reports`).

In the report, look above all at **the folder pairs**: for each one, which folder keeps its
copies. You disagree? See [choose which copy stays](05-choose-the-kept-copy.md) (`--prefer`,
`--protect`), then run the audit again. Details: [the HTML report](04-html-report.md).

## 2. Set the exact duplicates aside

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

Two changes: `:ro` is gone (`clean` moves files), and `/journal` and `/quarantine` are added.
`clean` audits again, says what it will do and asks for confirmation: answer `y`. The extra copies
go to the quarantine, never over another file. Details: [clean](08-clean.md).

## 3. Check, or undo

```powershell
explorer "$HOME\media-hygiene\quarantine"
```

The quarantine mirrors your folders, under one folder per clean. You change your mind? Run the
command of step 2 with `undo` instead of `clean`: everything goes back to its place. Details:
[undo, history, purge](09-undo-history-purge.md).

## 4. Near duplicates (optional)

Shrunk or recompressed copies (WhatsApp, e-mail…) and re-encoded videos are not identical to the
original: look at them first in the report of step 1, sections *Near duplicates* and *Re-encoded
videos*. Then the command of step 2, with `--tier near`:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean --tier near
```

All or nothing: every near duplicate goes to the quarantine, the highest resolution stays. Check
the quarantine, and `undo` if a group does not suit you. Details: [near
duplicates](11-near-duplicates.md).

## 5. Bursts (optional)

Series of photos taken seconds apart: you choose which ones to keep, in your browser.

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene review
```

Open the address it prints, `http://127.0.0.1:8088/`, in your browser (Ctrl+click) and sort
with the keyboard. Each choice is saved at once in `decisions.json`, in your reports folder;
**Ctrl+C** stops, the next `review` resumes where you were. Then the command of step 2 with
`--decisions` moves the discarded photos to the quarantine:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene clean --decisions
```

Details: [sort burst series in your browser](10-review-bursts.md).

## 6. Free the space, for good

So far, nothing is erased: the quarantine still takes the space. Once you have checked, the
command of step 2 with `purge` instead of `clean` empties the quarantine:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene purge
```

It asks for confirmation. After `purge`, `undo` can no longer bring these files back.

## 7. Check the result

Run the audit of step 1 again: it should say *Nothing to clean*. Its remaining near duplicates
and bursts are the ones you chose to keep.

What next? Your library is ready to be sorted: [sort in short](../sort/quick-guide.md).

---

[Documentation](../README.md) · Step by step: **[4. The HTML report](04-html-report.md)** →
