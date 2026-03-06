import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from time import monotonic
from typing import Dict, List

from .models import CommandResult
from .runner import Runner


class SSHRunner(Runner):
    def __init__(
        self,
        *,
        max_workers: int = 16,
        connect_timeout_s: int = 5,
        strict_host_key_checking: str = "accept-new",
        known_hosts_file: str = "~/.cache/clusterinspector/known_hosts",
    ) -> None:
        self.max_workers = max(1, max_workers)
        self.connect_timeout_s = max(1, connect_timeout_s)
        self.strict_host_key_checking = strict_host_key_checking
        self.known_hosts_file = known_hosts_file

    def _build_ssh_prefix(self, host: str) -> List[str]:
        return [
            "ssh",
            "-T",
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={self.connect_timeout_s}",
            "-o",
            f"StrictHostKeyChecking={self.strict_host_key_checking}",
            "-o",
            f"UserKnownHostsFile={self.known_hosts_file}",
            host,
        ]

    def run(self, host: str, command: List[str], timeout_s: int) -> CommandResult:
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = monotonic()
        cmd = self._build_ssh_prefix(host) + command
        try:
            proc = subprocess.run(
                cmd,
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
            host=host,
            command=cmd,
            returncode=rc,
            stdout=out,
            stderr=err,
            started_at=started_at,
            finished_at=finished_at,
            duration_s=round(monotonic() - t0, 3),
            timeout=timeout_hit,
            error=error,
        )

    def run_many(self, commands_by_host: Dict[str, List[str]], timeout_s: int) -> Dict[str, CommandResult]:
        out: Dict[str, CommandResult] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futs = {
                pool.submit(self.run, host, cmd, timeout_s): host
                for host, cmd in commands_by_host.items()
            }
            for fut in as_completed(futs):
                host = futs[fut]
                try:
                    out[host] = fut.result()
                except Exception as exc:
                    out[host] = CommandResult(
                        host=host,
                        command=commands_by_host.get(host, []),
                        returncode=255,
                        stdout="",
                        stderr=str(exc),
                        started_at=datetime.now(timezone.utc).isoformat(),
                        finished_at=datetime.now(timezone.utc).isoformat(),
                        duration_s=0.0,
                        timeout=False,
                        error="internal_error",
                    )
        return out
