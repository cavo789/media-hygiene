# `person`: who is on this photo — name them, or set them aside

[Documentation](../README.md) › [Commands](../reference-commands.md) › `person` · 🇫🇷 [Français](../../fr/commands/person.md)

## In short

**A photo shows someone the people page never asked you about ("this is Aunt Juliette")?**
`person` opens the page *Identify someone* on that photo: name each face, then confirm, among
the photos that look like it, those that are really that person. The page and its gestures are
described in [`people`](people.md#from-any-photo-name-or-set-aside-someone).

The same page opens from the 👤 **Identify someone** of the large view of every page, from the
people page (**👤 Name someone from a photo**) and from the home page (*Find*).

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed. What you set aside goes into `decisions.json`, for [`clean --decisions`](clean.md). |
| Needs | `/cache` (the index) with the faces of [`audit --people`](audit.md). |
| Writes | The names in `config.toml` (`[[people.person]]`), read back and shown; a face you draw by hand (**✏ Draw a face the tool missed**) in the index, as described in [`people`](people.md#from-any-photo-name-or-set-aside-someone). |
| Sends | Nothing: the faces stay on this computer. |

## Run it

In Windows PowerShell, the photo as the Explorer shows its path (below the folders mounted):

```powershell
mh person "C:\Photos\2026\IMG_1234.jpg"
```

The console gives the page's address; Ctrl+C stops it. A path that is not a photo of the
folders mounted is refused at once, nothing served.

## The built-in help

<details>
<summary><code>person --help</code></summary>

<!-- capture: help-person.txt -->
```text
 Usage: media-hygiene person [OPTIONS] {photo}

 Who is on this photo: name each face, then confirm that person's other photos,
 in your browser.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    photo      <str>  The photo, as the Explorer shows its path             │
│                        (C:\Photos\x.jpg), below the folders mounted.         │
│                        [required]                                            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port of the page. docker run publishes   │
│                                     it under the same number on your         │
│                                     computer: -p 127.0.0.1:9000:9000 for     │
│                                     --port 9000. Default:  port in           │
│                                     config.toml, 8088.                       │
│ --help  -h      <bool>              Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
