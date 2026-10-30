# 0503 — mh: the port check's false alarm on "Idle (process 0)", a refusal said in red

- Priority: P1
- Batch: launcher
- Depends: none
- Files: src/media_hygiene/cli/templates/mh_guards.ps1.j2, src/media_hygiene/cli/templates/mh.ps1.j2, src/media_hygiene/cli/templates/mh_guards.sh.j2, src/media_hygiene/services/launcher_guards.py, src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po, tests/unit/ (launcher tests), documentation/en|fr (mh page, troubleshooting), tests/measure/mh-measure.ps1

## Reported (maintainer, 2026-10-30, Windows PowerShell 5.1)

`mh --lan` printed, all in white, one block:

```
La page d'accueil s'ouvre aussi aux téléphones du réseau de la maison, à 192.168.0.218, …
Windows peut demander si Docker Desktop peut accepter des connexions : …
Média Hygiène tourne : sa page s'ouvre dans votre navigateur. Gardez cette fenêtre ouverte …
Le port des pages de mh est pris par un autre programme, Idle (processus 0) : fermez-le, …
```

No mh container existed (Docker Desktop: none running or stopped). A few seconds later,
the same `mh` worked without any change.

## Reported again (maintainer, 2026-10-30): from the home page, the page is lost

Ctrl+K on the home page → "mh review --intruders". PowerShell printed:

```
La prochaine fois, tapez-la directement : mh review --intruders
Le port des pages de mh est pris par un autre programme, Idle (processus 0) : fermez-le, …
Le port des pages de mh est pris par un autre programme, Idle (processus 0) : fermez-le, …
PS C:\Users\Christophe>
```

The home page no longer answers and `mh` has returned to the prompt: the user is left with
nothing. Reading `mh.ps1.j2` (not measured): a page step ends the home container, then the
loop of `mh` starts the step's container **at once on the same port** — exactly the moment
Windows still shows the socket under PID 0. So this is not a rare race: it is the normal
path of every page step chosen on the home page (`review*`, `places`, `browse`…), likely to
fail each time Docker Desktop is slow to release the port.

Three more defects seen there:
- **The refusal is printed twice** (the guard called twice? once by the step, once by the
  loop's relaunch of home? — find out, test it once).
- **A refusal inside the home loop ends `mh`**: the step could not start, so home must open
  again (the user is back where they were, with the refusal said on the page if possible),
  never a dead page and a prompt.
- Priority raised to the top of the launcher batch: it breaks the home page's main use.

## Analysis

1. **False alarm.** The check (0253, `mh_guards.ps1.j2`) takes every `Listen` socket of
   `Get-NetTCPConnection -LocalPort <port>` and names its `OwningProcess`. PID 0 is the
   *System Idle Process*: Windows reports it for a socket whose owner has just exited and
   that is not released yet (here, very likely Docker Desktop's relay of the previous mh
   container, closed seconds before — *estimated*, not measured). Nobody can "close" it;
   it frees itself. PID 4 (`System`, http.sys) is a real holder and must stay reported.
2. **Order and colour.** The "it runs / keep this window open" line comes *before* the
   refusal, and everything is plain `Write-Host`: the user reads success. The command did
   not run.
3. **Which port?** The line says "le port des pages de mh" without its number: the user
   cannot check it (nor know it is the `[review] port`, 8088 by default).

## To do

- PID 0 (and any PID whose process no longer exists): not a holder. Wait for the port to
  free itself — poll every 500 ms up to a short limit (named constant, ~10 s; propose
  whether it is a setting: no, per [few settings]), one line said while waiting
  ("Le port 8088 se libère encore (une page mh vient de s'arrêter)…"), then go on. Only if
  it is still held at the end: the refusal, without a process name ("Windows ne l'a pas
  encore libéré : attendez quelques secondes, puis retapez la commande").
- The relaunch from the home loop (a page step, and home again after it) waits for the port
  the same way, since mh itself just freed it; test it with the step-file path of 0210.
- In the home loop, a step refused by a guard reopens home (no exit to the prompt); the
  refusal said once. Test: a guard refusal inside the loop → home started again.
- Longer term, 0505/0506 (steps run beside the page): a page step served inside the home
  server would need no restart at all — check, per page, whether it can.
- Run all the guards **before** printing the LAN / firewall / "Média Hygiène tourne"
  lines, so a refusal is never preceded by a success line.
- Every refusal of the guards (`busy`, `held`, `open`, `unshared`) in red
  (`Write-Host -ForegroundColor Red`; in `mh.sh`, `tput setaf 1` when stdout is a
  terminal), with a non-zero exit code; informational ones (`stopped`, `shared`, `kept`)
  unchanged.
- Name the port in every port line: "Le port 8088 des pages de mh…" (`{port}` in the
  msgid), and keep "[review] port dans config.toml" as the way to change it.
- Same review of `mh_guards.sh.j2` (WSL/Linux: `ss -ltnp` may show no process for a socket
  being released).
- Tests: rendered `mh.ps1` contains the PID 0 skip, the wait loop, `-ForegroundColor Red`
  on refusals, guards before the "tourne" line; i18n_update + French.
- `tests/measure/mh-measure.ps1`: a step that runs an mh page, closes it, and starts
  another at once — records whether PID 0 shows up and how long the release takes
  (gives the wait limit a measured value).
- Docs (en + fr): the mh page's troubleshooting line for this message; `docs_screenshots`
  should run afterwards (console output changed).

## Where the user gains (also)

Before: choosing a page in Ctrl+K could kill the home page and leave the prompt. After: the
page opens a few seconds later, or home comes back with the reason.

## Where the user gains

Before: an mh launched right after another one is refused with an impossible advice
("close Idle"), in white after a success line. After: it waits a few seconds and starts;
a real refusal is red, alone, and names the port.
