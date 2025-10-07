"""
Rotas de ranking para Dashboard de Manutenção (entidades, categorias, tops)
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from .. import glpi_client
from ..logic.maintenance_ranking_logic import (
    generate_entity_ranking,
    generate_category_ranking,
    generate_entity_top_all,
    generate_category_top_all,
    generate_technician_ranking,
)
from ..schemas_maintenance import (
    EntityRankingItem,
    CategoryRankingItem,
    TechnicianRankingItem,
)
from ..logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError
from ..utils.cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/manutencao", tags=["Manutenção"])


@router.get("/ranking-entidades", response_model=list[EntityRankingItem])
def get_entity_ranking(inicio: str, fim: str, top: Optional[int] = 10):
    cache_key = f"maintenance_entity_rank_{inicio}_{fim}_{top}"
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
        ranking = generate_entity_ranking(
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
    cache_key = f"maintenance_category_rank_{inicio}_{fim}_{top}"
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
        ranking = generate_category_ranking(
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


@router.get("/top-atribuicao-entidades", response_model=list[EntityRankingItem])
def get_top_atribuicao_entidades(top: Optional[int] = 10):
    cache_key = f"maintenance_top_entities_{top}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = os.getenv("API_URL")
    APP_TOKEN = os.getenv("APP_TOKEN") or os.getenv("GLPI_APP_TOKEN")
    USER_TOKEN = os.getenv("USER_TOKEN") or os.getenv("GLPI_USER_TOKEN")

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API não configuradas.")

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        ranking = generate_entity_top_all(
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
    cache_key = f"maintenance_top_categories_{top}"
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
        ranking = generate_category_top_all(
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


@router.get("/ranking-tecnicos", response_model=list[TechnicianRankingItem])
def get_technician_ranking(inicio: str, fim: str, top: Optional[int] = 10):
    cache_key = f"maintenance_technician_rank_{inicio}_{fim}_{top}"
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
        ranking = generate_technician_ranking(
            api_url=API_URL,
            session_headers=headers,
            inicio=inicio,
            fim=fim,
            top_n=top or 10,
        )

        result = [TechnicianRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/ranking-tecnicos inicio=%s fim=%s count=%d",
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
        logger.exception("Erro inesperado ao buscar ranking de técnicos: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")