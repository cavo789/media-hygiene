# `review-sort`: now the 🗂 Events view of `search`

`review-sort`'s page is gone: its events, choices, rules and *Sort this event now* are the
[🗂 Events view of `search`](search.md#the-events-of-the-latest-classify). For this version,
`mh review-sort` opens that view (a one-line notice says so); it goes in the next version: use
`mh search` and open **🗂 Events of the latest classify**. Your `sort-decisions.json` keeps
working: the view reads it and writes it as before.

## The built-in help

<details>
<summary><code>review-sort --help</code></summary>

<!-- capture: help-review-sort.txt -->
```text
 Usage: media-hygiene review-sort [OPTIONS] [workbook]

 🔒 Read-only: never changes your photos. Name the events of the classify
 proposal one by one in your browser.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  The classify workbook; the latest classify run's by   │
│                        default.                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port of the page. docker run publishes   │
│                                     it under the same number on your         │
│                                     computer: -p 127.0.0.1:9000:9000 for     │
│                                     --port 9000. Default:  port in           │
│                                     config.toml, 8088.                       │
│ --help  -h                          Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
