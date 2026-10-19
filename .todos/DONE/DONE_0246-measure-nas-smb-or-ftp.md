# 0246 — `mh-measure.ps1` step 21: the Synology NAS, reached by SMB or by FTP, from Windows and from Docker (read-only)

- **Priority**: High — the NAS import of 0245 is designed from what this step shows
- **Batch**: launcher
- **Depends**: —
- **Files**: `tests/measure/mh-measure.ps1`

## Context

0245 (copy into `C:\Photos` what only the NAS holds) needs to know how the container can read the
maintainer's Synology NAS. The maintainer said on 2026-10-19: it is reachable over FTP; whether it
also offers SMB (Windows file sharing) is unknown — "we will have to test". The NAS is plugged
into the PC only (no other machine on that link) and powered off most of the time; FTPS is not
needed (plain FTP is fine on that link: maintainer, 2026-10-19).

Three ways in, to try in that order (the first that works makes 0245 smallest):

1. **SMB, mounted by Docker**: a Docker CIFS volume (`docker volume create --driver local --opt
   type=cifs …`) or a mapped drive letter given to `-v`. If one works, 0205's read-only backup
   mount and 0204's comparison are reused as they are.
2. **SMB, from Windows only**: readable in Explorer but not by Docker — then `mh` would have to
   copy, which 0245 avoids.
3. **FTP, from the container** (Python's `ftplib`, in the image): 0245's FTP design.

None of this can run here: the NAS is on the maintainer's desk.

## What to do

A step 21 in `tests/measure/mh-measure.ps1`, run with `-Only 21`: Windows PowerShell 5.1, ASCII
only, no `-ExecutionPolicy Bypass` (Avast, 2026-10-16), results logged with `Log`. **It never
writes, moves, renames or deletes anything on the NAS**: listings and reads only; Docker volumes
mounted with `ro`. New parameters: `-Nas` (host name or IP address), `-NasShare` (default
`photo`, Synology's usual shared folder; the FTP path is the same name), `-NasUser`.

1. Ask to power the NAS on, wait until it answers (`Test-Connection`, up to 3 minutes, every
   10 s), log the time it took to answer and the PC's network adapter on that link (name, IPv4).
2. Ports, by `System.Net.Sockets.TcpClient` with a 2 s timeout (faster than
   `Test-NetConnection`): 21 (FTP), 445 and 139 (SMB), 22 (SSH), 5000/5001 (DSM web page); log
   each one, open or closed.
3. Password asked once (`Read-Host -AsSecureString`), **never logged**, kept in a
   `PSCredential`; for the container, put in a process environment variable `MH_NAS_PASSWORD`
   passed by name (`docker run -e MH_NAS_PASSWORD`, no value on the command line), removed at the
   end.
4. **SMB from Windows** (when 445 is open): `net view \\<Nas>` (log the share names);
   `New-PSDrive -PSProvider FileSystem -Root \\<Nas>\<NasShare> -Credential` (this session only);
   log the top folders (names only), the number of files and their size below the first year
   folder found (at most 2,000 files), the time of that listing, how many `@eaDir` folders; read
   20 photos whole into memory (`[IO.File]::OpenRead`, nothing copied to disk): MB/s.
5. **SMB from Docker**, two tries, each logged works / fails with Docker's message:
   - a. `net use` a free drive letter on the share, then
     `docker run --rm -v <letter>:\:/nas:ro --entrypoint python <Image> -c "<count files below /nas>"`;
     `net use <letter>: /delete` afterwards;
   - b. a CIFS volume `mh-measure-nas`:
     `docker volume create --driver local --opt type=cifs --opt device=//<IP>/<NasShare> --opt
     o=addr=<IP>,username=<NasUser>,password=…,ro,vers=3.0`, the same count with
     `-v mh-measure-nas:/nas:ro`, and the read speed of the same 20 photos from inside the
     container; then `docker volume rm` (the volume keeps the password in its options: never
     left behind). If `vers=3.0` fails, try `vers=2.1` and log which one worked.
6. **FTP from Docker** (when 21 is open): a small Python script run by
   `docker run --rm -e MH_NAS_PASSWORD --entrypoint python <Image> -c "$(script)"` (as step 7's
   probe), `ftplib` in passive mode: log the server's `FEAT` answer (whether `MLSD`/`MLST`,
   `REST STREAM`, `SIZE`, `MDTM`, `UTF8` are offered), the path of the share as FTP shows it,
   the listing of the first year folder (`MLSD`, else `LIST`: one sample line logged), its time
   for at most 2,000 files, whether names with accents come back right (one logged), the first
   and last 64 KiB of 10 photos (`REST` + `RETR`, aborted after 64 KiB: time per file), and
   20 photos read whole (MB/s). Only `FEAT`, `PWD`, `CWD`, `MLSD`/`LIST`, `SIZE`, `MDTM`, `REST`,
   `RETR`, `TYPE`, `PASV`/`EPSV`, `QUIT` are sent.
7. Clean up whatever happened (a `finally`): remove the drive, the `net use`, the Docker volume,
   the environment variable; log "nothing was written on the NAS".
8. A summary of three lines: "SMB in Docker: works with … / does not work", "SMB in Windows:
   …", "FTP in Docker: works, MLSD yes/no, … MB/s".

Update the step list at the top of the script and its usage lines (`-Only 21`).

## Explicit non-goals

- `mh` or the tool itself: 0245.
- Synology's own tools (Synology Drive, Photos, DSM API), SSH, NFS.
- Changing anything in the NAS settings: the step only reports what is on.

## Acceptance

- The step runs with `-Only 21`, writes nothing on the NAS, logs no password, removes the drive,
  the mapping and the Docker volume even after an error, is ASCII only, and is listed at the top
  of the script.
- DONE when the step is written: running it is the maintainer's part, recorded in 0245's
  `Needs maintainer`. Close with the exact commands to run it (fetch from the branch, then
  `.\mh-measure.ps1 -Only 21 -Count 1 -Nas <IP> -NasShare photo -NasUser <user>`).

## Gain

None by itself: it tells 0245 which of three designs to build (SMB mounted by Docker: mostly
reuse of 0204/0205; FTP: a new remote source), with the speeds to estimate a first comparison —
in one run of a few minutes (estimated: 20 + 20 photos read, two listings of at most 2,000 files).
