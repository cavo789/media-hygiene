# mh-measure.ps1 - the measurements only the maintainer's Windows + Docker Desktop can give.
#
# Runs, one after the other, the measurements the PARTIAL TODOs wait for, and writes the lines
# that matter to one text file Claude reads afterwards (from the devcontainer, through a
# read-only mount of C:\). Windows PowerShell 5.1, ASCII only (an accented byte breaks the
# console code page, TODO 0098).
#
#   1. a first audit of a test folder with duplicates, fresh cache   (0148: checks, fingerprints;
#      0159: its estimate of the checks, against their time per step)
#   2. the same audit again, nothing changed                         (warm audit, 0159 line)
#   3. one photo added to the big flat folder, audit                 (0153: listing)
#   4. a folder renamed, audit                                        (0147: files followed)
#   5. clean, then undo, then audit                                   (0149 clean time, 0156)
#      clean --delete, then undo: no move, against 5a                 (0150: share of the moves)
#      clean, then undo, one file at a time ([clean] workers = 1)     (0149: K = 1 against 5a/5b)
#   6. C:\Photos read-only with your usual cache, audit twice         (0147 one-time pass, 0152)
#      people --sample 200 on it: seconds per photo, faces            (0058; adds the faces of
#      those 200 photos and the two face models, 39 MB, to that cache)
#   7. classify, sort (NTFS file ids before/after), undo of the test folder  (0138: moves on NTFS)
#      sort, then undo, one file at a time ([clean] workers = 1)       (0163: 4 at once against 7b)
#   8. each file operation of a sort by link and its undo, alone           (0138: what is refused)
#   9. the mh launcher around docker run, in the old console (conhost)    (0184 accents, 0179 awake,
#      0185 title and sound, 0178 browser): asks what you heard and saw; the awake check
#      (powercfg /requests) needs an administrator PowerShell
#  10. mh open, mh shortcut, mh explorer (right-click a folder), each read back   (0175, 0180,
#      0181): asks what you saw; your own Media Hygiene shortcut or entry is put back after
#  11. mh folders add / remove (mh rewrites its own file), a new terminal audits the folder added;
#      mh update: with the local image it says there is nothing to pull; then, if you agree, the
#      local image tagged cavo789/media-hygiene plays an older one and mh update pulls the
#      published one, writes mh again and says both versions                (0176, 0177)
#  12. clean of photos on another drive (-OtherDrive, else the first drive but C: with 2 GB
#      free), quarantine on C:: the line before the question names both drives, the size and
#      C:'s free space (checked against Windows'); quarantine on that drive: no line   (0182)
#  13. 1 GB set aside from another drive (-OtherDrive, else the first drive but C: with 3 GB
#      free): to the quarantine on C: (copy E: -> C:), then to that drive's own quarantine
#      /quarantine/x (copy E: -> E:): wall time of each clean and undo; then undo without
#      the drive's quarantine mounted must refuse, naming the drive                  (0183)
#
# The test folder is a copy of a few photos of C:\Photos, made under -Work and removed at the
# end (-Keep to keep it); C:\Photos itself is only read. Build the image from the branch to
# measure first (devcontainer: `build`, or `docker build --tag media-hygiene .`).
#
# Usage (PowerShell, from any folder):
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Count 3000 -Image media-hygiene
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 8 -Count 10   (step 8 only)
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 9 -Count 300  (step 9 only)
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 10 -Count 20  (step 10 only)
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 11 -Count 20  (step 11 only)
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 12 -Count 20 -OtherDrive E:
#   powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 13 -Count 20 -OtherDrive E:

param(
    [string]$Photos = "C:\Photos",
    [string]$Work = (Join-Path $env:TEMP "mh-measure"),
    [int]$Count = 2000,
    [string]$Image = "media-hygiene",
    [string]$Cache = "media-hygiene-cache",
    [switch]$Keep,
    [string]$Only = "",
    [string]$OtherDrive = ""
)

$ErrorActionPreference = "Stop"
# The tool writes UTF-8 (emoji, table borders): read docker's output as such, not as the
# console code page, which garbles them.
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
$outDir = Join-Path $HOME "media-hygiene"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$out = Join-Path $outDir "measures-$stamp.txt"
$wanted = 'Time per step|Duration|Report written|moved or renamed|unchanged folder|Reading 128 KB|copies|Error|first time|Next audit|No new or changed|per photo|A full run|faces in|Left out|Source folders removed|will be copied|Not enough room|not mounted'

