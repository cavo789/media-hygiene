# 0199 — `mh`: say before reading them that photos are in OneDrive's cloud only

- **Priority**: High — the default Pictures folder of many Windows 11 PCs lives in OneDrive
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/services/launcher_update.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_comfort.py`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal A2). Windows 11 turns on OneDrive's backup of
Desktop, Documents and Pictures during setup with a Microsoft account (reported in June 2024 by
Neowin and others). With Files On-Demand, a photo can live in the cloud only. Today only the
troubleshooting page warns (`## OneDrive "Files On-Demand"`); users do not read the docs before a
first audit.

The maintainer does not use OneDrive and cannot test (2026-10-17: the measurement 0198 was closed
UNNEEDED). The design rests on Microsoft's documentation (*File Attribute Constants*, checked on
2026-10-17):

- `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` (0x00400000): the file is "not fully present locally";
  "reading the file … will cause at least some of the file/directory content to be fetched from a
  remote store". Only kernel-mode callers set it: a cloud provider's placeholder.
- `FILE_ATTRIBUTE_OFFLINE` (0x00001000): "the data of a file is not available immediately".
- Enumerating a directory reads attributes without fetching data.

What Docker Desktop's file sharing does on such a read is not documented; a Windows read fetches
the data, so the warning says "downloads" and the docs say "to check".

## What to do

- In `mh` (PowerShell), before a command that reads the photos' contents (`audit`, `review`,
  `clean`, `crosscheck`, `classify`, `tags`, `people`, `search`; not `status`, `history`,
  `config`, `reports`, `menu`, `inventory`, which read the tool's folders only), for each photo
  folder lying under a OneDrive root (`$env:OneDrive`, `$env:OneDriveConsumer`,
  `$env:OneDriveCommercial`; none set: nothing to do): count the files whose attributes hold
  0x00400000 or 0x00001000 (`[int]$_.Attributes -band …`: Windows PowerShell 5.1's
  `FileAttributes` enum lacks the first name, the value is there), and their size.
- When some are: one line and a question before the run: "1,234 photos (45 GB) of
  C:\Users\…\OneDrive\Pictures are in OneDrive's cloud only: reading them downloads them onto this
  PC (120 GB free on C:). To keep them here: right-click the folder › Always keep on this device.
  Continue? (y/N)". N runs nothing.
- The count is one recursive listing per OneDrive folder; its time cannot be measured here (no
  Windows, no OneDrive): count once per PowerShell session (a global variable holding the folder
  and its result), so that the listing and the question come once.
- `mh folders add` of a folder under OneDrive says the same once.
- Docs both languages: the troubleshooting entry (attributes, the question, "Always keep on this
  device", what is not checked: Docker Desktop's behaviour), one line in the first audit page.

## Explicit non-goals

- No automatic "Always keep on this device": it changes the user's OneDrive settings.
- The bash `mh` (WSL, Linux): no OneDrive.
- What the audit does with a file whose download fails: 0222.

## Acceptance

- Unit: the rendered `mh.ps1` holds the check (both attribute values, the OneDrive variables, the
  session cache) and the question, ASCII, translated; a folder outside OneDrive is never listed;
  the bash `mh` is unchanged.
- Docs both languages.
- A run with OneDrive would confirm the wording: none here; say in the docs that a OneDrive user's
  report is welcome.

## Gain (estimated)

A first audit of an online-only OneDrive library downloads all of it (tens of GB; Microsoft's
documentation: reading fetches the data) without a word today → one line and a question before
anything is read.
