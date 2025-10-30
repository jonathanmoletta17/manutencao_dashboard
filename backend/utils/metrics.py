import logging
from typing import Dict, Optional

_counters: Dict[str, int] = {}
logger = logging.getLogger(__name__)

def increment(name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
    key = _format_key(name, tags)
    _counters[key] = _counters.get(key, 0) + value
    logger.info("metric.increment name=%s value=%d tags=%s total=%d", name, value, tags or {}, _counters[key])

def record_timing(name: str, elapsed_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
    logger.info("metric.timing name=%s elapsed_ms=%.2f tags=%s", name, elapsed_ms, tags or {})

def _format_key(name: str, tags: Optional[Dict[str, str]]) -> str:
    if not tags:
        return name
    parts = [f"{k}:{v}" for k, v in sorted(tags.items())]
    return f"{name}|" + ",".join(parts)