function Log([string]$text) {
    Add-Content -Path $out -Value $text -Encoding UTF8
    Write-Host $text
}

function Measure-Mh([string]$title, [string[]]$mounts, [string[]]$arguments) {
    Log ""
    Log "== $title"
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $lines = & docker run --rm --env COLUMNS=160 @mounts $Image --locale en --verbosity verbose @arguments 2>&1
    $watch.Stop()
    foreach ($line in $lines) {
        $text = "$line"
        if ($text -match $wanted) { Log ("   " + $text.Trim()) }
    }
    Log ("   wall time: {0:N1} s, exit code {1}" -f $watch.Elapsed.TotalSeconds, $LASTEXITCODE)
}

# -Only "7,8": with -File, PowerShell hands the list over as one string; split it here.
$steps = @($Only -split '[,; ]+' | Where-Object { $_ -ne "" })

function Wanted([int]$group) {
    return ($steps.Count -eq 0) -or ($steps -contains "$group")
}

# NTFS file ids (no administrator rights needed): a file renamed or linked keeps its id, a
# copy gets a new one. That is what proves 0138 (sort moves without copying).
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
public static class MhFileId {
    [StructLayout(LayoutKind.Sequential)]
    struct Info {
        public uint Attributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME Created, Accessed, Written;
        public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow;
    }
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool GetFileInformationByHandle(IntPtr handle, out Info info);
    public static string Of(string path) {
        using (FileStream stream = File.Open(path, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete)) {
            Info info;
            if (!GetFileInformationByHandle(stream.SafeFileHandle.DangerousGetHandle(), out info)) {
                throw new IOException("GetFileInformationByHandle: " + Marshal.GetLastWin32Error());
            }
            return String.Format("{0:x8}{1:x8}", info.IndexHigh, info.IndexLow);
        }
    }
}
'@

function FileIds([string]$root) {
    $ids = @{}
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File) {
        $ids[[MhFileId]::Of($file.FullName)] = $file.FullName
    }
    return $ids
}

# --- the test folder: photos copied twice (exact duplicates), one big flat folder --------
$data = Join-Path $Work "data"
$tool = Join-Path $Work "tool"
if (Test-Path $Work) {
    if (-not (Test-Path (Join-Path $Work ".mh-measure"))) {
        throw "$Work exists and was not made by this script: choose another -Work."
    }
    Remove-Item -Recurse -Force $Work
}
foreach ($folder in "data\flat", "data\copies", "tool\journal", "tool\quarantine", "tool\reports") {
    New-Item -ItemType Directory -Force -Path (Join-Path $Work $folder) | Out-Null
}
Set-Content -Path (Join-Path $Work ".mh-measure") -Value "made by mh-measure.ps1"

Log "mh-measure $stamp - image $Image $(docker image inspect $Image --format '{{.Id}}')"
Log "Copying $Count photos of $Photos into $data (twice: exact duplicates)..."
$picked = Get-ChildItem -Path $Photos -Recurse -File -Include *.jpg, *.jpeg |
    Where-Object { $_.FullName -notmatch '\\#recycle\\' } | Select-Object -First $Count
$index = 0
foreach ($photo in $picked) {
    $index++
    $name = "{0:D6}-{1}" -f $index, $photo.Name
    Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $data "flat\$name")
    Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $data "copies\$name")
}
$megabytes = ($picked | Measure-Object -Property Length -Sum).Sum * 2 / 1MB
Log ("Test folder: {0} files, {1:N0} MB" -f ($index * 2), $megabytes)

$volume = "mh-measure-cache"
docker volume rm -f $volume | Out-Null
docker volume create $volume | Out-Null
$readOnly = @("-v", "${data}:/data/c/measure:ro", "-v", "${volume}:/cache")
$writable = @(
    "-v", "${data}:/data/c/measure",
    "-v", "${volume}:/cache",
    "-v", "$(Join-Path $tool 'journal'):/journal",
    "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
    "-v", "$(Join-Path $tool 'reports'):/reports"
)

