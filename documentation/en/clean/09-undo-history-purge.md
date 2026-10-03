# 9. Undo, history, purge

[Documentation](../README.md) › Cleaning, step 9 of 13 · 🇫🇷 [Français](../../fr/clean/09-undo-history-purge.md)

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
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene undo
```

<!-- capture: undo.txt -->
```text
────────────────────── Undo the clean run 20261003-080719 ──────────────────────
🛟 Each file comes back where it was, never over another one; what cannot come
back whole is left as it is, and said.

Undo the clean run 20261003-080719
┌──────────────────────────┬─────────┐
│ Files processed          │      36 │
│ Size                     │ 15.5 MB │
│ Skipped (left untouched) │       0 │
│ Failed                   │       0 │
│ Duration                 │     0 s │
└──────────────────────────┴─────────┘
```

- Each quarantined file — the extra copies first of all — is moved back to its place, never
  over another file.
- Each copy deleted with `clean --delete` is **rebuilt from the copy that was kept**, date
  included, even across disks.
- Without a name, `undo` restores the latest run; `undo <run>` restores that one. The names
  of the runs come from `history`, below, and from the last lines of each clean.
- A file that is back already, or whose copy is gone, is left alone and listed with the reason:
  `undo` never overwrites nor guesses.
- A [sort](../sort/07-sort.md) run is undone the same way: the files move back, the folders it
  removed come back, the folders it created go. A sort stopped then run again with the same
  workbook is undone whole: every run of it, newest first, after one question (`--yes` skips
  it).
- `undo` needs the same `/journal`, folders not mounted `:ro`, and the same `/quarantine` when the
  run moved files there (unreadable files, orphan sidecars, near duplicates, burst shots, copies of
  other files, the `Thumbs.db` and the like a sort set aside). Otherwise it refuses before changing
  anything and names the run. A run that only deleted copies (`--delete`) or moved files needs no
  quarantine.

## See what was done: `history`

```powershell
cavo789/media-hygiene history
```

<!-- capture: history.txt -->
```text
Runs (newest first)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Run             ┃ Command ┃ Deleted ┃ Freed ┃ Quarantined ┃ Restored ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 20261003-080724 │ clean   │       1 │   0 B │          39 │        0 │
│ 20261003-080719 │ clean   │       1 │   0 B │          35 │       36 │
└─────────────────┴─────────┴─────────┴───────┴─────────────┴──────────┘
💡 'media-hygiene undo <run>' restores the files of a run.
```

One line per run, the newest first: the command that made it, how many files it deleted, the
space freed, how many files it moved to the quarantine, and how many were restored since. A
*Moved* column appears once a run has moved files to another of your folders. Here the first
clean was fully undone (36 files restored), then cleaned again.

## Empty the quarantine: `purge`

The quarantine keeps what `clean` moved: the extra copies, unreadable files, orphan sidecars,
and, if you asked, near duplicates and burst shots. Their space is freed only now: once you have
checked them (open the quarantine folder in the Explorer), `purge` deletes them **for good**.
It is the only command that erases content (with `clean --delete`, if you use it), and it says
so before asking:

```powershell
cavo789/media-hygiene purge
```

<!-- capture: purge.txt -->
```text
⚠️  'purge' erases for good: these files cannot come back, not even with 'undo'.
It is, with 'clean --delete', the only way the tool removes content.
❓ Erase the quarantine of 20261003-080724, 20261003-080719 (39 files, 16.2 MB)?
[y/N] y
✅ Quarantine purged: 16.2 MB freed.
💡 'undo' can no longer restore these files.
```

- Without a name, `purge` empties the quarantine of every clean; `purge <run>` only that one.
- It asks first, like `clean`; `--yes` skips the question.
- After a purge, `undo` can no longer bring those files back.

## Keep the journal folder

The journal is small, and it is what makes `undo` possible. Never delete it while you might
still want to restore a clean.

---

← [8. Clean](08-clean.md) · [Documentation](../README.md) · Next: **[10. Sort burst series in your browser](10-review-bursts.md)** →
