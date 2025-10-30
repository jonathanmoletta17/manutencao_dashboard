"""
Lógica de rankings (entidades e categorias) para o Dashboard de Manutenção
Separada por responsabilidade (ranking)
"""
from typing import Dict, List, Any
import os
import html
from collections import Counter
from .. import glpi_client
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..utils.glpi_params import build_search_params, mask_sensitive_keys
from ..utils.user_names import resolve_user_names_fast
from ..utils.convert import first_numeric_id
from ..utils import metrics
from ..utils.cache import cache
from .glpi_constants import (
    FIELD_CREATED, FIELD_ENTITY, FIELD_CATEGORY, FIELD_TECH, FIELD_STATUS,
    STATUS_NEW,
)
from .criteria_helpers import add_date_range, add_status
from ..config import ranking_timeouts_sec

# Helpers globais de sanitização e validação de rótulos
def sanitize_label(s: Any) -> str:
    if not isinstance(s, str):
        s = str(s) if s is not None else ''
    # Primeiro, desfaz entidades HTML padrão de forma robusta
    t = html.unescape(s)
    replacements = {
        '&amp;#62;': '>',
        '&#62;': '>',
        '&gt;': '>',
        '&amp;gt;': '>',
        '&#39;': "'",
        '&amp;': '&',
        '&lt;': '<',
        '&amp;lt;': '<',
        '&#60;': '<',
        '&quot;': '"',
        '&#34;': '"',
        '&nbsp;': ' ',
    }
    for k, v in replacements.items():
        t = t.replace(k, v)
    return t

def _normalize_label(s: str) -> str:
    return (s or '').strip().lower()

def is_invalid_label(s: str) -> bool:
    ns = _normalize_label(s)
    return ns in ('none', 'null', '')

# Helpers globais para normalização/conversão de técnicos
def normalize_tech_key(raw: Any) -> str:
    """Normaliza users_id_assign para um bucket único '0' quando não há ID numérico válido."""
    if isinstance(raw, list):
        for v in raw:
            vs = str(v).strip()
            if vs.isdigit() and int(vs) > 0:
                return vs
        return '0'
    if isinstance(raw, (int, float)):
        try:
            iv = int(raw)
            return str(iv) if iv > 0 else '0'
        except Exception:
            return '0'
    if isinstance(raw, str):
        s = raw.strip()
        if s.isdigit() and int(s) > 0:
            return s
        return '0'
    return '0'

def safe_int_id(s: Any) -> int:
    try:
        return int(s)
    except Exception:
        return 0


def _resolve_entity_name(headers: Dict[str, str], api_url: str, eid: str) -> str:
    # Se não houver ID, retorna rótulo padrão
    if not eid or eid == '0':
        return '(sem entidade)'
    key = f"entity_name_{eid}"
    cached = cache.get(key)
    if cached:
        return cached
    try:
        # Se 'eid' não for estritamente numérico, não chama API e devolve o próprio rótulo
        if not str(eid).isdigit():
            label = sanitize_label(str(eid))
            label = label if not is_invalid_label(label) else '(sem entidade)'
            cache.set(key, label)
            return label
        url = f"{api_url}/Entity/{eid}"
        resp = requests.get(url, headers=headers, timeout=(1, 2.5))
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            data = data[0]
        comp = data.get('completename')
        nm = data.get('name')
        label = sanitize_label(comp or nm or eid)
        if is_invalid_label(label):
            label = eid
        cache.set(key, label)
        return label
    except Exception:
        # Em falha, devolve o próprio valor sanitizado
        return sanitize_label(str(eid))


def _resolve_category_name(headers: Dict[str, str], api_url: str, cid: str) -> str:
    if not cid or cid == '0':
        return 'sem'
    key = f"category_name_{cid}"
    cached = cache.get(key)
    if cached:
        return cached
    try:
        # Evita chamada à API quando o valor não é numérico (já é um rótulo)
        if not str(cid).isdigit():
            label = sanitize_label(str(cid))
            label = label if not is_invalid_label(label) else 'sem'
            cache.set(key, label)
            return label
        url = f"{api_url}/ITILCategory/{cid}"
        resp = requests.get(url, headers=headers, timeout=(1, 2.5))
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            data = data[0]
        comp = data.get('completename')
        nm = data.get('name')
        label = sanitize_label(comp or nm or cid)
        if is_invalid_label(label):
            label = cid
        cache.set(key, label)
        return label
    except Exception:
        return sanitize_label(str(cid))


