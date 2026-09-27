# 9. Undo, history, purge

[Documentation](README.md) › Step 9 of 13 · 🇫🇷 [Français](../fr/09-undo-history-purge.md)

A clean is not final. The journal remembers every action, so you can put everything back, see
what each clean did, and, once you are sure, empty the quarantine for good.

For the three commands below, keep the same `-v` options as your `clean` (step 8); only the last
word changes.

## Undo a clean: `undo`

Changed your mind? Run the same command with `undo` instead of `clean`:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  -v media-dedup-cache:/cache `
  -v "$HOME\media-dedup\reports:/reports" `
  -v "$HOME\media-dedup\config:/config" `
  -v "$HOME\media-dedup\journal:/journal" `
  -v "$HOME\media-dedup\quarantine:/quarantine" `
  cavo789/media-dedup undo
```

<!-- capture: undo.txt -->
```text
───────────────────────────── Undo 20260927-064254 ─────────────────────────────
Undo 20260927-064254
┌──────────────────────────┬─────────┐
│ Files processed          │      36 │
│ Size                     │ 15.5 MB │
│ Skipped (left untouched) │       0 │
│ Failed                   │       0 │
│ Duration                 │     0 s │
└──────────────────────────┴─────────┘
```

- Each deleted copy is **rebuilt from the copy that was kept**, date included, even across
  disks: that is why a clean can really delete.
- Each quarantined file is moved back to its place.
- Without a name, `undo` restores the latest clean; `undo <run>` restores that one. The names
  of the runs come from `history`, below, and from the last lines of each clean.

## See what was done: `history`

```powershell
cavo789/media-dedup history
```

<!-- capture: history.txt -->
```text
Clean runs (newest first)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Run             ┃ Deleted ┃   Freed ┃ Quarantined ┃ Restored ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 20260927-064257 │      33 │ 16.2 MB │           7 │        0 │
│ 20260927-064254 │      33 │ 15.5 MB │           3 │       36 │
└─────────────────┴─────────┴─────────┴─────────────┴──────────┘
💡 'media-dedup undo <run>' restores the files of a run.
```

One line per clean, the newest first: how many files it deleted, the space freed, how many files
it moved to the quarantine, and how many were restored since. Here the first clean was fully
undone (36 files restored), then cleaned again.

## Empty the quarantine: `purge`

The quarantine keeps what `clean` moved: unreadable files, orphan sidecars, and, if you asked,
near duplicates and burst shots. Once you have checked them (open the quarantine folder in the
Explorer), `purge` deletes them **for good**:

```powershell
cavo789/media-dedup purge
```

<!-- capture: purge.txt -->
```text
❓ Permanently delete the quarantine of 20260927-064257, 20260927-064254 (2.2
MB)? [y/N] y
✅ Quarantine purged: 2.2 MB freed.
💡 'undo' can no longer restore these broken files.
```

- Without a name, `purge` empties the quarantine of every clean; `purge <run>` only that one.
- It asks first, like `clean`; `--yes` skips the question.
- After a purge, `undo` can no longer bring those files back.

## Keep the journal folder

The journal is small, and it is what makes `undo` possible. Never delete it while you might
still want to restore a clean.

---

← [8. Clean](08-clean.md) · [Documentation](README.md) · Next: **[10. Sort burst series in your browser](10-review-bursts.md)** →
