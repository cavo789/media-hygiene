# Mount points

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-mount-points.md)

The tool runs in a container: it only sees the folders you give it with `-v "<yours>:<its>"`.
Each place in the container has one role.

| Mount | Content | Needed | Guide |
|---|---|---|---|
| `/data/<drive>/<path>` | The folders to analyse (`C:\Photos` → `/data/c/Photos`). | always; `:ro` for `audit` and `review` | [1](start/01-first-audit.md), [3](start/03-several-folders.md) |
| `/cache` | SQLite index: later audits only read new or changed files; the descriptions of a local model ([sorting, step 8](sort/08-subjects-from-a-local-model.md)) are kept there too; `inventory` exports it ([inventory](reference-inventory.md)). | optional, recommended; **required** by `inventory` | [2](start/02-keep-the-cache.md) |
| `/reports` | One folder per run (`report.html`, one page per folder pair, previews, `plan.csv`), `index.html`, the `decisions.json` of `review`, the `<date>-classify` folders ([workbook and report](sort/05-review-the-proposal.md)) and the `<date>-inventory` folders ([inventory](reference-inventory.md)). | optional; **required** by `review` and `inventory` | [4](clean/04-html-report.md) |
| `/config` | `config.toml` only, created and commented on first run; `places` saves your places in it. | optional; **required** by `places` | [7](clean/07-configuration-file.md) |
| `/journal` | One JSONL journal per clean or sort. | **required** by `clean`, `sort`, `undo`, `history` | [8](clean/08-clean.md) |
| `/quarantine` | Unreadable files, orphan sidecars, near duplicates, burst shots set aside and copies of other file types moved by `clean`. | to handle them | [8](clean/08-clean.md) |

## Good to know

- **Check them**: `config` shows each mount point, the Windows folder behind it, and whether it
  is read-only, mounted, or missing ([step 7](clean/07-configuration-file.md#check-what-the-tool-uses-config)).
- **Missing or unwritable mounts** are explained by 💡 tips. `clean` stops before the analysis
  without `/journal`, with a `:ro` folder, or when it cannot write to one of its folders.
- **Create your folders before `docker run`**: a folder Docker creates by itself belongs to the
  administrator, and the tool cannot write there
  ([troubleshooting](reference-troubleshooting.md#folders-the-tool-cannot-write-to)).
- **`/config` holds `config.toml` only**: nothing else is ever written there.
- **Hardened runs**: the image also works with `--read-only --tmpfs /tmp`.
