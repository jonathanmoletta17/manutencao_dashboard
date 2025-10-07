"""
Lógica de rankings (entidades e categorias) para o Dashboard de Manutenção
Separada por responsabilidade (ranking)
"""
from typing import Dict, List, Any
from .. import glpi_client
from .glpi_constants import (
    FIELD_CREATED, FIELD_ENTITY, FIELD_CATEGORY, FIELD_TECH,
)


def generate_entity_ranking(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Gera ranking de tickets por entidade dentro de um período.
    Implementação robusta baseada em ID da entidade (display_type=2),
    mapeando posteriormente para o nome completo da entidade.

    Returns:
        Lista de {entity_name, ticket_count} ordenada por count
    """
    # Critérios com link correto entre condições (sem entrada solta de 'AND')
    criteria = [
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]

    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[str(FIELD_ENTITY)],
        uid_cols=False,
        range_step=300,
        extra_params={'display_type': '2', 'is_recursive': '1'}
    )

    id_counts: Dict[str, int] = {}
    for row in tickets_data:
        eid = str(row.get(str(FIELD_ENTITY), '0'))
        if not eid:
            eid = '0'
        id_counts[eid] = id_counts.get(eid, 0) + 1

    if not id_counts:
        return []

    entity_rows = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Entity',
        criteria=[],
        forcedisplay=['Entity.id', 'Entity.completename', 'Entity.name'],
        uid_cols=True,
        range_step=300
    )

    def sanitize_label(s: Any) -> str:
        if not isinstance(s, str):
            s = str(s) if s is not None else ''
        t = s
        replacements = {
            '&amp;#62;': '>',
            '&#62;': '>',
            '&gt;': '>',
            '&amp;gt;': '>',
            '&#39;': "'",
            '&amp;': '&',
        }
        for k, v in replacements.items():
            t = t.replace(k, v)
        return t

    name_by_id: Dict[str, str] = {}
    for er in entity_rows:
        oid = str(er.get('Entity.id', ''))
        comp = er.get('Entity.completename')
        nm = er.get('Entity.name')
        label = sanitize_label(comp or nm or oid)
        if oid and (oid not in name_by_id):
            name_by_id[oid] = label

    sorted_items = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result: List[Dict[str, Any]] = []
    for eid, count in sorted_items:
        nm = name_by_id.get(eid)
        if not nm:
            nm = '(sem entidade)' if eid == '0' else eid
        result.append({'entity_name': nm, 'ticket_count': count})

    return result


def generate_entity_top_all(
    api_url: str,
    session_headers: Dict[str, str],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Top N de atribuição por entidades (sem filtro de datas),
    espelhando o script PowerShell top_entities.ps1.
    """
    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[],
        forcedisplay=[str(FIELD_ENTITY)],
        uid_cols=False,
        range_step=300,
        extra_params={'display_type': '2', 'is_recursive': '1'}
    )

    id_counts: Dict[str, int] = {}
    for row in tickets_data:
        eid = str(row.get(str(FIELD_ENTITY), '0'))
        if not eid:
            eid = '0'
        id_counts[eid] = id_counts.get(eid, 0) + 1

    if not id_counts:
        return []

    entity_rows = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Entity',
        criteria=[],
        forcedisplay=['Entity.id', 'Entity.completename', 'Entity.name'],
        uid_cols=True,
        range_step=300
    )

    def sanitize_label(s: Any) -> str:
        if not isinstance(s, str):
            s = str(s) if s is not None else ''
        t = s
        replacements = {
            '&amp;#62;': '>',
            '&#62;': '>',
            '&gt;': '>',
            '&amp;gt;': '>',
            '&#39;': "'",
            '&amp;': '&',
        }
        for k, v in replacements.items():
            t = t.replace(k, v)
        return t

    name_by_id: Dict[str, str] = {}
    for er in entity_rows:
        oid = str(er.get('Entity.id', ''))
        comp = er.get('Entity.completename')
        nm = er.get('Entity.name')
        label = sanitize_label(comp or nm or oid)
        if oid and (oid not in name_by_id):
            name_by_id[oid] = label

    sorted_items = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result: List[Dict[str, Any]] = []
    for eid, count in sorted_items:
        nm = name_by_id.get(eid)
        if not nm:
            nm = '(sem entidade)' if eid == '0' else eid
        result.append({'entity_name': nm, 'ticket_count': count})

    return result


