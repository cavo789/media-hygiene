# Troubleshooting

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-troubleshooting.md)

## A real backup is seen as duplicates

If `D:\backup` must remain a second copy of your photos, [exclude it](clean/05-choose-the-kept-copy.md#exclude-a-folder)
(or do not mount it). Otherwise the tool, rightly, sees its files as duplicates.

## A folder is refused because it is mounted twice

A folder already includes its subfolders: mount `C:\Photos` alone, not `C:\Photos` **and**
`C:\Photos\2019`. Windows ignores case, Docker does not: `C:\Photos` plus `C:\photos\2019` is the
same folder twice. The tool refuses it rather than taking a photo for a duplicate of itself.

## OneDrive "Files On-Demand"

Analysing a folder whose files are online-only downloads them all. Make them available offline
first, or leave that folder out.

## Windows drives are slow through Docker

The first audit reads every image and every file that shares its size with another one. With
[`-v media-hygiene-cache:/cache`](start/02-keep-the-cache.md) the next audits only read new or changed
files. Tens of thousands of files take a few minutes just to be listed:
[every step shows its progress](start/01-first-audit.md#what-you-see-while-it-runs).

## The computer is sluggish during an audit

The tool uses every processor to go faster. To leave some for your other work:
[limit the processors used](reference-advanced.md#limit-the-processors-used).

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

## A Windows path in `config.toml` is refused

Write Windows paths between **single quotes**: `'D:\backup'`. In double quotes, TOML turns the
`\b` of `"D:\backup"` into a control character, and the tool refuses such a path rather than
ignoring it ([step 7](clean/07-configuration-file.md#fill-it-in)).

## The review page does not open

- Did you publish the port? The command needs `-p 127.0.0.1::8080`.
- The address comes from `docker port media-hygiene-review 8080`, in another window, while the
  review runs ([step 10](clean/10-review-bursts.md#step-2-open-the-page)).
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
