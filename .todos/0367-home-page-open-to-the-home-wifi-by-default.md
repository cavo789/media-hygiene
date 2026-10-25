# 0367 — The home page open to the home Wi-Fi by default: the QR code always there

- **Priority**: High
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_lan.ps1.j2`, `src/media_hygiene/services/launcher_lan.py`, `src/media_hygiene/services/home_lan.py`, `src/media_hygiene/review/lan.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/home_texts.py`, `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/config/review_settings.py`, `src/media_hygiene/config/templates/`, `tests/unit/test_home_lan.py`, `tests/measure/mh-measure.ps1`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`

## Context

Maintainer, 2026-10-25: "I want to connect easily from my phone: a QR code on the home page, I
scan it and from the sofa I see my photos, run a search…". The QR code exists since 0269, but
only under `mh --lan`, typed in PowerShell. The typical user (*JohnDoe*) starts mh from the
**desktop shortcut** and does not know what PowerShell is: he never sees the QR code.

The maintainer's reading of what opening by default loses (decided 2026-10-25):

- `mh` is started on purpose and never runs all the time: the opening lasts one session.
- The guests of the house have neither the address nor the code: the pairing (8-digit code, a new
  one at each start, 5 wrong codes close it, 0269) stays the protection.
- The firewall: Windows asks once per program ("Windows Security Alert", the answer kept as a
  rule) — **to check** on the maintainer's PC, never measured here.

## What to do

1. **Open by default.** `mh` alone and the desktop shortcut start the home page as `mh --lan`
   does today: the port published on the PC's private address too (never every interface, never a
   public address), the pairing secret drawn, the QR card shown in the sidebar.
   `mh --lan` stays accepted (same as `mh`: the docs, the measures and the user's habits).
2. **A setting to turn it off**: `[review] lan = true` in `config.toml` (an office PC, a shared
   network). It follows the precedent of `[review] port`: written into `mh.ps1` at `launcher` /
   `mh update` (the launcher runs on the host, before any container reads `config.toml`); the
   default `config.toml` template explains it in one comment. Off: the home page as before 0269,
   the card absent. `slideshow --lan` unchanged (the TV pairing is its own step).
3. **Never fail because of the network.** Today `mh --lan` stops with code 1 when no private
   address is found (`t.none`). By default, mh opens the home page anyway, for the PC alone; the
   card says why the phone cannot come (*No home network found: the phone cannot open this
   page*), never PowerShell.
4. **Say the problems on the page, not in the PowerShell window** (JohnDoe does not read it):
   - Windows counts the Wi-Fi as **public** (already detected by `_mh_lan_address`): passed to the
     page (an env var beside the address and the secret) and shown on the card in plain words,
     with where to click (*Settings › Network & Internet › Wi-Fi › Private network*).
   - The firewall prompt: one line on the card, *If Windows asks about Docker Desktop: tick
     Private networks, then Allow*. A rule that **blocks** Docker Desktop (a Cancel clicked once):
     whether `Get-NetFirewallRule` / `Get-NetFirewallApplicationFilter` can find it without admin
     rights is **to check**; if so, say it on the card with how to undo it.
5. **Tests**: the launcher template under each case (setting on/off, no private address, public
   network) gives the right `docker run` options and env; the page shows the card, the public
   warning and the no-network line; `lan = false` gives the pre-0269 page. Unit tests on the
   rendered `mh.ps1` text, like the existing ones of 0269.
6. **Docs en + fr**: `home.md` (section *From a phone of the home Wi-Fi*: by default now, the
   setting to turn it off, the firewall once), `launcher.md` (the `mh --lan` row), the reference
   of `[review]`. Screenshots stale: say that `docs_screenshots` should run.
7. **`mh-measure.ps1` step 29**: start by the shortcut, not `mh --lan`; ask whether the firewall
   prompt showed, then start a second time and ask whether it came back. The maintainer runs it
   after the implementation: it confirms the firewall lines of step 4, it does not block the work.

## Out of scope

- Search and browse from the phone: 0356 then 0360 (the pairing in front of every page). This TODO
  makes the QR code reachable; those make the sofa useful.

## Acceptance

- JohnDoe double-clicks the shortcut: the home page shows the QR code; his phone scans it, types
  nothing, and opens the home page.
- On a network Windows counts as public, the card says so and how to change it; no PowerShell
  message needed.
- `[review] lan = false` + `mh update`: no port on the home network, no card.

## Gain

Before: the phone needs `mh --lan` typed in PowerShell (JohnDoe: never). After: the QR code on
every home page started by the shortcut, one scan (estimated: from 0 % of shortcut users reaching
the phone pairing to every user whose Wi-Fi Windows counts as private).
