"""Drive the docker CLI from the end-to-end tests."""

from __future__ import annotations

import os
import subprocess
from typing import Final

IMAGE: Final = "media-hygiene:latest"
KINDS: Final = ("data", "journal", "quarantine", "reports", "cache")
# A container whose main process died of a signal exits with 128 + its number.
SIGNAL_EXIT: Final = 128
# Python prints its stack on a fatal signal (SIGSEGV...), unbuffered, to the logs.
FAULT_HANDLER: Final = ("--env", "PYTHONFAULTHANDLER=1")


def docker(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a docker CLI command and capture its output.

    Args:
        *args: Arguments after `docker`.

    Returns:
        The completed process.
    """
    command = ["docker", *args]
    # Trusted, fixed arguments built by the tests themselves.
    return subprocess.run(  # noqa: S603
        command, capture_output=True, text=True, check=False
    )


def _cpu_share() -> tuple[str, ...]:
    """Pass the developer's processor share on to the container.

    The `check`, `e2e` and `docs_screenshots` helpers set PYTHON_CPU_COUNT to run
    gently; without it, the tool in the container starts one worker per processor.

    Returns:
        The `docker run` options, none when PYTHON_CPU_COUNT is not set.
    """
    cpus = os.environ.get("PYTHON_CPU_COUNT", "")
    if not cpus.isdigit():
        return ()
    return ("--cpus", cpus, "--env", f"PYTHON_CPU_COUNT={cpus}")


def run_image(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a container to completion, then read its output from the logs.

    Some Docker setups (Docker Desktop through a mounted socket) cut the attached
    output after about a second; the logs are always complete. A container killed by a
    signal (TODO 0053: a rare exit 139 with no output) also reports its Docker state,
    and Python's fault handler prints where it stopped.

    Args:
        *args: Arguments after `docker run`: options, image, command.

    Returns:
        The exit code and the container's output.
    """
    started = docker("run", "--detach", *FAULT_HANDLER, *_cpu_share(), *args)
    container = started.stdout.strip()
    if started.returncode != 0:
        return started
    code = int(docker("wait", container).stdout.strip())
    logs = docker("logs", container)
    stderr = logs.stderr
    if code > SIGNAL_EXIT:
        state = docker("inspect", "--format", "{{json .State}}", container)
        stderr += f"\n[e2e] killed by a signal, container state: {state.stdout}"
    docker("rm", container)
    return subprocess.CompletedProcess(args, code, logs.stdout, stderr)


def tool(volumes: dict[str, str], *args: str, read_only_data: bool = False) -> str:
    """Run the image with every mount point.

    Args:
        volumes: Volume name per mount point.
        *args: The media-hygiene command line.
        read_only_data: Mount the data volume with `:ro`.

    Returns:
        The exit code, a newline, then the output.
    """
    mounts = []
    for kind, name in volumes.items():
        suffix = ":ro" if kind == "data" and read_only_data else ""
        mounts += ["-v", f"{name}:/{kind}{suffix}"]
    # --read-only: the image must work with an immutable root filesystem (the tmpfs
    # is inside the container, not a host temporary file).
    hardening = ["--read-only", "--tmpfs", "/tmp"]  # noqa: S108
    result = run_image(*hardening, *mounts, IMAGE, *args)
    return f"{result.returncode}\n{result.stdout}{result.stderr}"
