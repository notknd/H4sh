from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass


@dataclass
class CommandResult:
    command: list[str]
    stdout: str
    stderr: str
    returncode: int


async def run(command: list[str], timeout: int = 90) -> CommandResult:
    """Run a fixed argv list without a shell and place a cap on output/time."""
    if not command or shutil.which(command[0]) is None:
        raise FileNotFoundError(f"Ferramenta indisponível: {command[0] if command else '?'}")
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        process.kill()
        await process.communicate()
        raise TimeoutError(f"Comando excedeu {timeout}s e foi interrompido.")
    return CommandResult(command, out.decode(errors="replace")[:100_000], err.decode(errors="replace")[:20_000], process.returncode)
