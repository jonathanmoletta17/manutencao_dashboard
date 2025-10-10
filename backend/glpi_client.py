"""
Cliente GLPI
Funções para autenticação, configuração de entidade e busca paginada,
com cache simples de sessão para evitar reautenticação por requisição.
Lança exceções específicas para que a camada de API mapeie respostas HTTP neutras.

Sessão e Cache
---------------
- Usa cache por processo com TTL para reuso de `Session-Token`.
- Protegido por lock para evitar condições de corrida em ambientes multi-thread.
- TTL padrão vem de `SESSION_TTL_SEC` (env), mas pode ser injetado via argumento.
- Mudança de entidade ativa pode ser desabilitada via env `GLPI_CHANGE_ENTITY`.
"""
import os
import time
import threading
from typing import Any, Dict, List, Optional

import requests
import logging

from .logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError
from .utils.glpi_params import build_search_params, mask_sensitive_keys
from .utils.convert import to_int_zero

logger = logging.getLogger(__name__)

# Cache leve de sessão (reuso de Session-Token por TTL curto)
_SESSION_HEADERS: Optional[Dict[str, str]] = None
_SESSION_TS: float = 0.0
_SESSION_LOCK = threading.Lock()
SESSION_TTL_SEC = int(os.environ.get("SESSION_TTL_SEC", "300"))


def authenticate(
    api_url: str,
    app_token: str,
    user_token: str,
    session_ttl_sec: Optional[int] = None,
    change_entity: Optional[bool] = None,
) -> Dict[str, str]:
    """
    Autentica no GLPI e configura entidade ativa.
    
    Args:
        api_url: URL da API GLPI (já incluindo /apirest.php)
        app_token: Token da aplicação
        user_token: Token do usuário
        
    Returns:
        Headers com session-token para uso nas próximas requisições
    """
    # Cache de sessão: reutiliza se ainda válido (com proteção de lock)
    global _SESSION_HEADERS, _SESSION_TS
    ttl = SESSION_TTL_SEC if session_ttl_sec is None else int(session_ttl_sec)
    with _SESSION_LOCK:
        if _SESSION_HEADERS and (time.time() - _SESSION_TS) < ttl:
            return _SESSION_HEADERS

    # Endpoint de autenticação
    auth_url = f"{api_url}/initSession"
    
    # Headers para autenticação
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'user_token {user_token}',
        'App-Token': app_token
    }
    
    try:
        response = requests.get(auth_url, headers=headers, timeout=(3, 6))
        response.raise_for_status()
        
        auth_data = response.json()
        session_token = auth_data.get('session_token')
        
        if not session_token:
            raise GLPIAuthError("Token de sessão não encontrado", status_code=401)
        
        # Headers para próximas requisições
        session_headers = {
            'Content-Type': 'application/json',
            'Session-Token': session_token,
            'App-Token': app_token
        }
        
        # Determinar se deve trocar entidade ativa
        # change_entity=None => usa env GLPI_CHANGE_ENTITY (default habilitado)
        change_by_env = os.environ.get("GLPI_CHANGE_ENTITY", "1").strip().lower()
        change_enabled = (change_entity if change_entity is not None else (change_by_env not in ("0", "false")))

        if change_enabled:
            change_entity_url = f"{api_url}/changeActiveEntities"
            entity_data = {
                'entities_id': 1,
                'is_recursive': True
            }
            entity_response = requests.post(change_entity_url, headers=session_headers, json=entity_data, timeout=(3, 6))
            entity_response.raise_for_status()

        # Atualiza cache de sessão com lock
        with _SESSION_LOCK:
            _SESSION_HEADERS = session_headers
            _SESSION_TS = time.time()

        return session_headers
        
    except requests.exceptions.Timeout:
        # Timeout pode ocorrer tanto em initSession quanto em changeActiveEntities
        raise GLPINetworkError("Timeout na autenticação/configuração de entidade", timeout=True)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        if status in (401, 403):
            raise GLPIAuthError("Falha de autenticação GLPI", status_code=status)
        # Demais erros HTTP na autenticação ou troca de entidade
        raise GLPISearchError(f"Erro HTTP na autenticação/configuração (status={status})", status_code=status)
    except requests.exceptions.RequestException:
        # Falhas de rede genéricas
        raise GLPINetworkError("Falha de rede na autenticação/configuração de entidade")

