import socket
import subprocess
from datetime import datetime, timezone
from time import monotonic
from typing import List

from .models import CommandResult
from .runner import Runner


class LocalRunner(Runner):
    def run(self, host: str, command: List[str], timeout_s: int) -> CommandResult:
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = monotonic()
        actual_host = socket.gethostname().split(".", 1)[0]
        effective_host = host or actual_host
        try:
            proc = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=max(1, timeout_s),
                check=False,
            )
            timeout_hit = False
            error = ""
            rc = proc.returncode
            out = proc.stdout or ""
            err = proc.stderr or ""
        except FileNotFoundError as exc:
            timeout_hit = False
            error = "not_found"
            rc = 127
            out = ""
            err = str(exc)
        except subprocess.TimeoutExpired as exc:
            timeout_hit = True
            error = "timeout"
            rc = 124
            out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            err = (exc.stderr or "") if isinstance(exc.stderr, str) else ""

        finished_at = datetime.now(timezone.utc).isoformat()
        return CommandResult(
            host=effective_host,
            command=command,
            returncode=rc,
            stdout=out,
            stderr=err,
            started_at=started_at,
            finished_at=finished_at,
            duration_s=round(monotonic() - t0, 3),
            timeout=timeout_hit,
            error=error,
        )
