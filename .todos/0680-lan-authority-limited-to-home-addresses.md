# 0680 — The phone's certificate authority can only vouch for home addresses, and its key never leaves the PC

- **Priority**: High
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_tls.py`, `src/media_hygiene/review/lan_ca_page.py`, `src/media_hygiene/review/templates/lan_ca.html.j2`, `src/media_hygiene/services/cache_backup.py`, `tests/unit/test_lan_https.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`
- **Needs maintainer**: one phone (Android, and an iPhone if at hand) installing the new authority: accepted or not

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

For HTTPS on the home network (0430), `mh` creates a certificate authority that each phone
**installs as trusted**. Read in `review/lan_tls.py` (2026-11-10): the authority is valid
20 years (`CA_DAYS = 7300`), made with `basicConstraints=CA:TRUE` and `keyUsage` only — **no
name constraints** — and its private key `ca.key` sits unencrypted (`-noenc`, mode 0600) in
`$HOME\media-hygiene\lan`.

Consequence: whoever copies `ca.key` (a malware on the PC, a backup of the home folder on a
shared NAS, an old disk given away) can sign a certificate for **any site** — the bank, the
mail — that every family phone having installed the authority will accept, for 20 years.
The risk is to the phones, well beyond the photos.

## Proposal

- **Name constraints** on the authority: `nameConstraints=critical,permitted;IP:10.0.0.0/8,
  IP:172.16.0.0/12,IP:192.168.0.0/16` (and no DNS name): a stolen key can then only vouch
  for private addresses. *To check before relying on it*: that Android's and iOS's
  validators enforce IP name constraints on a user-installed authority (documented for
  recent versions — not checked here), and that iOS still accepts the profile.
- A shorter life (e.g. 5 years) with the page saying when it ends, if the phones accept it
  as well.
- `ca.key` listed as **never copied**: not in `mh backup`'s archive, not sent by `mh push`,
  not under any synced folder; a test asserts `/lan` is outside what both read. Said in the
  docs: "this file is the key of your phones' trust; delete the `lan` folder to revoke —
  then remove the authority from each phone".
- Existing installs: the old authority keeps working; the PC's card offers *Renew the
  authority (safer)* with the steps per phone — never done silently (phones would break).
- The page that hands out `ca.crt` says in one line what installing it means.

## Acceptance

- [ ] A new authority carries the constraint (test reads it back with `openssl x509 -text`)
- [ ] A certificate for a public name signed by it is refused (test with `openssl verify`)
- [ ] Tried on a real phone (maintainer); result written here
- [ ] Docs EN + FR: what the authority is, how to revoke it

## Where the user gains

Before: a stolen key lets someone impersonate any site to the family's phones for 20 years.
After: at worst, a device of the home network — and only where the phone enforces the
constraint (to be confirmed by the check above).
