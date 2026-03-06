from abc import ABC, abstractmethod
from typing import Dict, List

from .models import CommandResult


class Runner(ABC):
    @abstractmethod
    def run(self, host: str, command: List[str], timeout_s: int) -> CommandResult:
        raise NotImplementedError

    def run_many(self, commands_by_host: Dict[str, List[str]], timeout_s: int) -> Dict[str, CommandResult]:
        results: Dict[str, CommandResult] = {}
        for host, cmd in commands_by_host.items():
            results[host] = self.run(host=host, command=cmd, timeout_s=timeout_s)
        return results