def generate_entity_ranking(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str,
    top_n: int | None = None,
    range_step_tickets: int = 1000,
    display_type: str = '2',
    is_recursive: str = '1',
) -> List[Dict[str, Any]]:
    """
    Gera ranking de tickets por entidade dentro de um período.
    Implementação robusta baseada em ID da entidade (display_type=2),
    mapeando posteriormente para o nome completo da entidade.

    Returns:
        Lista de {entity_name, ticket_count} ordenada por count
    """
    # Critérios com link correto entre condições
    criteria = add_date_range([], inicio, fim, field=FIELD_CREATED)

    id_counts: Dict[str, int] = {}
    for row in glpi_client.search_paginated_iter(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[str(FIELD_ENTITY)],
        uid_cols=False,
        range_step=range_step_tickets,
        extra_params={'display_type': display_type, 'is_recursive': is_recursive}
    ):
        # Extrai ID de forma robusta; tenta alternativas quando o campo não vem
        raw_e = row.get(str(FIELD_ENTITY)) or row.get('entities_id')
        num = first_numeric_id(raw_e)
        eid = str(num) if isinstance(num, int) else str(raw_e or '0')
        id_counts[eid] = id_counts.get(eid, 0) + 1

    if not id_counts:
        return []

    sorted_pairs = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)
    limit = top_n if (top_n and top_n > 0) else None
    sorted_items = sorted_pairs if limit is None else sorted_pairs[:limit]
    result: List[Dict[str, Any]] = []
    for eid, count in sorted_items:
        nm = _resolve_entity_name(session_headers, api_url, eid)
        if is_invalid_label(nm):
            continue
        result.append({'entity_name': nm, 'ticket_count': count})

    return result


def generate_entity_top_all(
    api_url: str,
    session_headers: Dict[str, str],
    top_n: int | None = None,
    range_step_tickets: int = 300,
    display_type: str = '2',
    is_recursive: str = '1',
) -> List[Dict[str, Any]]:
    """
    Top N de atribuição por entidades (sem filtro de datas),
    espelhando o script PowerShell top_entities.ps1.
    """
    # Contagem eficiente de entidades via streaming
    id_counts = Counter()
    for row in glpi_client.search_paginated_iter(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[],
        forcedisplay=[str(FIELD_ENTITY)],
        uid_cols=False,
        range_step=range_step_tickets,
        extra_params={'display_type': display_type, 'is_recursive': is_recursive}
    ):
        raw_e = row.get(str(FIELD_ENTITY)) or row.get('entities_id')
        num = first_numeric_id(raw_e)
        eid = str(num) if isinstance(num, int) else str(raw_e or '0')
        id_counts.update([eid])

    if not id_counts:
        return []

    sorted_pairs = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)
    limit = top_n if (top_n and top_n > 0) else None
    sorted_items = sorted_pairs if limit is None else sorted_pairs[:limit]
    result: List[Dict[str, Any]] = []
    for eid, count in sorted_items:
        nm = _resolve_entity_name(session_headers, api_url, eid)
        if is_invalid_label(nm):
            continue
        result.append({'entity_name': nm, 'ticket_count': count})

    return result


def generate_category_ranking(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str,
    top_n: int | None = None,
    range_step_tickets: int = 1000,
    display_type: str = '2',
    is_recursive: str = '1',
) -> List[Dict[str, Any]]:
    """
    Gera ranking de tickets por categoria.
    Returns:
        Lista de {category_name, ticket_count} ordenada por count
    """
    criteria = add_date_range([], inicio, fim, field=FIELD_CREATED)

    # Buscar IDs brutos de categoria no Ticket para contagem confiável
    # Contagem eficiente de categorias via streaming
    id_counts = Counter()
    for row in glpi_client.search_paginated_iter(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[str(FIELD_CATEGORY)],
        uid_cols=False,
        range_step=range_step_tickets,
        extra_params={'display_type': display_type, 'is_recursive': is_recursive}
    ):
        raw_c = row.get(str(FIELD_CATEGORY)) or row.get('itilcategories_id')
        num = first_numeric_id(raw_c)
        cid = str(num) if isinstance(num, int) else str(raw_c or '0')
        id_counts.update([cid])

    if not id_counts:
        return []

    sorted_pairs = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)
    limit = top_n if (top_n and top_n > 0) else None
    sorted_items = sorted_pairs if limit is None else sorted_pairs[:limit]
    result: List[Dict[str, Any]] = []
    for cid, count in sorted_items:
        nm = _resolve_category_name(session_headers, api_url, cid)
        if is_invalid_label(nm):
            continue
        result.append({'category_name': nm, 'ticket_count': count})
    
    return result


