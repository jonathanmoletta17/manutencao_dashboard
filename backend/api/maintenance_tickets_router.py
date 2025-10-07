"""
Rotas de tickets para Dashboard de Manutenção (apenas tickets)
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from .. import glpi_client
from ..logic.maintenance_tickets_logic import get_maintenance_new_tickets
from ..schemas_maintenance import MaintenanceNewTicketItem
from ..logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError
from ..utils.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manutencao", tags=["Manutenção"])


@router.get("/tickets-novos", response_model=list[MaintenanceNewTicketItem])
def get_new_tickets(limit: Optional[int] = 10):
    """
    Lista os tickets novos mais recentes de manutenção.
    """
    cache_key = f"maintenance_new_tickets_{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = os.getenv("API_URL") or os.getenv("GLPI_BASE_URL")
    APP_TOKEN = os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Variáveis de ambiente da API não configuradas."
        )

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        tickets = get_maintenance_new_tickets(
            api_url=API_URL,
            session_headers=headers,
            limit=limit
        )

        result = [MaintenanceNewTicketItem(**ticket) for ticket in tickets]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/tickets-novos count=%d",
            len(result)
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
        logger.exception("Erro inesperado ao buscar tickets novos: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar tickets.")