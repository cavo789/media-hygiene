"""Run an external tool (`ffprobe`, `ffmpeg`) on a file, with a time limit."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class ToolRun:
    """What a tool printed, and how it ended."""

    returncode: int
    stdout: bytes
    stderr: bytes


async def run_tool(command: Sequence[str], seconds: float) -> ToolRun | None:
    """Run a command to completion, killing it when it takes too long.

    Args:
        command: The executable and its arguments.
        seconds: The time limit.

    Returns:
        What it printed and its exit code, or None when it was stopped.
    """
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        async with asyncio.timeout(seconds):
            stdout, stderr = await process.communicate()
    except TimeoutError:
        process.kill()
        await process.wait()
        return None
    return ToolRun(process.returncode or 0, stdout, stderr)
