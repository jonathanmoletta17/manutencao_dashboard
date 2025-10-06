"""
Rotas da API para Dashboard de Manutenção
Endpoints específicos para métricas de manutenção
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from .. import glpi_client
from ..logic import maintenance_logic
from ..schemas_maintenance import (
    MaintenanceGeneralStats,
    EntityRankingItem,
    CategoryRankingItem,
    MaintenanceNewTicketItem
)
from ..logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError
from ..utils.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manutencao", tags=["Manutenção"])


@router.get("/stats-gerais", response_model=MaintenanceGeneralStats)
def get_maintenance_general_stats(inicio: str, fim: str):
    """
    Estatísticas gerais de manutenção por status.
    
    Args:
        inicio: Data início no formato YYYY-MM-DD
        fim: Data fim no formato YYYY-MM-DD
        
    Returns:
        Contagens de novos, pendentes, planejados, resolvidos
    """
    # Verificar cache
    cache_key = f"maintenance_stats_{inicio}_{fim}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    API_URL = os.getenv("API_URL")
    APP_TOKEN = os.getenv("APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN")
    
    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Variáveis de ambiente da API não configuradas."
        )
    
    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        stats = maintenance_logic.generate_maintenance_stats(
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


@router.get("/ranking-entidades", response_model=list[EntityRankingItem])
def get_entity_ranking(inicio: str, fim: str, top: Optional[int] = 10):
    """
    Ranking de atribuição por entidades.
    
    Args:
        inicio: Data início no formato YYYY-MM-DD
        fim: Data fim no formato YYYY-MM-DD
        top: Número de entidades no ranking (padrão 10)
        
    Returns:
        Lista de entidades ordenadas por número de tickets
    """
    # Verificar cache
    cache_key = f"maintenance_entity_rank_{inicio}_{fim}_{top}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    API_URL = os.getenv("API_URL")
    APP_TOKEN = os.getenv("APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN")
    
    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Variáveis de ambiente da API não configuradas."
        )
    
    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        ranking = maintenance_logic.generate_entity_ranking(
            api_url=API_URL,
            session_headers=headers,
            inicio=inicio,
            fim=fim,
            top_n=top
        )
        
        result = [EntityRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/ranking-entidades inicio=%s fim=%s count=%d",
            inicio, fim, len(result)
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
        logger.exception("Erro inesperado ao buscar ranking de entidades: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")


@router.get("/ranking-categorias", response_model=list[CategoryRankingItem])
def get_category_ranking(inicio: str, fim: str, top: Optional[int] = 10):
    """
    Ranking de atribuição por categorias.
    
    Args:
        inicio: Data início no formato YYYY-MM-DD
        fim: Data fim no formato YYYY-MM-DD
        top: Número de categorias no ranking (padrão 10)
        
    Returns:
        Lista de categorias ordenadas por número de tickets
    """
    # Verificar cache
    cache_key = f"maintenance_category_rank_{inicio}_{fim}_{top}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    API_URL = os.getenv("API_URL")
    APP_TOKEN = os.getenv("APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN")
    
    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Variáveis de ambiente da API não configuradas."
        )
    
    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        ranking = maintenance_logic.generate_category_ranking(
            api_url=API_URL,
            session_headers=headers,
            inicio=inicio,
            fim=fim,
            top_n=top
        )
        
        result = [CategoryRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/ranking-categorias inicio=%s fim=%s count=%d",
            inicio, fim, len(result)
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
        logger.exception("Erro inesperado ao buscar ranking de categorias: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")


@router.get("/tickets-novos", response_model=list[MaintenanceNewTicketItem])
def get_new_tickets(limit: Optional[int] = 10):
    """
    Lista os tickets novos mais recentes de manutenção.
    
    Args:
        limit: Número máximo de tickets (padrão 10)
        
    Returns:
        Lista de tickets novos
    """
    # Verificar cache
    cache_key = f"maintenance_new_tickets_{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    API_URL = os.getenv("API_URL")
    APP_TOKEN = os.getenv("APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN")
    
    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Variáveis de ambiente da API não configuradas."
        )
    
    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        tickets = maintenance_logic.get_maintenance_new_tickets(
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