def search_paginated(
    headers: Dict[str, str], 
    api_url: str, 
    itemtype: str, 
    criteria: Optional[List[Dict]] = None,
    forcedisplay: Optional[List[str]] = None,
    uid_cols: bool = True,
    range_step: int = 1000,
    extra_params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Busca paginada com suporte a grandes volumes de dados.
    
    Args:
        headers: Headers com session-token
        api_url: URL base da API GLPI
        itemtype: Tipo do item para busca
        criteria: Critérios de filtro
        forcedisplay: Campos a serem exibidos
        uid_cols: Se deve usar uid_cols=1
        range_step: Tamanho da página
        
    Returns:
        Lista completa de registros encontrados
    """
    search_url = f"{api_url}/search/{itemtype}"
    all_results: List[Dict[str, Any]] = []
    start = 0

    # Parâmetros base via helper reutilizável
    params = build_search_params(
        uid_cols=uid_cols,
        forcedisplay=forcedisplay,
        criteria=criteria,
        extra_params=extra_params,
    )
    
    try:
        while True:
            # Configurar range para paginação
            current_params = params.copy()
            current_params['range'] = f"{start}-{start + range_step - 1}"

            # Log detalhado sem expor valores sensíveis
            logger.debug(
                "GLPI search GET %s itemtype=%s params=%s",
                search_url,
                itemtype,
                mask_sensitive_keys(current_params),
            )

            response = requests.get(search_url, headers=headers, params=current_params, timeout=(3, 6))
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar se há dados
            rows = data.get('data') if isinstance(data, dict) else None
            if not rows:
                break

            all_results.extend(rows)

            # Verificar se chegou ao fim
            totalcount = int(data.get('totalcount', 0) or 0)
            if (totalcount > 0 and len(all_results) >= totalcount) or (len(rows) < range_step):
                break

            start += range_step
            
        return all_results
        
    except requests.exceptions.Timeout:
        raise GLPINetworkError(f"Timeout na busca paginada de {itemtype}", timeout=True)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        body = ''
        try:
            body = getattr(e.response, 'text', '')
        except Exception:
            body = ''
        # Log detalhado do erro HTTP retornado pelo GLPI
        logger.error("GLPI HTTP error itemtype=%s status=%s body=%s", itemtype, status, body)
        if status in (401, 403):
            raise GLPIAuthError("Falha de autenticação GLPI", status_code=status)
        raise GLPISearchError(f"Erro HTTP na busca paginada de {itemtype} (status={status})", status_code=status)
    except requests.exceptions.RequestException:
        raise GLPINetworkError(f"Falha de rede na busca paginada de {itemtype}")


def search_totalcount(
    headers: Dict[str, str],
    api_url: str,
    itemtype: str,
    criteria: Optional[List[Dict]] = None,
    uid_cols: bool = True,
    extra_params: Optional[Dict[str, Any]] = None,
    timeout: tuple[int, int] = (2, 4),
) -> int:
    """
    Busca rápida retornando apenas o totalcount para um itemtype.

    Executa uma chamada única com `range=0-0` para que o GLPI
    devolva somente o total de registros que atendem aos critérios.

    Args:
        headers: Headers com session-token
        api_url: URL base da API GLPI
        itemtype: Tipo do item para busca (ex.: 'Ticket')
        criteria: Critérios de filtro
        uid_cols: Se deve usar uid_cols=1
        extra_params: Parâmetros adicionais de busca (ex.: display_type, is_recursive)
        timeout: Timeout (connect, read)

    Returns:
        Total de registros que atendem à busca
    """
    search_url = f"{api_url}/search/{itemtype}"
    params = build_search_params(
        uid_cols=uid_cols,
        forcedisplay=None,
        criteria=criteria,
        extra_params=extra_params,
    )
    params['range'] = '0-0'

    try:
        logger.debug(
            "GLPI search totalcount GET %s itemtype=%s params=%s",
            search_url,
            itemtype,
            mask_sensitive_keys(params),
        )
        response = requests.get(search_url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return int(data.get('totalcount', 0) or 0)
    except requests.exceptions.Timeout:
        raise GLPINetworkError(f"Timeout na busca de totalcount de {itemtype}", timeout=True)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        body = ''
        try:
            body = getattr(e.response, 'text', '')
        except Exception:
            body = ''
        logger.error("GLPI HTTP error (totalcount) itemtype=%s status=%s body=%s", itemtype, status, body)
        if status in (401, 403):
            raise GLPIAuthError("Falha de autenticação GLPI", status_code=status)
        raise GLPISearchError(f"Erro HTTP na busca de totalcount de {itemtype} (status={status})", status_code=status)
    except requests.exceptions.RequestException:
        raise GLPINetworkError(f"Falha de rede na busca de totalcount de {itemtype}")

def get_user_names_in_batch_with_fallback(headers: Dict[str, str], api_url: str, requester_ids: List[int]) -> Dict[int, str]:
    """
    Resolve nomes de usuários (requisitantes) a partir de seus IDs.
    Implementação segura: resolve individualmente via GET /User/{id} para cada ID único.
    Para listas pequenas (top 10), é suficiente e robusto.

    Args:
        headers: Headers com Session-Token/App-Token já autenticados.
        api_url: URL base da API GLPI (inclui /apirest.php).
        requester_ids: Lista de IDs de usuários para resolver nomes.

    Returns:
        Dict[int, str]: Mapa de user_id -> "firstname realname" (ou rótulo seguro se não encontrado).
    """
    import requests as _requests

    names_map: Dict[int, str] = {}
    # Normalização robusta de IDs: converte qualquer valor para int, devolve 0 em falha
    # Filtra IDs <= 0 e remove duplicados com ordenação
    normalized_ids = [to_int_zero(rid) for rid in requester_ids]
    unique_ids = list(sorted({rid for rid in normalized_ids if rid > 0}))

    for user_id in unique_ids:
        try:
            user_url = f"{api_url}/User/{user_id}"
            response = _requests.get(user_url, headers=headers, timeout=(3, 6))
            response.raise_for_status()
            user_data = response.json()

            # A API pode retornar uma lista mesmo para um único ID
            if isinstance(user_data, list) and user_data:
                user_data = user_data[0]

            first_name = user_data.get('firstname', '')
            last_name = user_data.get('realname', '')
            full_name = f"{first_name} {last_name}".strip()
            names_map[user_id] = full_name if full_name else f"Usuário ID {user_id}"

        except _requests.exceptions.Timeout:
            names_map[user_id] = f"Usuário ID {user_id} (Timeout)"
        except _requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            if status == 403:
                names_map[user_id] = f"Usuário ID {user_id} (Sem Permissão)"
            elif status == 404:
                names_map[user_id] = f"Usuário ID {user_id} (Não Encontrado)"
            else:
                names_map[user_id] = f"Usuário ID {user_id} (Erro HTTP {status})"
        except _requests.exceptions.RequestException:
            names_map[user_id] = f"Usuário ID {user_id} (Erro de Rede)"
        except (IndexError, KeyError, TypeError, ValueError):
            names_map[user_id] = f"Usuário ID {user_id} (Dados Incompletos)"

    return names_map