# --- 1-5: the test folder ------------------------------------------------------------------
if (Wanted 1) {
    Measure-Mh "1. first audit, fresh cache (0148)" $readOnly @("audit")
}
if (Wanted 2) {
    Measure-Mh "2. audit again, nothing changed" $readOnly @("audit")
}
if (Wanted 3) {
    Copy-Item -LiteralPath $picked[0].FullName -Destination (Join-Path $data "flat\new-photo.jpg")
    Measure-Mh "3. one photo added to a folder of $Count (0153)" $readOnly @("audit")
}
if (Wanted 4) {
    Rename-Item -LiteralPath (Join-Path $data "copies") -NewName "copies renamed"
    Measure-Mh "4. a folder renamed in Explorer (0147)" $readOnly @("audit")
}
if (Wanted 5) {
    Measure-Mh "5a. clean of the duplicates (0149)" $writable @("clean", "--yes")
    Measure-Mh "5b. undo of that clean" $writable @("undo", "--yes")
    Measure-Mh "5c. audit after undo: nothing decoded again (0156)" $readOnly @("audit")
    Measure-Mh "5d. clean --delete: no move, against 5a (0150)" $writable @("clean", "--yes", "--delete")
    Measure-Mh "5e. undo of that clean: copies rebuilt from the kept files" $writable @("undo", "--yes")
    $oneAtATime = @("--env", "MEDIA_HYGIENE_CLEAN__WORKERS=1") + $writable
    Measure-Mh "5f. clean, one file at a time: against 5a (0149)" $oneAtATime @("clean", "--yes")
    Measure-Mh "5g. undo, one file at a time: against 5b (0149)" $oneAtATime @("undo", "--yes")
}

# --- 6: the real collection, read-only, with the usual cache -------------------------------
$real = @("-v", "${Photos}:/data/c/Photos:ro", "-v", "${Cache}:/cache")
if (Wanted 6) {
    Measure-Mh "6a. C:\Photos, first audit with this image (one-time 128 KB pass, 0147)" $real @("audit")
    Measure-Mh "6b. C:\Photos, warm audit (near duplicates, 0152)" $real @("audit")
    Measure-Mh "6c. C:\Photos, people --sample 200 (0058)" $real @("people", "--sample", "200")
}

# --- 7: sort on the test folder: moves within one NTFS mount (0138) --------------------------
# 7b and 7d print 'Time per step' (0170): counts, moves, cache update, move checks, manifest.
if (Wanted 7) {
    Measure-Mh "7a. classify the test folder" $writable @("classify")
    $before = FileIds $data
    Measure-Mh "7b. sort, the default proposal (0138: renamed or linked, not copied)" $writable @("sort", "--yes")
    $after = FileIds $data
    $kept = @($after.Keys | Where-Object { $before.ContainsKey($_) }).Count
    $moved = @($after.Keys | Where-Object { $before.ContainsKey($_) -and $before[$_] -ne $after[$_] }).Count
    Log ("   NTFS ids: {0} of {1} files kept their id ({2} at a new path: renamed or linked), {3} new ids (copied)" -f $kept, $after.Count, $moved, ($after.Count - $kept))
    Measure-Mh "7c. undo of that sort" $writable @("undo", "--yes")
    $back = FileIds $data
    $same = @($back.Keys | Where-Object { $before.ContainsKey($_) -and $before[$_] -eq $back[$_] }).Count
    Log ("   NTFS ids after undo: {0} of {1} files back at their first path with their first id" -f $same, $back.Count)
    $oneByOne = @("--env", "MEDIA_HYGIENE_CLEAN__WORKERS=1") + $writable
    Measure-Mh "7d. sort, one file at a time: against 7b, 4 at once (0163)" $oneByOne @("sort", "--yes")
    Measure-Mh "7e. undo of that sort" $writable @("undo", "--yes")
}

