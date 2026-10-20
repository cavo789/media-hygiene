# 0259 — `mh.sh` (WSL): a stick not mounted — say the line to type, never run `sudo`

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_drives.sh.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher_guards.py`, `tests/unit/test_launcher_wsl_drive.py`, `tests/measure/mh-measure.ps1`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

Follows 0254 (commit 12104de), decided in the review of feedback 2026-10-19-3 (2026-10-20):
`mh.sh` must not run `sudo` by itself, only say the line to type.

## Today

`_mh_drive` (`mh_drives.sh.j2`) finds a `/mnt/<x>` folder whose drive Windows has (`cmd.exe /c
vol X:`) but WSL has not mounted, then runs `sudo mkdir -p /mnt/x && sudo mount -t drvfs X:
/mnt/x -o uid,gid` (a password prompt possible), and `_mh_release` runs `sudo umount` after the
command. The documentation contradicts it already: `reference-troubleshooting.md` says "`mh`
never runs `sudo`" (Docker not started section) while its stick section describes the mount.

## To do

- Keep the detection (mountpoint + `cmd.exe /c vol`); in place of the mount, stop before
  `docker run` with one line naming the drive and the command to paste, e.g.
  *E: is plugged in but not mounted in WSL: type `sudo mkdir -p /mnt/e && sudo mount -t drvfs E:
  /mnt/e -o uid=$(id -u),gid=$(id -g)`, then the command again (↑ then Enter).* (exit code 2,
  nothing run). The uid/gid expanded to numbers in the printed line, so it pastes as is.
- Remove `_mh_release`, the `mounted` array and the `mh` → `_mh_command` wrapper if nothing else
  needs them (the drive label `marks` stays only if another reader uses it — check). Say in the
  same line, or a second one, how to unmount before ejecting (`sudo umount /mnt/e`)?
  Proposed: one line after the command when the folder is on a drive mounted after WSL started —
  to decide while implementing, keep it short.
- Texts in `launcher_guards.py` (`WslTexts`: `mount`, `failed`, `kept`, `stuck`) reduced to what
  remains; `i18n_update` + French.
- Docs en + fr: the stick paragraph of `reference-troubleshooting.md` ("Before each command,
  `mh` mounts it with `sudo`…") rewritten: `mh` says the line, you paste it once per plug-in.
- `mh-measure.ps1` step 11k: its logs say "as mh.sh does with sudo"; reword ("the line mh.sh
  says"). The step itself still answers the open question of 0254 (does a container started from
  WSL see the distribution's mount).
- Tests: the line printed, nothing run (no `sudo` in any rendered `mh.sh`: a test like 0257's
  forbidden-words check), native Linux / interop off unchanged.

## Gain

Estimated: 0 commands run with root rights by `mh.sh` (today 3: `mkdir`, `mount`, `umount`); cost
for the user: one paste per stick plug-in instead of nothing (at most a password today).
