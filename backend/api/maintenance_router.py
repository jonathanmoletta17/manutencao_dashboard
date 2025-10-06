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
    MaintenanceStatusTotals,
    EntityRankingItem,
    CategoryRankingItem,
    MaintenanceNewTicketItem
)
from ..logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError
from ..utils.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manutencao", tags=["Manutenção"])


@router.get("/status-totais", response_model=MaintenanceStatusTotals)
def get_status_totais():
    """
    Totais gerais por status (1, 2+4, 3, 5, 6, 5+6),
    alinhados com o script PowerShell e sem filtro de datas.
    """
    cache_key = "maintenance_status_totals"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = os.getenv("API_URL") or os.getenv("GLPI_BASE_URL")
    # Aceita nomes de variáveis conforme .env e scripts PowerShell
    APP_TOKEN = os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Variáveis de ambiente da API não configuradas."
        )

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        totals = maintenance_logic.generate_status_totals(
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
    APP_TOKEN = os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")
    
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


@router.get("/top-atribuicao-entidades", response_model=list[EntityRankingItem])
def get_top_atribuicao_entidades(top: Optional[int] = 10):
    """
    Top N de atribuição por entidades (sem filtro de datas),
    espelhando a lógica do script PowerShell top_entities.ps1.
    """
    cache_key = f"maintenance_top_entities_{top}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = os.getenv("API_URL")
    APP_TOKEN = os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Variáveis de ambiente da API não configuradas."
        )

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        ranking = maintenance_logic.generate_entity_top_all(
            api_url=API_URL,
            session_headers=headers,
            top_n=top or 10,
        )

        result = [EntityRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/top-atribuicao-entidades count=%d",
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
        logger.exception("Erro inesperado ao buscar top atribuição por entidades: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")


@router.get("/top-atribuicao-categorias", response_model=list[CategoryRankingItem])
def get_top_atribuicao_categorias(top: Optional[int] = 10):
    """
    Top N de atribuição por categorias (sem filtro de datas),
    espelhando a lógica do script PowerShell top_categories.ps1.
    """
    cache_key = f"maintenance_top_categories_{top}"
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
        ranking = maintenance_logic.generate_category_top_all(
            api_url=API_URL,
            session_headers=headers,
            top_n=top or 10,
        )

        result = [CategoryRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/top-atribuicao-categorias count=%d",
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
        logger.exception("Erro inesperado ao buscar top atribuição por categorias: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")
