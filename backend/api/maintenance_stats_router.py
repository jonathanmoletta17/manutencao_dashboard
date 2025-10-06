"""
Rotas de métricas para Dashboard de Manutenção (stats gerais e totais por status)
"""
import logging
import os

from fastapi import APIRouter, HTTPException
from .. import glpi_client
from ..logic.maintenance_stats_logic import (
    generate_maintenance_stats,
    generate_status_totals,
)
from ..schemas_maintenance import (
    MaintenanceGeneralStats,
    MaintenanceStatusTotals,
)
from ..logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError
from ..utils.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manutencao", tags=["Manutenção"])


@router.get("/status-totais", response_model=MaintenanceStatusTotals)
def get_status_totais():
    cache_key = "maintenance_status_totals"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = os.getenv("API_URL") or os.getenv("GLPI_BASE_URL")
    APP_TOKEN = os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API não configuradas.")

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        totals = generate_status_totals(
            api_url=API_URL,
            session_headers=headers,
        )

        result = MaintenanceStatusTotals(**totals)
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/status-totais novos=%d nao_solucionados=%d planejados=%d solucionados=%d fechados=%d resolvidos=%d",
            totals['novos'], totals['nao_solucionados'], totals['planejados'], totals['solucionados'], totals['fechados'], totals['resolvidos']
        )
        return result

    except GLPIAuthError as e:
        logger.error("Erro de autenticação GLPI: %s", str(e))
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPINetworkError as e:
        logger.error("Erro de rede GLPI: %s", str(e))
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPISearchError as e:
        logger.error("Erro de busca GLPI: %s", str(e))
        raise HTTPException(status_code=502, detail="Erro ao buscar dados no GLPI.")
    except Exception as e:
        logger.exception("Erro inesperado ao buscar totais de status: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar totais de status.")


@router.get("/stats-gerais", response_model=MaintenanceGeneralStats)
def get_maintenance_general_stats(inicio: str, fim: str):
    cache_key = f"maintenance_stats_{inicio}_{fim}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = os.getenv("API_URL") or os.getenv("GLPI_BASE_URL")
    APP_TOKEN = os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API não configuradas.")

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        stats = generate_maintenance_stats(
            api_url=API_URL,
            session_headers=headers,
            inicio=inicio,
            fim=fim
        )

        result = MaintenanceGeneralStats(**stats)
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/stats-gerais inicio=%s fim=%s novos=%d pendentes=%d planejados=%d resolvidos=%d",
            inicio, fim, stats['novos'], stats['pendentes'], stats['planejados'], stats['resolvidos']
        )
        return result

    except GLPIAuthError as e:
        logger.error("Erro de autenticação GLPI: %s", str(e))
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPINetworkError as e:
        logger.error("Erro de rede GLPI: %s", str(e))
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPISearchError as e:
        logger.error("Erro de busca GLPI: %s", str(e))
        raise HTTPException(status_code=502, detail="Erro ao buscar dados no GLPI.")
    except Exception as e:
        logger.exception("Erro inesperado ao buscar estatísticas de manutenção: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar métricas.")