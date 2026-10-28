# `home`: the home page, in your browser

[Documentation](../README.md) › [Commands](../reference-commands.md) › `home` · 🇫🇷 [Français](../../fr/commands/home.md)

> `mh` alone opens this page; `mh home` is still there for a script, but `mh --help` no longer lists it.

## In short

**One page in your browser: where your photos stand, the next step as a big button, every
action of the tool a click or <kbd>Ctrl</kbd>+<kbd>K</kbd> away.**

`home` shows in your browser what [`status`](status.md) and [`menu`](menu.md) show in the
terminal, laid out as the cycle of your photos: **Import** (a phone, your NAS or an old disk),
**Clean**, **Sort**, **Find**, **Back up** (planned); then, apart from the cycle, **Share**
(your photos on the TV: [`slideshow`](slideshow.md), a folder or an
[album](search.md#put-photos-in-an-album)) and three tools: **History and undo**,
**Reports**, **Settings**. Each space has its page: its guide, numbered, then "Go further". Every
action shows its `mh` command, copyable, and links to its chapter of this documentation. The
page can also run the audit itself, its progress shown in the page.

**When**: whenever you prefer clicking to typing, or no longer know what comes next.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene home
```

![The home page: the sidebar with the five stages of the cycle and the tools, the next step as a big button, the cycle, the tiles of where you are, what the last audit found, the reports and the audit in the page](../images/home.webp)

## At a glance

| | |
|---|---|
| Your photos | 🔒 Nothing moves without your GO on a page (review-sort, search), journaled: `undo` puts it back. `mh home` mounts them writable, with `/journal`; the audit run from the page only reads them. |
| Needs | The tool's folders (`/reports`, `/journal`, `/quarantine`, `/cache`), as `status` does; your folders for the audit; `-p 127.0.0.1:8088:8088` for the page. |
| Writes | Nothing by itself; the audit run from the page writes its cache and its report, as `audit` does; the [albums' page](#your-albums-on-the-phone) changes `albums.json` alone. |
| Undo | Nothing to undo; each step keeps its own undo. |
| With `mh` | `mh home`. |

## What the page shows

- **The sidebar**: the five stages of the cycle, **Share** (a goal, not a stage: no number) and the tools, each with its count (*9* extra
  copies to set aside, *214* files only the NAS keeps), *Your folders* (each found or not), the
  version (*0.5.0 available* when a newer one is published, [`mh update`](launcher.md#a-new-version-mh-update)),
  and the theme switch.
- **A banner when `mh` is older than its image** (a new image pulled or built, `mh` not
  written again): the line the console says, and an **Update** button that runs
  [`mh update`](launcher.md#a-new-version-mh-update); gone once `mh` is written again.
- **The top bar**: *What do you want to do?* (the palette), **Undo the last run** while a run is
  undoable, and **Documentation**: the chapter of the page you are on, and its English twin.
- **The next step**: why, what it risks in words (*Undoable*), the button that runs it and its
  command: *the last audit found extra copies: 'clean' sets them aside*, **mh clean**. Its
  button has the focus when the page opens: <kbd>Enter</kbd> runs it, as in `mh menu`. When
  everything is applied, the page says so.
- **The cycle of your photos**: the five stages, the next one highlighted (*You are here*), each
  with one line (*9 copies to set aside*, *A proposal to apply*) and how many steps of its
  guide are done.
- **Where you are**: one tile per fact (the last audit, the extra copies, the quarantine, the
  files only on the NAS, the sort, the words, the faces), each leading to its space.
- **What the last audit found**: each finding with its button (*9 identical copies*: **Set the
  extra copies aside**; *3 unreadable files*: the report), and a few previews of its report.
  Before any audit: three things to know (nothing moves without you, everything that moves can
  be undone, one thing only is for good).
- **Recent reports**, and **Audit in this page** 🔒: **Audit now** reads your folders as
  `mh audit` does, with the same settings. Each step shows with its counts as it goes; at the
  end, the audit's figures, the time each step took, *What you can do*, and a link to the new
  report. One audit at a time; **Stop the audit** stops it between two files: the cache keeps
  what it has read, and the next audit starts from there.
- **One page per space**: its guide, numbered, then "Go further" as cards. Each action says what
  it risks (🔒 *Photos untouched*, ↩️ *Undoable*, ⚠️ *For good*), *Optional*, *Windows*, *Local
  AI* (🤖), *Planned*; **Done** when the tool's folders prove it; when it cannot run yet, why
  instead of its text (*Nothing to undo yet.*). *History and undo* shows the run still undoable
  and the quarantine run by run; *Settings* your folders, the update, Windows, the local AI,
  privacy, the advanced actions and *About*.

Opened by a right-click on a folder (or `mh --photos "E:\Folder"`), the page names that folder
first: *This page also analyses: E:\Folder*; the audit of the page and every step run from it
analyse it too.

## Run a step

The page never changes your photos itself. What a step's button does depends on the `mh` that
opened the page:

- **`mh` alone** (and so the Desktop shortcut and the right-click of a folder) runs the steps of
  the page: **Start** (or the big button) hands the step to `mh`, in the window where `mh` runs
  (PowerShell on Windows), with the folders that step needs. With reports in a folder of your
  disk (the default), the page **stays open** while a step runs in that window: *mh clean runs
  in the PowerShell window of mh (in the taskbar): answer it if it asks something. This page
  stays open and shows the result at the end*; then *mh clean: done.* and the page shows its
  new state, without reloading. *search* and *browse* open at once in this very tab, served
  by the home page itself; a step that opens another page of its own (review, people…) closes
  this one meanwhile: *Back to the home page* brings it back. A second step asked while
  one runs waits: *A step is running in the window of mh: wait for its end.* Otherwise (reports
  in a named volume, an older `mh`) the page closes and comes back by itself after the step.
  In both cases the page says at once, in bold, *Switch to the
  PowerShell window of mh (in the taskbar) now (Alt+Tab, or its button in the taskbar): it may
  ask you something*. `mh` also rings the terminal's bell and plays Windows' sound, often
  unheard (speakers off). What you can see: Windows Terminal makes its taskbar button flash on
  that bell once its settings say so (its default is the sound only): *Settings* → *Open JSON
  file*, then `"bellStyle": "taskbar"` in `profiles` → `defaults` (`["audible", "taskbar"]` to
  keep the sound). With the classic console, `mh` also brings its window forward when Windows
  allows it (a minimised window stays minimised). After 30 seconds the page adds
  *Nothing moves? Look at the PowerShell window of mh (in the taskbar) (Alt+Tab)*. The step
  chosen reaches `mh` through `.mh-step.json` of your reports folder, as the words of a form
  below: `mh` runs them at once (it used to start `mh menu` in a container of its own first,
  2 s per click). With reports in a named volume it is the command's exit code, `20 + n` for
  step `n` of `mh menu`. The tab shows the next page as soon as its server answers.
  Ctrl+C during a step (or on a page it opened) gives the prompt back: the home page does not
  come back, and no other step runs.
- **A step that takes words** (an album's name, your NAS's folder, a folder to
  remove, how many reports to keep): **Fill in** opens its form, the example filled in. The
  server checks each value and says why it refuses one (*no double quote*, *no control
  character*, *it cannot start with '-'*, *a folder as the Explorer shows it*); then it writes
  the words into `.mh-step.json` of your reports folder and ends with `199`. `mh` reads that file
  once, removes it, and runs those words: `Christmas 2025` stays one word. With reports in a
  named volume, or an older `mh`, the page gives the command to copy instead.
- **⚠️ For good** (`purge`, `clean --delete`, `import --phone --free`): the page asks first; `mh` asks
  again in its window before touching anything.
- **Otherwise** (`mh home` typed, an older `mh`, or `docker run` alone): the button copies the
  command (*Command copied*) and the page keeps running; stop it with Ctrl+C in the window where
  `mh` runs, paste the command there (right click) and press Enter. When the browser refuses to
  copy (an address other than `127.0.0.1` or `localhost`), the command is selected: press Ctrl+C.

Every other page ([`review`](review.md), [`review-sort`](search.md#the-events-of-the-latest-classify),
[`places`](places.md), [`search`](search.md), [`browse`](browse.md), [`people`](people.md))
wears the home page's look and theme, under a bar: **Documentation** opens that page's chapter,
next to its French twin (*En français*). When the home page opened it, the page shows in the
**same tab** (no new tab), and **⌂ Back to the home page** closes it (what you decided there is
already saved) and brings that tab back to the home page, on the space you left (*Clean*,
*Sort*…). Closing the tab instead ends the page and `mh` with it: the prompt comes back.

The documentation itself is inside the image: every **Doc** and **Documentation** link of these
pages opens its chapter served by the tool, in the same look, offline, and written for the version
you run (the website may already describe a newer one). Its sidebar lists every chapter, its top
bar switches to the other language (**FR**), each page lists its sections and ends on the previous
and next ones. The links the terminal prints, and the HTML reports opened from the disk, still
lead to the [website](https://cavo789.github.io/media-hygiene/): no page of the tool answers there.

## From a phone on the home Wi-Fi: `mh --lan`

In Windows, **`mh` and its desktop shortcut open the home page to the phones of the same
Wi-Fi too**, until `mh` stops: this is the default (`lan = true`). You prefer the page on this
PC only? See [Keep the page on this PC only](#keep-the-page-on-this-pc-only) below.

1. `mh` finds the PC's address on the home network (*192.168.1.20*) and says *The home page opens
   to the phones of the home network too*. Windows may ask whether **Docker Desktop** may accept
   connections: allow it on **private networks** only.
2. The PC's page shows, in its sidebar, *On your phone*: the address, a **code** of 8 digits
   and its **QR code** (the window of `mh` says the same address and code).
3. On the phone, scan the QR code, or open the address and type the code: the home page opens.
   The phone stays paired **for good** (a cookie of its own, 400 days): the next `mh --lan`
   opens on it without a code. Without HTTPS, until `mh` stops only.

On the phone, the home page is the family's door, **Our photos**: *Find a photo* (search and
browse), the albums and where you are; the stages that change photos (import, clean, sort, back
up) and the tools are not shown there, the PC keeps the whole cycle.

🔒 **The phone is read-only: every change is made on the PC.** From the phone: the page, where you are, the reports, the progress of an audit started on the PC,
[your albums](#your-albums-on-the-phone), and **search** and **browse** (their photos opened at
the phone's size, and their videos; the originals only with `lan_phone_originals = true` under `[review]` of `config.toml`, off by default: full size, GPS position included; *set aside*, *Apply now* and a move stay the PC's). Only a paired
phone reaches them: any other device of the Wi-Fi (a guest, a TV) gets the pairing page, or
nothing, on every address. While the phone shows a page, `mh` keeps running even with the
PC's tab closed; once `mh` stops, the phone's page says so.
Every other step stays on the PC (*Run this step on the PC*): its questions are asked in the
window of `mh`, which nobody sees from the sofa. One exception: **Show an album on the TV**, on
the phone's page, lists the albums saved on the PC; a tap starts that album's
[slideshow](slideshow.md) in the home page's own server, and the phone opens its remote at once.
The TV's bookmark (`http://<PC address>:8089/screen`) waits for a show and stays paired while
`mh` runs.

The *Show your photos on the TV* step, chosen on the PC, opens the [slideshow](slideshow.md) to
the home network too: the phone already paired reloads its page and gets the slideshow's remote.

| | |
|---|---|
| Who | A device on the same Wi-Fi **with the code**; 5 wrong codes close the pairing until `mh` stops. |
| Where | The PC's private address only (`10.x`, `172.16–31.x`, `192.168.x`): never every interface, never the internet; `mh` opens no port on your router. |
| How | HTTPS (`https://192.168.1.20:8088`), signed by a certificate authority `mh` makes on your PC: the phone installs it once (below); the code and the cookie never travel in clear. |
| Kept | `C:\Users\<you>\media-hygiene\lan\` holds that authority and the page's certificate (`ca.key` never leaves it). Deleted, `mh` makes a new one: install it again on each phone. |
| Next time | A paired phone opens the page directly. The PC's card lists the **phones paired for good** (Android, iPhone… and the date) with **Forget this phone**: its cookie opens nothing any more. `phones.json` (in the `lan` folder) keeps only a hash of each phone's token. |

### Once per phone: install the certificate

The PC's card says *First time on this phone? Install the certificate first:*
`http://192.168.1.20:8089/`. Open it on the phone, tap **Download the certificate**, then:

- **Android**: in the **phone's Settings app** (the gear on the home screen, not Chrome's
  settings). Do not tap *Open* after the download: Android 11 and later refuse it (*cannot
  install CA certificates*).
  1. **Samsung**: *Settings › Security and privacy › More security settings › Install from
     device storage › CA certificate › Install anyway*.
     **Other phones** (Pixel…): *Settings › Security › More settings › Encryption and
     credentials › Install a certificate › CA certificate › Install anyway*.
  2. Open the *Download* folder and tap `media-hygiene-ca.crt`.

  Android warns that the network may be monitored: it is your own PC.
  Downloading is not enough, and **CA certificate** matters (not *VPN and app*, not *Wi-Fi*).
  Check: *Trusted credentials › User* shows *Media Hygiene (this PC)*, and Chrome shows `https`
  without a red cross; otherwise *Install* fails (*This app cannot be installed*).
- **iPhone, iPad** (in Safari): allow the profile, install it in *Settings › General › VPN and
  device management*, then turn **Media Hygiene** on in *Settings › General › About ›
  Certificate trust settings*.

Then tap **Done: open Media Hygiene**, and pair with the code as above. When the PC's address
changes, `mh` signs a new certificate for it with the same authority: nothing to install
again. Ask your box for a **DHCP reservation** of the PC to keep the same address, and the
phone's bookmark. The [slideshow](slideshow.md) stays in plain HTTP: a TV cannot install a
certificate.

### Media Hygiene as an app on the phone

Once paired over HTTPS, the phone may keep the home page as an app, with the meerkat as its
icon: **Android** (Chrome) offers *Install app* (or ⋮ › *Add to Home screen*); on an
**iPhone**, Safari says how in one line: *Share*, then *Add to Home Screen*. The icon then
opens the home page directly, no QR code, no code. When Media Hygiene is not running on the
PC, the app shows the asleep meerkat, *Media Hygiene is asleep*, instead of the browser's
error, and opens the page again by itself once `mh` runs. The app keeps that page only:
never a photo. Nothing is published: no store, no account, no internet.

The phone cannot open the page? The card *On your phone* says why: *No home network found*
(the page opens for the PC alone, nothing fails), or Windows counts the Wi-Fi as **public**: set
it to private in *Settings › Network & Internet › Wi-Fi › Private network*. The first time,
Windows may ask about Docker Desktop once: tick **Private networks**, then **Allow**.

### Keep the page on this PC only

No phone at home, or you do not want one? Turn it off once, in `config.toml`:

1. In Windows PowerShell, open the file (`mh config` creates it the first time):

   ```powershell
   mh config
   notepad "$HOME\media-hygiene\config\config.toml"
   ```

2. Find the line `lan = true` (under `[review]`) and change it to:

   ```toml
   lan = false
   ```

3. Save, close Notepad, then type `mh update` (it writes the change into `mh` and the shortcut).

From then on, `mh` and its shortcut keep the page on this PC: no card *On your phone*, no
question from Windows' firewall. For one evening with a phone, type `mh --lan`: the page opens
to the Wi-Fi for that run only. To open it again every time, put back `lan = true`, then
`mh update`.

Windows PowerShell only for now.

## Your albums, on the phone

At home, show an album to the family **on your own phone**, without the TV: pair it once with
`mh --lan` (above), then open **Open the albums** on its home page (or, on the PC, *Share ›
Your albums*). The relatives look at your screen and pair nothing.

- **The list**: each [album](search.md#put-photos-in-an-album), its cover, its dates, its
  place and how many photos it holds.
- **An album**, as the big photo apps show it: a **cover** (the sharpest photo of the first
  day), the album's name, its dates and its place (named offline, from the photos' GPS), then
  a **mosaic** grouped by day, *Monday 10 July 2023 · Heraklion*.
- **A tap** opens the photo full screen; **a swipe** goes to the next or the previous one;
  **a tap** (or the phone's *Back*) closes it. The next photos are loaded in advance.
- **Videos** play in place, as on the TV: H.264 as it is; another format (HEVC, AVI) is
  labelled, never converted.
- 🔒 **Read only**: albums are made and changed on the PC (*➖ Take out*, *➕ Add*, *🖼 Cover*,
  [the albums' reference](../reference-albums.md)); the phone shows them.

| | |
|---|---|
| Your photos | 🔒 Only read. The phone gets pictures sized for it (1440 pixels at most, kept in `/cache`), an original only with `[review] lan_phone_originals = true`. |
| What the phone reaches | The albums and **their** files; the rest of your library through *Search* and *Browse* only (read only). |
| Where | The home Wi-Fi only, while `mh` runs on the PC (said on the page). |

## The keyboard, the palette, the theme

| Key | What it does |
|---|---|
| <kbd>Enter</kbd> | When the page opens, runs the next step: its button has the focus. |
| <kbd>Ctrl</kbd>+<kbd>K</kbd> or <kbd>/</kbd> | *What do you want to do?*: every action and every space, found by everyday words (*phone*, *NAS*, *undo*), then the sections of the documentation (opened in a new tab); <kbd>↑</kbd> <kbd>↓</kbd> choose, <kbd>Enter</kbd> runs. |
| <kbd>↑</kbd> <kbd>↓</kbd> | In the sidebar, from one space to the next (one <kbd>Tab</kbd> stop for the whole sidebar). |
| <kbd>?</kbd> | The keys. |
| <kbd>Esc</kbd> | Closes what is open. |

A keyboard-only walk: <kbd>Tab</kbd> once shows *Skip to the content*; <kbd>Enter</kbd> on it
jumps over the sidebar. <kbd>Shift</kbd>+<kbd>Tab</kbd> back to the sidebar, <kbd>↓</kbd> to
*Clean*, <kbd>Enter</kbd> opens its page. <kbd>Ctrl</kbd>+<kbd>K</kbd>, type *phone*,
<kbd>Enter</kbd>: the phone's step runs. Reload the page: <kbd>Enter</kbd> runs the next step.
The focus ring shows only for the keyboard; the toasts are read by screen readers.

The theme follows Windows (light or dark); **Auto**, **Light** and **Dark** at the bottom of the
sidebar choose for this browser. Animations stop when Windows asks for reduced motion. The
fonts and pictures come from the image itself: the page asks nothing of any other site.

## Options

| Option | What it does |
|---|---|
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- The page answers only at `127.0.0.1` or `localhost` (and, under `mh --lan`, at the PC's address
  to a paired phone), and only to its own buttons: another site cannot choose a step for you.
- Closing the page's browser tab, or Ctrl+C in the terminal stops the page
  and gives the prompt back; an audit running stops between two files. A closed tab is noticed
  about 10 seconds later (*The home page's tab was closed: the home page stopped.*); a reload, or
  a tab left in the background, never stops it.
- The steps are read again from the tool's folders each time the page loads: what another
  window did shows at the next reload. A button of a page drawn before such a change is refused
  (*The steps changed since the page was shown*) and the page shows the steps again.
- `config.toml` is read again when you change it, the next audit run from the page included. A
  typo that makes it unreadable is said at the top of the page (*…config.toml cannot be read: …
  The last good settings stay until it is fixed.*); the line goes once the file is fixed.
- If the page stops unexpectedly (a bug, Docker out of memory), `mh` starts it again by itself
  (*The home page stopped unexpectedly: started again.*); a second stop within a minute gives the
  prompt back.

## Go further

- [`menu`: the same steps in the terminal](menu.md)
- [`status`: where you are, in one second](status.md)

## The built-in help

<details>
<summary><code>home --help</code></summary>

<!-- capture: help-home.txt -->
```text
 Usage: media-hygiene home [OPTIONS]

 🔒 Read-only: never changes your photos. The home page in your browser: where
 you are, the next step as a button, every step of the guides, the reports.

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