def generate_category_top_all(
    api_url: str,
    session_headers: Dict[str, str],
    top_n: int | None = None,
    range_step_tickets: int = 1000,
    display_type: str = '2',
    is_recursive: str = '1',
) -> List[Dict[str, Any]]:
    """
    Top N de atribuição por categorias (sem filtro de datas),
    espelhando o script PowerShell top_categories.ps1.
    """
    # Contagem eficiente de categorias via streaming
    id_counts = Counter()
    for row in glpi_client.search_paginated_iter(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[],
        forcedisplay=[str(FIELD_CATEGORY)],
        uid_cols=False,
        range_step=range_step_tickets,
        extra_params={'display_type': display_type, 'is_recursive': is_recursive}
    ):
        raw_c = row.get(str(FIELD_CATEGORY)) or row.get('itilcategories_id')
        num = first_numeric_id(raw_c)
        cid = str(num) if isinstance(num, int) else str(raw_c or '0')
        id_counts.update([cid])

    if not id_counts:
        return []

    # Resolver nomes sob demanda por ID com cache

    sorted_pairs = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)
    limit = top_n if (top_n and top_n > 0) else None
    sorted_items = sorted_pairs if limit is None else sorted_pairs[:limit]
    result: List[Dict[str, Any]] = []
    for cid, count in sorted_items:
        nm = _resolve_category_name(session_headers, api_url, cid)
        if is_invalid_label(nm):
            continue
        result.append({'category_name': nm, 'ticket_count': count})

    return result


def generate_technician_ranking(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str,
    top_n: int | None = None,
    range_step_tickets: int = 1000,
    display_type: str = '2',
    is_recursive: str = '1',
    include_unassigned: bool = False,
) -> List[Dict[str, Any]]:
    """
    Gera ranking de tickets por técnico (users_id_assign = FIELD_TECH = 5) dentro de um período.
    Baseado no comportamento do script PowerShell (top_technicians.ps1), usando IDs brutos e mapeando para nomes.

    Returns:
        Lista de {tecnico, tickets} ordenada por count
    """
    # Critério de intervalo de datas consistente com os demais rankings
    criteria = add_date_range([], inicio, fim, field=FIELD_CREATED)

    # Flag de exclusão de STATUS_NEW controlada via ambiente
    exclude_new = True
    try:
        env_flag = os.environ.get("TECH_RANK_EXCLUDE_STATUS_NEW")
        if env_flag is None:
            env_flag = os.environ.get("EXCLUDE_STATUS_NEW")
        if env_flag is not None:
            exclude_new = str(env_flag).strip().lower() in {"1", "true", "yes", "on"}
    except Exception:
        pass

    # Contagem streaming simples, como entidades/categorias
    import time as _time
    _t0 = _time.perf_counter()
    # Permitir override do passo via variável de ambiente
    try:
        env_step_raw = os.environ.get("RANGE_STEP_TICKETS")
        if env_step_raw:
            range_step_tickets = max(1, int(env_step_raw))
    except Exception:
        pass
    id_counts = Counter()
    # Usar timeouts específicos para operação de ranking (mais generosos)
    ranking_timeout = ranking_timeouts_sec()
    for row in glpi_client.search_paginated_iter(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[FIELD_TECH, FIELD_STATUS],
        uid_cols=False,
        range_step=range_step_tickets,
        extra_params={'display_type': display_type, 'is_recursive': is_recursive, 'expand_dropdowns': '0'},
        timeout=ranking_timeout
    ):
        # Extrai ID do técnico de forma robusta: tenta campo numérico forçado e fallback
        raw_t = row.get(str(FIELD_TECH)) or row.get('users_id_assign')
        num_id = first_numeric_id(raw_t)
        tech_key = str(num_id) if isinstance(num_id, int) and num_id > 0 else normalize_tech_key(raw_t)
        # Se solicitada a exclusão de "Novo", pule apenas tickets novos não atribuídos
        if exclude_new:
            raw_status = row.get(str(FIELD_STATUS))
            status_num = first_numeric_id(raw_status)
            if isinstance(status_num, int) and status_num == STATUS_NEW and tech_key == '0':
                continue
        id_counts.update([tech_key])

    _t1 = _time.perf_counter()
    try:
        metrics.record_timing('glpi.search_total_ms', (_t1 - _t0) * 1000, tags={'itemtype': 'Ticket', 'stage': 'technician_ranking_simple'})
    except Exception:
        pass

    # Excluir do ranking o bucket de não atribuídos ('0' => "Sem técnico")
    if not include_unassigned:
        id_counts.pop('0', None)

    if not id_counts:
        return []

    # Ordenar e limitar ao top-N antes de resolver nomes
    sorted_pairs = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)
    limit = top_n if (top_n and top_n > 0) else None
    sorted_items = sorted_pairs if limit is None else sorted_pairs[:limit]

    # Resolver nomes somente para IDs presentes no top-N
    top_ids = [safe_int_id(k) for k, _ in sorted_items if safe_int_id(k) > 0]
    names_map = resolve_user_names_fast(session_headers, api_url, top_ids)

    result: List[Dict[str, Any]] = []
    for tech_id_str, count in sorted_items:
        tech_id = safe_int_id(tech_id_str)
        if tech_id > 0:
            tecnico_nome = names_map.get(tech_id) or f"Usuário ID {tech_id}"
        else:
            # tech_id == 0 => não atribuído
            if include_unassigned:
                tecnico_nome = 'Sem técnico'
            else:
                continue
        result.append({'tecnico': tecnico_nome, 'tickets': count})

    return result
