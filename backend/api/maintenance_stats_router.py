"""
Rotas de métricas para Dashboard de Manutenção (stats gerais e totais por status)
"""
import logging
import os

from fastapi import APIRouter, HTTPException
from .. import glpi_client
from ..logic.maintenance_stats_logic import (
    generate_maintenance_stats,
)
from ..schemas_maintenance import (
    MaintenanceGeneralStats,
)
from ..logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError
from ..utils.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manutencao", tags=["Manutenção"])



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
            "endpoint=/manutencao/stats-gerais inicio=%s fim=%s novos=%d em_atendimento=%d pendentes=%d planejados=%d resolvidos=%d",
            inicio, fim, stats['novos'], stats.get('em_atendimento', 0), stats['pendentes'], stats['planejados'], stats['resolvidos']
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
