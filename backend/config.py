"""
Configuração centralizada do backend.

Responsável por:
- Leitura de variáveis de ambiente com defaults.
- Conversão e normalização de timeouts para `requests`.
- Limites e clamps seguros para workers.
"""
from __future__ import annotations

import os
from typing import Tuple, Optional


def get_api_url() -> Optional[str]:
    return os.getenv("API_URL") or os.getenv("GLPI_BASE_URL")


def get_app_token() -> Optional[str]:
    return os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")


def get_user_token() -> Optional[str]:
    return os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")


def session_ttl_sec() -> int:
    try:
        return int(os.getenv("SESSION_TTL_SEC", "300"))
    except Exception:
        return 300


def should_change_entity() -> bool:
    raw = os.getenv("GLPI_CHANGE_ENTITY", "1").strip().lower()
    return raw not in ("0", "false")


def timeouts_sec() -> Tuple[float, float]:
    """
    Retorna (connect_timeout_sec, read_timeout_sec) para usar em `requests`.
    Defaults: 1000ms conexão, 2500ms leitura.
    """
    def _ms_to_sec(env_name: str, default_ms: int) -> float:
        try:
            return max(0.001, int(os.getenv(env_name, str(default_ms))) / 1000.0)
        except Exception:
            return default_ms / 1000.0

    return (
        _ms_to_sec("GLPI_TIMEOUT_CONN_MS", 1000),
        _ms_to_sec("GLPI_TIMEOUT_READ_MS", 2500),
    )


def ranking_timeouts_sec() -> Tuple[float, float]:
    """
    Retorna timeouts específicos para operações de ranking (mais generosos).
    Defaults: 3000ms conexão, 15000ms leitura.
    """
    def _ms_to_sec(env_name: str, default_ms: int) -> float:
        try:
            return max(0.001, int(os.getenv(env_name, str(default_ms))) / 1000.0)
        except Exception:
            return default_ms / 1000.0

    return (
        _ms_to_sec("GLPI_TIMEOUT_RANKING_CONN_MS", 3000),
        _ms_to_sec("GLPI_TIMEOUT_RANKING_READ_MS", 15000),
    )


def range_step_tickets() -> int:
    try:
        v = int(os.getenv("GLPI_RANGE_STEP_TICKETS", "1000"))
        return max(1, v)
    except Exception:
        return 1000


def tech_rank_top_limit() -> int:
    try:
        v = int(os.getenv("TECH_RANK_TOP_LIMIT", "20"))
        return max(1, v)
    except Exception:
        return 20


def name_workers() -> int:
    try:
        v = int(os.getenv("GLPI_NAME_WORKERS", "8"))
        # Clamp seguro entre 1 e 16
        return min(max(1, v), 16)
    except Exception:
        return 8