from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


DEFAULT_COMMAND_TIMEOUT_S = 8
DEFAULT_NODE_TIMEOUT_S = 45


@dataclass
class Deadline:
    end: datetime

    @classmethod
    def from_seconds(cls, seconds: int) -> "Deadline":
        return cls(end=datetime.now(timezone.utc) + timedelta(seconds=max(1, seconds)))

    def remaining_seconds(self) -> int:
        delta = self.end - datetime.now(timezone.utc)
        return max(1, int(delta.total_seconds()))

    def expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.end
