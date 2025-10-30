"""
Rotas de ranking para Dashboard de Manutenção (entidades, categorias, tops)
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
import time
from .. import glpi_client
from ..config import get_api_url, get_app_token, get_user_token, tech_rank_top_limit
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
def get_entity_ranking(inicio: str, fim: str, top: Optional[int] = None):
    top_key = 'all' if (top is None or top == 0) else str(top)
    cache_key = f"maintenance_entity_rank_{inicio}_{fim}_{top_key}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = get_api_url()
    APP_TOKEN = get_app_token()
    USER_TOKEN = get_user_token()

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API não configuradas.")

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        t0 = time.perf_counter()
        ranking = generate_entity_ranking(
            api_url=API_URL,
            session_headers=headers,
            inicio=inicio,
            fim=fim,
            top_n=top if (top not in (None, 0)) else None
        )
        t1 = time.perf_counter()
        try:
            from ..utils import metrics
            metrics.record_timing('endpoint.latency_ms', (t1 - t0) * 1000, tags={'endpoint': 'ranking-entidades'})
            if cached:
                metrics.increment('cache.hit', tags={'endpoint': 'ranking-entidades'})
            else:
                metrics.increment('cache.miss', tags={'endpoint': 'ranking-entidades'})
        except Exception:
            pass

        result = [EntityRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/ranking-entidades inicio=%s fim=%s count=%d duration_ms=%.1f",
            inicio, fim, len(result), (t1 - t0) * 1000
        )
        return result

    except GLPIAuthError as e:
        logger.error("Erro de autenticação GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-entidades devido a falha de autenticação")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPINetworkError as e:
        logger.error("Erro de rede GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-entidades devido a erro de rede")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPISearchError as e:
        logger.error("Erro de busca GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-entidades devido a erro de busca")
            return stale
        raise HTTPException(status_code=502, detail="Erro ao buscar dados no GLPI.")
    except Exception as e:
        logger.exception("Erro inesperado ao buscar ranking de entidades: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")


@router.get("/ranking-categorias", response_model=list[CategoryRankingItem])
def get_category_ranking(inicio: str, fim: str, top: Optional[int] = None):
    top_key = 'all' if (top is None or top == 0) else str(top)
    cache_key = f"maintenance_category_rank_{inicio}_{fim}_{top_key}"
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
        t0 = time.perf_counter()
        ranking = generate_category_ranking(
            api_url=API_URL,
            session_headers=headers,
            inicio=inicio,
            fim=fim,
            top_n=top if (top not in (None, 0)) else None
        )
        t1 = time.perf_counter()
        try:
            from ..utils import metrics
            metrics.record_timing('endpoint.latency_ms', (t1 - t0) * 1000, tags={'endpoint': 'ranking-categorias'})
            if cached:
                metrics.increment('cache.hit', tags={'endpoint': 'ranking-categorias'})
            else:
                metrics.increment('cache.miss', tags={'endpoint': 'ranking-categorias'})
        except Exception:
            pass

        result = [CategoryRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/ranking-categorias inicio=%s fim=%s count=%d duration_ms=%.1f",
            inicio, fim, len(result), (t1 - t0) * 1000
        )
        return result

    except GLPIAuthError as e:
        logger.error("Erro de autenticação GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-categorias devido a falha de autenticação")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPINetworkError as e:
        logger.error("Erro de rede GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-categorias devido a erro de rede")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPISearchError as e:
        logger.error("Erro de busca GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-categorias devido a erro de busca")
            return stale
        raise HTTPException(status_code=502, detail="Erro ao buscar dados no GLPI.")
    except Exception as e:
        logger.exception("Erro inesperado ao buscar ranking de categorias: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")


@router.get("/top-atribuicao-entidades", response_model=list[EntityRankingItem])
def get_top_atribuicao_entidades(top: Optional[int] = None):
    top_key = 'all' if (top is None or top == 0) else str(top)
    cache_key = f"maintenance_top_entities_{top_key}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = get_api_url()
    APP_TOKEN = get_app_token()
    USER_TOKEN = get_user_token()

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API não configuradas.")

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        t0 = time.perf_counter()
        ranking = generate_entity_top_all(
            api_url=API_URL,
            session_headers=headers,
            top_n=top if (top not in (None, 0)) else None,
        )
        t1 = time.perf_counter()
        try:
            from ..utils import metrics
            metrics.record_timing('endpoint.latency_ms', (t1 - t0) * 1000, tags={'endpoint': 'top-atribuicao-entidades'})
            if cached:
                metrics.increment('cache.hit', tags={'endpoint': 'top-atribuicao-entidades'})
            else:
                metrics.increment('cache.miss', tags={'endpoint': 'top-atribuicao-entidades'})
        except Exception:
            pass

        result = [EntityRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/top-atribuicao-entidades count=%d duration_ms=%.1f",
            len(result), (t1 - t0) * 1000
        )
        return result

    except GLPIAuthError as e:
        logger.error("Erro de autenticação GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para top-atribuicao-entidades devido a falha de autenticação")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPINetworkError as e:
        logger.error("Erro de rede GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para top-atribuicao-entidades devido a erro de rede")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPISearchError as e:
        logger.error("Erro de busca GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para top-atribuicao-entidades devido a erro de busca")
            return stale
        raise HTTPException(status_code=502, detail="Erro ao buscar dados no GLPI.")
    except Exception as e:
        logger.exception("Erro inesperado ao buscar top atribuição por entidades: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")


@router.get("/top-atribuicao-categorias", response_model=list[CategoryRankingItem])
def get_top_atribuicao_categorias(top: Optional[int] = None):
    top_key = 'all' if (top is None or top == 0) else str(top)
    cache_key = f"maintenance_top_categories_{top_key}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    API_URL = get_api_url()
    APP_TOKEN = get_app_token()
    USER_TOKEN = get_user_token()

    if not all([API_URL, APP_TOKEN, USER_TOKEN]):
        raise HTTPException(status_code=500, detail="Variáveis de ambiente da API não configuradas.")

    try:
        headers = glpi_client.authenticate(API_URL, APP_TOKEN, USER_TOKEN)
        t0 = time.perf_counter()
        ranking = generate_category_top_all(
            api_url=API_URL,
            session_headers=headers,
            top_n=top if (top not in (None, 0)) else None,
        )
        t1 = time.perf_counter()
        try:
            from ..utils import metrics
            metrics.record_timing('endpoint.latency_ms', (t1 - t0) * 1000, tags={'endpoint': 'top-atribuicao-categorias'})
            if cached:
                metrics.increment('cache.hit', tags={'endpoint': 'top-atribuicao-categorias'})
            else:
                metrics.increment('cache.miss', tags={'endpoint': 'top-atribuicao-categorias'})
        except Exception:
            pass

        result = [CategoryRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/top-atribuicao-categorias count=%d duration_ms=%.1f",
            len(result), (t1 - t0) * 1000
        )
        return result

    except GLPIAuthError as e:
        logger.error("Erro de autenticação GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para top-atribuicao-categorias devido a falha de autenticação")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPINetworkError as e:
        logger.error("Erro de rede GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para top-atribuicao-categorias devido a erro de rede")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPISearchError as e:
        logger.error("Erro de busca GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para top-atribuicao-categorias devido a erro de busca")
            return stale
        raise HTTPException(status_code=502, detail="Erro ao buscar dados no GLPI.")
    except Exception as e:
        logger.exception("Erro inesperado ao buscar top atribuição por categorias: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")


@router.get("/ranking-tecnicos", response_model=list[TechnicianRankingItem])
def get_technician_ranking(inicio: str, fim: str, top: Optional[int] = None, incluirNaoAtribuido: Optional[bool] = False):
    # Limite de TOP vindo do ambiente (padrão 20)
    top_limit = tech_rank_top_limit()

    # Aplicar clamp do top ao limite e defaultar para limite quando ausente
    applied_top = top_limit if (top is None or top == 0) else min(int(top), top_limit)
    top_key = str(applied_top)
    include_key = 'inclui' if incluirNaoAtribuido else 'nao_inclui'
    cache_key = f"maintenance_technician_rank_{inicio}_{fim}_{top_key}_{include_key}"
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
        t0 = time.perf_counter()
        ranking = generate_technician_ranking(
            api_url=API_URL,
            session_headers=headers,
            inicio=inicio,
            fim=fim,
            top_n=applied_top,
            include_unassigned=bool(incluirNaoAtribuido),
        )
        t1 = time.perf_counter()
        try:
            from ..utils import metrics
            metrics.record_timing('endpoint.latency_ms', (t1 - t0) * 1000, tags={'endpoint': 'ranking-tecnicos'})
            if cached:
                metrics.increment('cache.hit', tags={'endpoint': 'ranking-tecnicos'})
            else:
                metrics.increment('cache.miss', tags={'endpoint': 'ranking-tecnicos'})
        except Exception:
            pass

        result = [TechnicianRankingItem(**item) for item in ranking]
        cache.set(cache_key, result)
        logger.info(
            "endpoint=/manutencao/ranking-tecnicos inicio=%s fim=%s count=%d top_applied=%d",
            inicio, fim, len(result), applied_top
        )
        return result

    except GLPIAuthError as e:
        logger.error("Erro de autenticação GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-tecnicos devido a falha de autenticação")
            return stale
        raise HTTPException(status_code=502, detail="Falha de comunicação com serviço GLPI.")
    except GLPINetworkError as e:
        logger.error("Erro de rede GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-tecnicos devido a erro de rede")
            return stale
        status = 504 if getattr(e, 'timeout', False) else 502
        raise HTTPException(status_code=status, detail="Falha de comunicação com serviço GLPI.")
    except GLPISearchError as e:
        logger.error("Erro de busca GLPI: %s", str(e))
        stale = cache.get_stale(cache_key)
        if stale is not None:
            logger.warning("Retornando valor stale para ranking-tecnicos devido a erro de busca")
            return stale
        raise HTTPException(status_code=502, detail="Erro ao buscar dados no GLPI.")
    except Exception as e:
        logger.exception("Erro inesperado ao buscar ranking de técnicos: %s", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao processar ranking.")