def generate_category_ranking(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Gera ranking de tickets por categoria.
    Returns:
        Lista de {category_name, ticket_count} ordenada por count
    """
    criteria = [
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]

    # Buscar IDs brutos de categoria no Ticket para contagem confiável
    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[str(FIELD_CATEGORY)],
        uid_cols=False,
        range_step=300,
        extra_params={'display_type': '2', 'is_recursive': '1'}
    )

    id_counts: Dict[str, int] = {}
    for row in tickets_data:
        cid = str(row.get(str(FIELD_CATEGORY), '0'))
        if not cid:
            cid = '0'
        id_counts[cid] = id_counts.get(cid, 0) + 1

    if not id_counts:
        return []

    # Mapear IDs para nomes amigáveis de categoria
    category_rows = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='ITILCategory',
        criteria=[],
        forcedisplay=['ITILCategory.id', 'ITILCategory.completename', 'ITILCategory.name'],
        uid_cols=True,
        range_step=300
    )

    def sanitize_label(s: Any) -> str:
        if not isinstance(s, str):
            s = str(s) if s is not None else ''
        t = s
        replacements = {
            '&amp;#62;': '>',
            '&#62;': '>',
            '&gt;': '>',
            '&amp;gt;': '>',
            '&#39;': "'",
            '&amp;': '&',
        }
        for k, v in replacements.items():
            t = t.replace(k, v)
        return t

    name_by_id: Dict[str, str] = {}
    for cr in category_rows:
        oid = str(cr.get('ITILCategory.id', ''))
        comp = cr.get('ITILCategory.completename')
        nm = cr.get('ITILCategory.name')
        label = sanitize_label(comp or nm or oid)
        if oid and (oid not in name_by_id):
            name_by_id[oid] = label

    sorted_items = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result: List[Dict[str, Any]] = []
    for cid, count in sorted_items:
        nm = name_by_id.get(cid)
        if not nm:
            nm = 'sem' if cid == '0' else cid
        result.append({'category_name': nm, 'ticket_count': count})

    return result


def generate_category_top_all(
    api_url: str,
    session_headers: Dict[str, str],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Top N de atribuição por categorias (sem filtro de datas),
    espelhando o script PowerShell top_categories.ps1.
    """
    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[],
        forcedisplay=[str(FIELD_CATEGORY)],
        uid_cols=False,
        range_step=300,
        extra_params={'display_type': '2', 'is_recursive': '1'}
    )

    id_counts: Dict[str, int] = {}
    for row in tickets_data:
        cid = str(row.get(str(FIELD_CATEGORY), '0'))
        if not cid:
            cid = '0'
        id_counts[cid] = id_counts.get(cid, 0) + 1

    if not id_counts:
        return []

    category_rows = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='ITILCategory',
        criteria=[],
        forcedisplay=['ITILCategory.id', 'ITILCategory.completename', 'ITILCategory.name'],
        uid_cols=True,
        range_step=300
    )

    def sanitize_label(s: Any) -> str:
        if not isinstance(s, str):
            s = str(s) if s is not None else ''
        t = s
        replacements = {
            '&amp;#62;': '>',
            '&#62;': '>',
            '&gt;': '>',
            '&amp;gt;': '>',
            '&#39;': "'",
            '&amp;': '&',
        }
        for k, v in replacements.items():
            t = t.replace(k, v)
        return t

    name_by_id: Dict[str, str] = {}
    for cr in category_rows:
        oid = str(cr.get('ITILCategory.id', ''))
        comp = cr.get('ITILCategory.completename')
        nm = cr.get('ITILCategory.name')
        label = sanitize_label(comp or nm or oid)
        if oid and (oid not in name_by_id):
            name_by_id[oid] = label

    sorted_items = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result: List[Dict[str, Any]] = []
    for cid, count in sorted_items:
        nm = name_by_id.get(cid)
        if not nm:
            nm = 'sem' if cid == '0' else cid
        result.append({'category_name': nm, 'ticket_count': count})

    return result


def generate_technician_ranking(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str,
    top_n: int = 20
) -> List[Dict[str, Any]]:
    """
    Gera ranking de tickets por técnico (users_id_assign = FIELD_TECH = 5) dentro de um período.
    Baseado no comportamento do script PowerShell (top_technicians.ps1), usando IDs brutos e mapeando para nomes.

    Returns:
        Lista de {tecnico, tickets} ordenada por count
    """
    criteria = [
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]

    # Buscar IDs de técnicos atribuídos diretamente do Ticket (display_type=2 retorna ID bruto)
    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[str(FIELD_TECH)],
        uid_cols=False,
        range_step=300,
        extra_params={'display_type': '2', 'is_recursive': '1'}
    )

    def normalize_tech_key(raw: Any) -> str:
        """Normaliza users_id_assign para um único bucket 'Sem técnico' quando não há ID numérico válido."""
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

    id_counts: Dict[str, int] = {}
    for row in tickets_data:
        raw_val = row.get(str(FIELD_TECH))
        key = normalize_tech_key(raw_val)
        id_counts[key] = id_counts.get(key, 0) + 1

    if not id_counts:
        return []

    # Resolver nomes dos técnicos via /User/{id}, aproveitando utilitário existente
    def safe_int_id(s: str) -> int:
        try:
            return int(s)
        except Exception:
            return 0

    tech_ids = [safe_int_id(k) for k in id_counts.keys() if k.isdigit() and int(k) > 0]
    names_map = glpi_client.get_user_names_in_batch_with_fallback(session_headers, api_url, tech_ids)

    sorted_items = sorted(id_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    result: List[Dict[str, Any]] = []
    for tech_id_str, count in sorted_items:
        tech_id = safe_int_id(tech_id_str)
        if tech_id <= 0:
            tecnico_nome = 'Sem técnico'
        else:
            tecnico_nome = names_map.get(tech_id) or f"Usuário ID {tech_id}"
        result.append({'tecnico': tecnico_nome, 'tickets': count})

    return result