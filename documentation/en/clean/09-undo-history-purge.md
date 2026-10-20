# 9. Undo, history, purge

[Documentation](../README.md) › Cleaning, step 9 of 14 · 🇫🇷 [Français](../../fr/clean/09-undo-history-purge.md)

A clean is not final. The journal remembers every action, so you can put everything back, see
what each clean did, and, once you are sure, empty the quarantine for good.

With `mh`, the three commands below are one line each. Without it, keep the same `-v` options as
your `clean` (step 8); only the last word changes.

## Undo a clean: `undo`

Changed your mind? Run the same command with `undo` instead of `clean`:

```powershell
mh undo
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

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

</details>

<!-- capture: undo.txt -->
```text
────────────────────── Undo the clean run 20261019-153539 ──────────────────────
🛟 Each file comes back where it was, never over another one; what cannot come
back whole is left as it is, and said.

Undo the clean run 20261019-153539
┌──────────────────────────┬─────────┐
│ Files processed          │      36 │
│ Size                     │ 15.6 MB │
│ Skipped (left untouched) │       0 │
│ Failed                   │       0 │
│ Duration                 │     0 s │
└──────────────────────────┴─────────┘
```

- Each quarantined file — the extra copies first of all — is moved back to its place, never
  over another file. The quarantine folders it leaves empty go too: an undo carried out to the
  end leaves nothing of the run in the quarantine.
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
mh history
```

<!-- capture: history.txt -->
```text
Runs (newest first)
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃                 ┃         ┃         ┃       ┃          ┃  Folders ┃          ┃
┃ Run             ┃ Command ┃ Deleted ┃ Freed ┃ Quarant… ┃  removed ┃ Restored ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 20261019-153541 │ clean   │       1 │     0 │       41 │        9 │        0 │
│ 20261019-153539 │ clean   │       1 │     0 │       35 │        7 │       43 │
└─────────────────┴─────────┴─────────┴───────┴──────────┴──────────┴──────────┘
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
mh purge
```

<!-- capture: purge.txt -->
```text
⚠️  'purge' erases for good: these files cannot come back, not even with 'undo'.
It is, with 'clean --delete', the only way the tool removes content.
❓ Erase the quarantine of 20261019-153541 (41 files, 16.4 MB)? [y/N] y
✅ Quarantine purged: 16.4 MB freed.
💡 'undo' can no longer restore these files.
```

- Without a name, `purge` empties the quarantine of every clean; `purge <run>` only that one.
- It asks first, like `clean`; `--yes` skips the question.
- After a purge, `undo` can no longer bring those files back. The date of the purge is written
  next to the run's journal (`<run>.purged.json`, the journal itself is never rewritten):
  `mh phone --free` says it on the tile of a photo set aside by that run.

## Where am I? `status`

Back after a few days, you no longer remember which run is in the quarantine, nor whether a
review was applied? `status` reads the tool's own folders, without scanning your photos (about a
second), and says:

- the last audit or clean: when, and what it found;
- the quarantine: how many files, how much space, since when;
- the runs `undo` can still restore, with the full `undo` command;
- the burst series still to see and the decisions of `review` not applied yet;
- the last `classify` proposal, and whether `sort` applied it;

then **one** next step, as a full command. A quarantine older than 30 days (`purge_hint_days`, in
the `[clean]` section of `config.toml`) is the first thing it suggests to purge. Mount the same
folders as for `clean` (or type `mh status`): a folder not mounted is said, never an error.

## What you set aside stays set aside

You set burst shots aside, near duplicates, photos chosen in [`search`](../commands/search.md) or
[`review --junk`](../commands/review.md); months later, a phone backup brings them back, under
other names. The journal remembers the content of every file set aside by such a choice (its
size and SHA-256), even after `purge`: the next audit recognises them, whatever their name now,
and says it on a line of its own:

```text
↩️ 23 photos and videos you had set aside are back (45 MB): 'clean' sets them aside again.
```

The report lists them in a section of their own (*Back after being set aside*), each with its
preview, when and why it was set aside, and where it lay then. `clean` moves them to the
quarantine again with the rest of its plan, without another question: its usual question counts
them on a line of their own (*↩️ 23 photos and videos you had already set aside are back (45 MB):
back to the quarantine.*), and `history` counts them apart (*Of which back again*).

- To keep one after all: `undo` that clean. The last word is then yours: it is no longer
  proposed.
- Only what you set aside **by a choice** is remembered: an identical copy that comes back is a
  plain duplicate (its content is still kept elsewhere); a broken file is not remembered.
- A resized or recompressed version of a photo (other bytes) is not recognised. A file deleted
  in the Explorer is, once you confirm it (below).
- A file back in a [protected](07-configuration-file.md) folder is never touched.
- `returned = false` in the `[clean]` section of `config.toml` never looks for them.

### Deleted in the Explorer?

Photos deleted in the Explorer are unknown to the journal. The index can tell they are gone: a
file an audit no longer finds where it was, nor elsewhere (a folder renamed in the Explorer is
followed, never counted), below a folder mounted this time. Deleted on purpose, or moved to a
disk not plugged in? Only you can tell, so the audit asks:

```text
🗑️ 312 photos and videos have disappeared since the last audit (deleted in the Explorer?): say which ones you deleted on purpose, so that media-hygiene sets them aside if they come back.
```

`mh review --gone` shows them by folder and by day, each with its preview when the cache still
holds one (else its name, date, size and camera): `D` deleted on purpose, `M` moved elsewhere,
`G` the whole group deleted on purpose. Your answers are saved in `decisions.json`; the next
`clean --decisions` remembers the files deleted on purpose (nothing moves: a line in the
journal, counted by `history` under *Deleted in the Explorer*) and forgets the others. When one
of them comes back, it is proposed like a file you had set aside. `undo` of that clean forgets
them. A file gone whose content is still there (a copy elsewhere) or reappears later (a disk
plugged in again) is dropped from the list on its own: deleting one of two copies loses nothing.

## Keep the journal folder

The journal is small, and it is what makes `undo` possible, and what lets the audit recognise
the files you set aside if they come back. Never delete it while you might still want to restore
a clean.

---

← [8. Clean](08-clean.md) · [Documentation](../README.md) · Next: **[10. Sort burst series in your browser](10-review-bursts.md)** →
