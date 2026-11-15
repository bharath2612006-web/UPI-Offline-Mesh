from threading import Lock
from time import time
from app.config import IDEMPOTENCY_TTL_SECONDS

class IdempotencyService:
    """Process-local atomic claim; DB unique constraint is the durable second line of defence."""
    def __init__(self):
        self._seen = {}
        self._lock = Lock()

    def claim(self, packet_hash: str) -> bool:
        now = time()
        with self._lock:
            self._seen = {k: v for k, v in self._seen.items()
                          if now - v < IDEMPOTENCY_TTL_SECONDS}
            if packet_hash in self._seen:
                return False
            self._seen[packet_hash] = now
            return True

    def reset(self):
        with self._lock:
            self._seen.clear()
