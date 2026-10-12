# 0. Install Docker

[Documentation](../README.md) › Start, before step 1 · 🇫🇷 [Français](../../fr/start/00-install-docker.md)

media-hygiene is not installed like a usual program: it comes as a Docker *image*, a box that
already holds everything it needs (Python, the photo and video decoders…). Docker is the program
that opens that box on your computer. You install Docker **once**; then every `docker run …`
command of this guide downloads and starts the tool by itself.

Already done? `docker run --rm hello-world` prints *Hello from Docker!*: go straight to
[step 1](01-first-audit.md).

## On Windows

You need Windows 10 or 11, 64-bit, up to date, and about 5 GB of free disk space for Docker and
the tool.

### 1. Install Docker Desktop

1. Download **Docker Desktop for Windows** from
   [docker.com](https://www.docker.com/products/docker-desktop/) (the *AMD64* version on almost
   every PC; *ARM64* only on a Windows on ARM computer, such as a Surface with a Snapdragon
   processor).
2. Run the installer and keep the option **Use WSL 2 instead of Hyper-V** ticked. WSL 2 is the
   small Linux that Windows runs for Docker: the installer sets it up for you.
3. Restart the computer when asked.

Or, in a PowerShell window, the same in one line:

```powershell
winget install --exact --id Docker.DockerDesktop
```

### 2. Start it

Open **Docker Desktop** from the Start menu. The first time, accept the terms of service; an
account is **not** needed: skip the sign-in. Wait until the bottom-left corner says
*Engine running*, in green.

> 💡 Docker Desktop must be **running** for every command of this guide: its whale icon 🐳 sits
> in the notification area, next to the clock. To have it ready every time, tick
> *Start Docker Desktop when you sign in to your computer* in *Settings › General*.

Docker Desktop is free for personal use, education and small businesses (fewer than 250
employees *and* less than 10 million dollars of yearly revenue); larger companies need a paid
subscription ([the terms](https://www.docker.com/pricing/faq/)).

### 3. Check it

Open a **new** PowerShell window (Start menu, type *PowerShell*) and type:

```powershell
docker run --rm hello-world
```

*Hello from Docker!* and a few lines of explanation: Docker works. Your drives `C:`, `D:`… are
reachable by Docker as they are: nothing more to set.

### If it does not work

| You see | What to do |
|---|---|
| *docker : The term 'docker' is not recognized* | The installation is not finished, or the window was opened before it: open a new PowerShell window. Restart the computer if needed. |
| *error during connect* … *The system cannot find the file specified* | Docker Desktop is not started: open it, and wait for *Engine running*. |
| *Virtualization support not detected*, or *WSL 2 requires an update* | Run `wsl --update` in PowerShell. If the message stays, virtualization is off in the firmware of the computer (BIOS/UEFI: *Intel VT-x*, *AMD-V* or *SVM*): the maker's documentation says how to turn it on. |
| Docker Desktop stays on *Starting the Docker Engine…* | Quit it (right-click on the whale › *Quit Docker Desktop*), then open it again; otherwise restart the computer. |

### With WSL

You prefer a WSL terminal (Ubuntu…)? Docker Desktop serves it too: in *Settings › Resources ›
WSL integration*, turn on your distribution, then type `docker run --rm hello-world` in it. Do
**not** also install Docker inside WSL with the Linux steps below: two Docker engines on one
computer get in each other's way.

## On Linux

On Linux, Docker Engine is enough: no Docker Desktop. The commands below are for **Ubuntu** and
**Debian**, and their relatives (Linux Mint, Pop!_OS…); for another distribution, follow
[the official instructions](https://docs.docker.com/engine/install/).

### 1. Install Docker Engine

Docker's own script adds its package repository and installs the latest version:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

You would rather see each step? [Install using the apt
repository](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository) does
the same by hand.

> ⚠️ On Ubuntu, avoid the **snap** package (`snap install docker`, or the box ticked while
> installing Ubuntu Server): by default, it cannot see the folders outside your home, such as a USB
> disk under `/media`. `snap list docker` says whether you have it; `sudo snap remove docker` removes it.

### 2. Use it without `sudo`

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

The first line starts Docker now and at every boot. The second one lets you run `docker` without
`sudo`: **log out and in again** for it to apply. Members of the `docker` group control Docker
completely, as an administrator would: only add yourself
([why](https://docs.docker.com/engine/security/#docker-daemon-attack-surface)).

### 3. Check it

```bash
docker run --rm hello-world
```

*Hello from Docker!*: Docker works.

### If it does not work

| You see | What to do |
|---|---|
| *permission denied while trying to connect to the Docker daemon socket* | The `docker` group is not active yet: log out and in again (or restart). |
| *Cannot connect to the Docker daemon … Is the docker daemon running?* | `sudo systemctl start docker`. |
| *docker: command not found* | The installation failed: run the script again and read its last lines. |

### Your first command on Linux

The guide shows Windows paths. On Linux, mount your folder under `/data`, followed by its own
path, and run as yourself so that the files the tool creates belong to you:

```bash
docker run --rm -it --user "$(id -u):$(id -g)" \
  -v "$HOME/Pictures:/data$HOME/Pictures:ro" \
  cavo789/media-hygiene audit
```

`$HOME/Pictures` becomes `/data/home/<you>/Pictures`, and the tool shows your folders by their
real path, `/home/<you>/Pictures`. A `\` at the end of a line continues the command on the next
one.

## On a Mac

Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) (*Apple
Silicon* or *Intel*, as *About This Mac* says), open it, then `docker run --rm hello-world` in
the Terminal. The commands of this guide follow the Linux pattern above.

## Updating

- **Docker**: Docker Desktop offers its updates itself; on Linux, your usual system updates
  (`sudo apt upgrade`) include it.
- **The tool**: `docker pull cavo789/media-hygiene` fetches its latest version.

---

[Documentation](../README.md) · Next: **[1. Your first audit](01-first-audit.md)** →