# --- 8: which file operations Docker Desktop's NTFS mount allows (0138: undo after a link) ----
# Each line: probe <scenario> <operation> ok|<errno name>. Same sequence as a sort by link,
# then its undo: renameat2(RENAME_NOREPLACE), link, unlink, rmdir, mkdir, then the way back.
if (Wanted 8) {
    $probeDir = Join-Path $tool "probe"
    New-Item -ItemType Directory -Force -Path $probeDir | Out-Null
    Set-Content -Path (Join-Path $probeDir "probe.py") -Encoding Ascii -Value @'
import ctypes, errno, os, time

ROOT = '/data/c/measure/probe'
LIBC = ctypes.CDLL(None, use_errno=True)


def renameat2(source, target):
    if LIBC.renameat2(-100, source.encode(), -100, target.encode(), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def create(path):
    with open(path, 'xb') as stream:
        stream.write(b'x' * 1000)


def attempt(label, action):
    try:
        action()
        print('probe', label, 'ok', flush=True)
    except OSError as exc:
        print('probe', label, errno.errorcode.get(exc.errno, exc.errno), flush=True)


def scenario(name, linked, remove_folder, pause):
    base = os.path.join(ROOT, name)
    old_dir, new_dir = os.path.join(base, 'from'), os.path.join(base, 'to')
    os.makedirs(old_dir)
    os.makedirs(new_dir)
    old, new = os.path.join(old_dir, 'a.jpg'), os.path.join(new_dir, 'a.jpg')
    if linked:
        create(old)
        attempt(name + ' sort-renameat2', lambda: renameat2(old, new))
        attempt(name + ' sort-link', lambda: os.link(old, new))
        attempt(name + ' sort-unlink', lambda: os.unlink(old))
    else:
        create(new)
    if remove_folder:
        attempt(name + ' sort-rmdir', lambda: os.rmdir(old_dir))
        attempt(name + ' undo-mkdir', lambda: os.mkdir(old_dir))
    time.sleep(pause)
    attempt(name + ' undo-renameat2', lambda: renameat2(new, old))
    attempt(name + ' undo-link', lambda: os.link(new, old))
    if os.path.lexists(old):
        attempt(name + ' undo-unlink-new', lambda: os.unlink(new))
    else:
        attempt(name + ' undo-create', lambda: create(old))
        attempt(name + ' undo-remove-created', lambda: os.unlink(old))
        attempt(name + ' undo-rename', lambda: os.rename(new, old))


def times(label, path):
    info = os.stat(path)
    print('probe', label, 'owner', info.st_uid, 'me', os.getuid(), flush=True)
    attempt(label + ' utime', lambda: os.utime(path, ns=(info.st_mtime_ns, info.st_mtime_ns)))


os.makedirs(ROOT)
create(os.path.join(ROOT, 'made-here.jpg'))
times('made-by-the-tool', os.path.join(ROOT, 'made-here.jpg'))
times('made-by-windows', os.path.join('/data/c/measure/flat', sorted(os.listdir('/data/c/measure/flat'))[0]))
scenario('fresh', linked=False, remove_folder=False, pause=0)
scenario('linked', linked=True, remove_folder=False, pause=0)
scenario('linked-rmdir', linked=True, remove_folder=True, pause=0)
scenario('linked-rmdir-wait', linked=True, remove_folder=True, pause=5)
'@
    Log ""
    Log "== 8. file operations on the NTFS mount (0138: undo after a move by link)"
    $probeRun = @("-v", "${data}:/data/c/measure", "-v", "${probeDir}:/probe:ro")
    $lines = & docker run --rm @probeRun --entrypoint python $Image /probe/probe.py 2>&1
    foreach ($line in $lines) { Log ("   " + "$line".Trim()) }
}

# --- 9: the mh launcher around docker run (0184, 0179, 0185, 0178) ---------------------------
# mh is written by the image under test, French, with the tool folders of the test folder.
if (Wanted 9) {
    $mhDir = Join-Path $tool "mh"
    New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image --locale fr launcher --photos $data > $mhFile
    $result = Join-Path $mhDir "probe.txt"
    $probe = Join-Path $mhDir "probe.ps1"
    Set-Content -Path $probe -Encoding Ascii -Value @'
param([string]$mh, [string]$result)
function Note([string]$text) { Add-Content -Path $result -Value $text -Encoding UTF8 }
Note ("   9a. console code page before mh: " + [Console]::OutputEncoding.CodePage)
. $mh
$menu = @(mh menu 2>&1 | ForEach-Object { "$_" })
$text = $menu -join "`n"
Note ("   9a. French menu holds accented letters: " + ($text -match '[\u00E0-\u00FC]') + "; an e-acute garbled as in code page 850: " + ($text -match '\u251C\u00AE'))
Note ("   9a. its first line: " + ($menu | Where-Object { "$_".Trim() } | Select-Object -First 1))
Note ("   9a. console code page after mh: " + [Console]::OutputEncoding.CodePage)
$Host.UI.RawUI.WindowTitle = "mh-measure"
mh audit
Note ("   9c. exit code " + $LASTEXITCODE + ", window title after mh audit: " + $Host.UI.RawUI.WindowTitle)
mh history | Out-Null
Note ("   9c. window title at the next mh call: " + $Host.UI.RawUI.WindowTitle)
'@
    Log ""
    Log "== 9. the mh launcher in the old console (0184, 0179, 0185, 0178)"
    Remove-Item -Force -ErrorAction SilentlyContinue $result
    $arguments = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$probe`" -mh `"$mhFile`" -result `"$result`""
    $child = Start-Process -FilePath conhost.exe -ArgumentList $arguments -PassThru
    $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $awake = $false
    while (-not $child.HasExited) {
        if ($admin -and ((powercfg /requests) -join " ") -match 'powershell') { $awake = $true }
        Start-Sleep -Seconds 1
    }
    if (Test-Path $result) { Get-Content -Path $result -Encoding UTF8 | ForEach-Object { Log $_ } }
    if ($admin) {
        $after = ((powercfg /requests) -join " ") -match 'powershell'
        Log ("   9b. awake request of powershell.exe during mh audit: {0}; still there after: {1}" -f $awake, $after)
    } else {
        Log "   9b. skipped: powercfg /requests needs an administrator PowerShell (run -Only 9 from one)"
    }
    $heard = Read-Host "9c. Did you hear a sound when mh audit ended in the other window? (y/n)"
    Log "   9c. sound heard at the end: $heard"
    $review = "-NoProfile -ExecutionPolicy Bypass -NoExit -Command . '$mhFile'; mh review"
    Start-Process -FilePath conhost.exe -ArgumentList "powershell.exe $review" | Out-Null
    $opened = Read-Host "9d. A window runs mh review: did your browser open on the review page by itself? (y/n; n/a if it said there is nothing to review)"
    Log "   9d. browser opened by mh review: $opened"
    Write-Host "Press Ctrl+C in the review window, then close it."
}

# --- 10: what mh does by itself, without docker run (0175, 0180, 0181) ----------------------
# mh open, mh shortcut, mh explorer: each one read back here; a Media Hygiene shortcut or
# right-click entry you already had is saved first and put back at the end.
if (Wanted 10) {
    $ErrorActionPreference = "Continue"
    $mhDir = Join-Path $tool "mh"
    New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $data > $mhFile
    . $mhFile
    Log ""
    Log "== 10. what mh does by itself (0175 open, 0180 shortcut, 0181 explorer)"
    $index = Join-Path $tool "reports\index.html"
    if (-not (Test-Path $index)) {
        $said = @(mh open 6>&1 | ForEach-Object { "$_" })
        Log ("   10a. mh open before any report says: " + ($said -join ' / '))
        mh audit | Out-Null
    }
    mh open
    $opened = Read-Host "10a. mh open: did your browser open the list of the reports? (y/n)"
    Log "   10a. browser opened on index.html by mh open: $opened"

    # 10b: the shortcuts, yours saved first.
    $shell = New-Object -ComObject WScript.Shell
    $links = @(foreach ($place in 'Desktop', 'Programs') { Join-Path ([Environment]::GetFolderPath($place)) 'Media Hygiene.lnk' })
    foreach ($link in $links) { if (Test-Path -LiteralPath $link) { Copy-Item -LiteralPath $link -Destination "$link.mh-measure" -Force } }
    $said = @(mh shortcut 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   10b. " + $line) }
    foreach ($link in $links) {
        $back = $shell.CreateShortcut($link)
        Log ("   10b. {0} exists: {1}; target {2}; arguments {3}" -f $link, (Test-Path -LiteralPath $link), $back.TargetPath, $back.Arguments)
    }
    $clicked = Read-Host "10b. Double-click Media Hygiene on your Desktop: does a PowerShell window open on the mh menu and stay open? (y/n)"
    Log "   10b. the icon opens the mh menu, window kept: $clicked"

    # 10c: the right-click entry, yours exported first; a folder whose name has a space and an apostrophe.
    $key = 'HKCU\Software\Classes\Directory\shell\MediaHygiene'
    $saved = Join-Path $Work "explorer-key.reg"
    $had = Test-Path -LiteralPath "HKCU:\Software\Classes\Directory\shell\MediaHygiene"
    if ($had) { & reg.exe export $key $saved /y | Out-Null }
    $said = @(mh explorer 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   10c. " + $line) }
    $command = (Get-Item -LiteralPath "HKCU:\Software\Classes\Directory\shell\MediaHygiene\command" -ErrorAction SilentlyContinue)
    Log ("   10c. registry command read back: " + $(if ($command) { $command.GetValue('') } else { '(none)' }))
    $odd = Join-Path $Work "L'ete 2019"
    New-Item -ItemType Directory -Force -Path $odd | Out-Null
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 3 | Copy-Item -Destination $odd
    explorer.exe $Work
    $menu = Read-Host "10c. In the Explorer window, right-click the folder L'ete 2019, then Media Hygiene: does the mh menu open, saying it also analyses that folder? (y/n)"
    Log "   10c. right-click opens the menu on the folder: $menu"
    $where = Read-Host "10c. Where was Media Hygiene: in the first menu, or under Show more options? (first/more)"
    Log "   10c. entry found in: $where (Windows $([Environment]::OSVersion.Version))"
    $audit = Read-Host "10c. In that window, type 1 (mh audit): does it analyse L'ete 2019 too (its 3 photos counted, its folder named)? (y/n)"
    Log "   10c. audit chosen from the right-click analyses the folder: $audit"

    # 10d: --remove, then what you had put back.
    $said = @(mh explorer --remove 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   10d. " + $line) }
    Log ("   10d. key still there after --remove: " + (Test-Path -LiteralPath "HKCU:\Software\Classes\Directory\shell\MediaHygiene"))
    if ($had) { & reg.exe import $saved 2>&1 | Out-Null }
    foreach ($link in $links) {
        Remove-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath "$link.mh-measure") { Move-Item -LiteralPath "$link.mh-measure" -Destination $link -Force }
    }
    Log "   10d. your own shortcuts and right-click entry, if any, are back; close the mh windows."
    $ErrorActionPreference = "Stop"
}

# --- 11: mh folders and mh update, mh rewriting its own file (0176, 0177) ------------------
# mh is written by the image under test; a folder added here is audited from a new terminal.
if (Wanted 11) {
    $ErrorActionPreference = "Continue"
    $mhDir = Join-Path $tool "mh11"
    New-Item -ItemType Directory -Force -Path $mhDir, (Join-Path $tool "config") | Out-Null
    $mhFile = Join-Path $mhDir "mh.ps1"
    $toolMounts = @(
        "-v", "${volume}:/cache",
        "-v", "$(Join-Path $tool 'config'):/config",
        "-v", "$(Join-Path $tool 'journal'):/journal",
        "-v", "$(Join-Path $tool 'quarantine'):/quarantine",
        "-v", "$(Join-Path $tool 'reports'):/reports"
    )
    & docker run --rm -e "MEDIA_HYGIENE_IMAGE=$Image" @toolMounts $Image launcher --photos $data > $mhFile
    . $mhFile
    Log ""
    Log "== 11. mh folders and mh update (0176, 0177)"
    $said = @(mh folders 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11a. " + $line) }
    $scanned = @(mh audit 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Media files scanned' })
    Log ("   11a. audit before add: " + ($scanned -join ' / '))

    # 11b: one more folder, then a new terminal (its own powershell.exe) loads the file and audits.
    $extra = Join-Path $Work "Extra photos"
    New-Item -ItemType Directory -Force -Path $extra | Out-Null
    Get-ChildItem -Path (Join-Path $data "flat") -File | Select-Object -First 3 | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $extra ("extra-" + $_.Name)) }
    $said = @(mh folders add $extra 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11b. " + $line) }
    Log ("   11b. the file names the folder: " + [bool](Select-String -LiteralPath $mhFile -SimpleMatch -Pattern $extra -Quiet))
    Log ("   11b. no temporary file left: " + (-not (Test-Path -LiteralPath "$mhFile.new")))
    $result = Join-Path $mhDir "probe.txt"
    $probe = Join-Path $mhDir "probe.ps1"
    Set-Content -Path $probe -Encoding Ascii -Value @'
param([string]$mh, [string]$result)
function Note([string]$text) { Add-Content -Path $result -Value $text -Encoding UTF8 }
. $mh
foreach ($line in @(mh folders 6>&1 | ForEach-Object { "$_" })) { Note ("   11b. new terminal: " + $line) }
$lines = @(mh audit 2>&1 | ForEach-Object { "$_" })
Note ("   11b. new terminal, exit code " + $LASTEXITCODE + ": " + (@($lines | Where-Object { $_ -match 'Media files scanned' }) -join ' / '))
'@
    Remove-Item -Force -ErrorAction SilentlyContinue $result
    Start-Process -FilePath powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$probe`" -mh `"$mhFile`" -result `"$result`"" -Wait
    if (Test-Path $result) { Get-Content -Path $result -Encoding UTF8 | ForEach-Object { Log $_ } }

    # 11c: refused folders leave the file as it was; 11d: the folder taken out again.
    $before = (Get-FileHash -LiteralPath $mhFile).Hash
    $inside = Join-Path $data "flat"
    $said = @(mh folders add $inside 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11c. add a folder inside another: " + $line) }
    Log ("   11c. mh.ps1 unchanged: " + ($before -eq (Get-FileHash -LiteralPath $mhFile).Hash))
    $said = @(mh folders remove $data 6>&1 | ForEach-Object { "$_" })
    $said += @(mh folders remove $extra 6>&1 | ForEach-Object { "$_" })
    $said += @(mh folders remove $data 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11d. " + $line) }

    # 11e: mh update. The local build has nothing to pull.
    $said = @(mh update 6>&1 | ForEach-Object { "$_" })
    foreach ($line in $said) { Log ("   11e. local image: " + $line) }
    $agree = Read-Host "11e. Try mh update for real? Your local image is tagged cavo789/media-hygiene, then the published one is pulled over that tag (y/n)"
    Log "   11e. real update tried: $agree"
    if ($agree -eq 'y') {
        & docker tag $Image "cavo789/media-hygiene:latest"
        & docker run --rm -e "MEDIA_HYGIENE_IMAGE=cavo789/media-hygiene" @toolMounts $Image launcher --photos $data > $mhFile
        . $mhFile
        $said = @(mh update 6>&1 | ForEach-Object { "$_" })
        foreach ($line in $said) { Log ("   11e. " + $line) }
        Log ("   11e. mh.ps1 still names the folder: " + [bool](Select-String -LiteralPath $mhFile -SimpleMatch -Pattern $data -Quiet))
        Log ("   11e. images: " + ((& docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' | Where-Object { $_ -match 'media-hygiene' }) -join ' / '))
    }
    $ErrorActionPreference = "Stop"
}

# --- 12: photos on another drive than the quarantine (0182) --------------------------------
# A few duplicates copied to X:\mh-measure-12 (removed at the end); the quarantine is the test
# folder's, on C:. 12a must show the line with X:, C: and C:'s free space; 12c must not.
$otherRoot = ""
if (Wanted 12) {
    if ($OtherDrive -eq "") {
        $found = Get-PSDrive -PSProvider FileSystem |
            Where-Object { $_.Name -ne 'C' -and $_.Free -gt 2GB } | Select-Object -First 1
        if ($found) { $OtherDrive = $found.Name + ":" }
    }
    Log ""
    if ($OtherDrive -eq "") {
        Log "== 12. skipped: no drive other than C: with 2 GB free (give one with -OtherDrive)"
    } else {
        $otherRoot = Join-Path ($OtherDrive.TrimEnd('\') + "\") "mh-measure-12"
        $otherData = Join-Path $otherRoot "data"
        $otherQuarantine = Join-Path $otherRoot "quarantine"
        foreach ($folder in "a", "b") {
            New-Item -ItemType Directory -Force -Path (Join-Path $otherData $folder) | Out-Null
        }
        New-Item -ItemType Directory -Force -Path $otherQuarantine | Out-Null
        foreach ($photo in ($picked | Select-Object -First 10)) {
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $otherData "a\$($photo.Name)")
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $otherData "b\$($photo.Name)")
        }
        $letter = $OtherDrive.Substring(0, 1).ToLower()
        $otherMounts = @(
            "-v", "${otherData}:/data/${letter}/mh-measure-12",
            "-v", "${volume}:/cache",
            "-v", "$(Join-Path $tool 'journal'):/journal",
            "-v", "$(Join-Path $tool 'reports'):/reports"
        )
        $onC = $otherMounts + @("-v", "$(Join-Path $tool 'quarantine'):/quarantine")
        $onOther = $otherMounts + @("-v", "${otherQuarantine}:/quarantine")
        Log ("== 12. data on $OtherDrive, Windows says C: has {0:N1} GB free" -f ((Get-PSDrive C).Free / 1GB))
        Measure-Mh "12a. clean, quarantine on C:: one line names $OtherDrive and C: (0182)" $onC @("clean", "--yes")
        Measure-Mh "12b. undo of that clean" $onC @("undo", "--yes")
        Measure-Mh "12c. clean, quarantine on ${OtherDrive}: no line expected (0182)" $onOther @("clean", "--yes")
        Measure-Mh "12d. undo of that clean" $onOther @("undo", "--yes")
    }
}

# --- 13: one quarantine per drive: copy E: -> C: against E: -> E: (0183) -------------------
# 1 GB of photos of -Photos copied twice to X:\mh-measure-13 (removed at the end): each clean
# sets 1 GB aside. 13a/13b: quarantine on C: only; 13c/13d: X:'s own on /quarantine/x too.
# If 13c is not faster than 13a, the gain of 0183 is the space on C: only (say it in the docs).
$driveRoot = ""
if (Wanted 13) {
    $drive13 = $OtherDrive
    if ($drive13 -eq "") {
        $found = Get-PSDrive -PSProvider FileSystem |
            Where-Object { $_.Name -ne 'C' -and $_.Free -gt 3GB } | Select-Object -First 1
        if ($found) { $drive13 = $found.Name + ":" }
    }
    Log ""
    if ($drive13 -eq "") {
        Log "== 13. skipped: no drive other than C: with 3 GB free (give one with -OtherDrive)"
    } else {
        $driveRoot = Join-Path ($drive13.TrimEnd('\') + "\") "mh-measure-13"
        $driveData = Join-Path $driveRoot "data"
        $driveQuarantine = Join-Path $driveRoot "quarantine"
        foreach ($folder in "data\a", "data\b", "quarantine") {
            New-Item -ItemType Directory -Force -Path (Join-Path $driveRoot $folder) | Out-Null
        }
        $bytes = 0
        $files = 0
        foreach ($photo in (Get-ChildItem -Path $Photos -Recurse -File -Include *.jpg, *.jpeg)) {
            if ($bytes -ge 1GB) { break }
            $name = "{0:D6}-{1}" -f $files, $photo.Name
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $driveData "a\$name")
            Copy-Item -LiteralPath $photo.FullName -Destination (Join-Path $driveData "b\$name")
            $bytes += $photo.Length
            $files++
        }
        $letter13 = $drive13.Substring(0, 1).ToLower()
        $driveMounts = @(
            "-v", "${driveData}:/data/${letter13}/mh-measure-13",
            "-v", "${volume}:/cache",
            "-v", "$(Join-Path $tool 'journal'):/journal",
            "-v", "$(Join-Path $tool 'reports'):/reports",
            "-v", "$(Join-Path $tool 'quarantine'):/quarantine"
        )
        $ownQuarantine = $driveMounts + @("-v", "${driveQuarantine}:/quarantine/${letter13}")
        Log ("== 13. {0} files ({1:N2} GB) to set aside on $drive13" -f $files, ($bytes / 1GB))
        Measure-Mh "13a. clean, quarantine on C: (copy $drive13 -> C:) (0183)" $driveMounts @("clean", "--yes")
        Measure-Mh "13b. undo of that clean (copy C: -> $drive13)" $driveMounts @("undo", "--yes")
        Measure-Mh "13c. clean, $drive13's own quarantine (copy $drive13 -> $drive13) (0183)" $ownQuarantine @("clean", "--yes")
        $aside = @(Get-ChildItem -Path $driveQuarantine -Recurse -File).Count
        Log "   13c. files in $driveQuarantine after the clean: $aside (expected: $files)"
        Measure-Mh "13d. undo without $drive13's quarantine mounted: must refuse, naming $drive13" $driveMounts @("undo", "--yes")
        Measure-Mh "13e. undo of that clean (copy $drive13 -> $drive13)" $ownQuarantine @("undo", "--yes")
    }
}

# --- clean up -------------------------------------------------------------------------------
if (-not $Keep) {
    if ($otherRoot -ne "") { Remove-Item -Recurse -Force $otherRoot }
    if ($driveRoot -ne "") { Remove-Item -Recurse -Force $driveRoot }
    Remove-Item -Recurse -Force $Work
    docker volume rm -f $volume | Out-Null
}
Log ""
Log "Done. Results: $out"
Log "Tell Claude: the measurements are in $out"
