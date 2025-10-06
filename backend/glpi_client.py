"""
Cliente GLPI
Funções para autenticação, configuração de entidade e busca paginada,
com cache simples de sessão para evitar reautenticação por requisição.
Lança exceções específicas para que a camada de API mapeie respostas HTTP neutras.
"""
import os
import time
from typing import Any, Dict, List, Optional

import requests

from .logic.errors import GLPIAuthError, GLPINetworkError, GLPISearchError

# Cache leve de sessão (reuso de Session-Token por TTL curto)
_SESSION_HEADERS: Optional[Dict[str, str]] = None
_SESSION_TS: float = 0.0
SESSION_TTL_SEC = int(os.environ.get("SESSION_TTL_SEC", "300"))


def authenticate(api_url: str, app_token: str, user_token: str) -> Dict[str, str]:
    """
    Autentica no GLPI e configura entidade ativa.
    
    Args:
        api_url: URL da API GLPI (já incluindo /apirest.php)
        app_token: Token da aplicação
        user_token: Token do usuário
        
    Returns:
        Headers com session-token para uso nas próximas requisições
    """
    # Cache de sessão: reutiliza se ainda válido
    global _SESSION_HEADERS, _SESSION_TS
    if _SESSION_HEADERS and (time.time() - _SESSION_TS) < SESSION_TTL_SEC:
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
        
        # Configurar entidade ativa (conforme script exemplo: EntitiesId = 1, recursivo)
        change_entity_url = f"{api_url}/changeActiveEntities"
        entity_data = {
            'entities_id': 1,
            'is_recursive': True
        }
        
        entity_response = requests.post(change_entity_url, headers=session_headers, json=entity_data, timeout=(3, 6))
        entity_response.raise_for_status()
        # Atualiza cache de sessão
        _SESSION_HEADERS = session_headers
        _SESSION_TS = time.time()

        return session_headers
        
    except requests.exceptions.Timeout:
        raise GLPINetworkError("Timeout na autenticação/configuração de entidade", timeout=True)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        if status in (401, 403):
            raise GLPIAuthError("Falha de autenticação GLPI", status_code=status)
        raise GLPISearchError(f"Erro HTTP na autenticação/configuração (status={status})", status_code=status)
    except requests.exceptions.RequestException:
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
    all_results = []
    start = 0
    
    # Parâmetros base
    params = {}
    if uid_cols:
        params['uid_cols'] = '1'
    if forcedisplay:
        for i, f in enumerate(forcedisplay):
            params[f'forcedisplay[{i}]'] = f
    if criteria:
        for i, c in enumerate(criteria):
            for k, v in c.items():
                params[f'criteria[{i}][{k}]'] = v
    if extra_params:
        for k, v in extra_params.items():
            params[str(k)] = v
    
    try:
        while True:
            # Configurar range para paginação
            current_params = params.copy()
            current_params['range'] = f"{start}-{start + range_step - 1}"
            
            response = requests.get(search_url, headers=headers, params=current_params, timeout=(3, 6))
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar se há dados
            if not data or 'data' not in data or not data['data']:
                break
                
            all_results.extend(data['data'])
            
            # Verificar se chegou ao fim
            totalcount = data.get('totalcount', 0)
            if len(all_results) >= totalcount or len(data['data']) < range_step:
                break
                
            start += range_step
            
        return all_results
        
    except requests.exceptions.Timeout:
        raise GLPINetworkError(f"Timeout na busca paginada de {itemtype}", timeout=True)
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        if status in (401, 403):
            raise GLPIAuthError("Falha de autenticação GLPI", status_code=status)
        raise GLPISearchError(f"Erro HTTP na busca paginada de {itemtype} (status={status})", status_code=status)
    except requests.exceptions.RequestException:
        raise GLPINetworkError(f"Falha de rede na busca paginada de {itemtype}")


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
    unique_ids = list(sorted(set(int(rid) for rid in requester_ids if isinstance(rid, (int, str)))))

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

        except _requests.exceptions.RequestException:
            names_map[user_id] = f"Usuário ID {user_id} (Não Encontrado)"
        except (IndexError, KeyError, TypeError, ValueError):
            names_map[user_id] = f"Usuário ID {user_id} (Dados Incompletos)"

    return names_map