import os
import time
from typing import Any, Optional, Tuple

# TTL padrão curto e configurável via variável de ambiente
DEFAULT_TTL = int(os.environ.get("CACHE_TTL_SEC", "300"))  # 5 minutos por padrão


class SimpleCache:
    def __init__(self, default_ttl: int = DEFAULT_TTL):
        self._store: dict[str, Tuple[Any, float, int]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            self.misses += 1
            return None
        value, ts, ttl = entry
        if (time.time() - ts) < ttl:
            self.hits += 1
            return value
        # Expirado: remove e contabiliza miss
        self._store.pop(key, None)
        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = (value, time.time(), ttl or self.default_ttl)

    def clear(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0


# Instância global simples para uso nos roteadores
cache = SimpleCache()