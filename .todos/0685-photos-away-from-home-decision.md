# 0685 — Photos away from home (at the in-laws'): the supported ways, and the network remembered as home

- **Priority**: High
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_address.py`, `src/media_hygiene/review/lan_problem.py`, `src/media_hygiene/cli/templates/mh_lan.ps1.j2`, `src/media_hygiene/services/launcher_lan.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`
- **Needs maintainer**: the decision between the options below; for the VPN option, a try with Tailscale on the PC and one phone

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The maintainer asks: "what if I expose mh on my network and let the photos be seen from a
web page — at my in-laws'?". What the code does today (read 2026-11-10):

- `mh --lan` (the default since 0367, `[review] lan = true`) publishes the page on the PC's
  **private IPv4** address only; a public address is refused, a network Windows counts as
  *Public* is said (`lan_problem`). Nothing in the docs mentions a VPN, a router's port
  forwarding, a reverse proxy (`grep` over `documentation/`).
- The server is built for a home network: a hand-written HTTP/1.1, no login beyond the
  pairing code, no rate limit yet. **It must never face the internet** — and nothing says so
  to a user tempted to forward a port on the router.
- The laptop taken to the in-laws' joins *their* Wi-Fi: a private address, so the page
  opens to that network as at home — a network with devices the user does not know — as
  soon as Windows calls it *Private*.
- A VPN address of Tailscale (100.64.0.0/10) is refused: Python's `is_private` is false for
  that range (*measured* 2026-11-10: `ipaddress.IPv4Address("100.64.0.1").is_private` → `False`).

## Options (to decide)

| | What the relatives use | Needs | Risk |
|---|---|---|---|
| A. The laptop travels | their TV / tablet on their Wi-Fi, guest role (see the guest TODO) | nothing new | their network's devices can reach the door: pairing + limits must hold |
| B. A private VPN (Tailscale / WireGuard) | their own device, the PC at home left on | accept 100.64.0.0/10 on demand (`[review] lan_vpn`), a doc page | the PC must stay on; a third party's software (to evaluate, not checked here) |
| C. An album taken along | a folder / USB stick with the album and a page that opens without a server (`album` hard links, `share`'s prepared copies) | check what `share` already makes | none for the library: only the copies travel |
| D. Port forwarding / reverse proxy | — | — | **refused**: said in the docs and by `mh` |

Proposed: A + C now (documented), B as a setting later if the try is good, D never.

## Proposal, whatever the option

- **The home network remembered**: the first time the page opens to a network, `mh` keeps
  what identifies it (gateway's MAC, as `mh.ps1` can read it; never sent anywhere). On
  another network the page stays **PC-only** and the card asks: *Open to this network (not
  your home)? — for this session only*. Paired-for-good cookies of home devices are not
  accepted on a network opened this way unless the user says so.
- The docs get "Seeing your photos away from home" (EN + FR): the table above in plain
  words, and the one sentence "never forward a port of your router to mh".
- `mh` refuses and explains when the address it is given is not private (already) — the
  sentence names the VPN option once B exists.

## Acceptance

- [ ] The decision recorded here; follow-up TODOs filed for B and C if chosen
- [ ] The home network remembered; a second network asks first (unit test of the decision,
      a step of `mh-measure.ps1` for the Windows part)
- [ ] The doc chapter EN + FR, linked from the PC's card

## Where the user gains

Before: no stated way, and a laptop that opens the library to any network Windows calls
private. After: a documented, safe way to show photos at relatives', and a door that opens
by itself only at home.
