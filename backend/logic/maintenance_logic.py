"""
Lógica de negócio para métricas do Dashboard de Manutenção
Processa dados de tickets GLPI específicos para manutenção
"""
from typing import Dict, List, Any
from .. import glpi_client
from .glpi_constants import (
    FIELD_STATUS, FIELD_CREATED, FIELD_ID, FIELD_NAME,
    FIELD_ENTITY, FIELD_CATEGORY,
    STATUS_NEW, STATUS_PENDING_PLANNED, STATUS_SOLVED
)


def generate_maintenance_stats(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str
) -> Dict[str, int]:
    """
    Gera estatísticas gerais de manutenção por status.
    
    Returns:
        Dict com novos, pendentes, planejados, resolvidos
    """
    # Status específicos de manutenção
    # 1=Novo, 4=Pendente, 2=Em Progresso/Planejado, 5=Resolvido
    
    # Novos (status 1)
    criteria_novos = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': STATUS_NEW},
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
        {'link': 'AND'}
    ]
    novos_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_novos,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )
    
    # Pendentes (status 4)
    criteria_pendentes = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '4'},
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
        {'link': 'AND'}
    ]
    pendentes_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_pendentes,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )
    
    # Planejados (status 2 - Em progresso/Atribuído)
    criteria_planejados = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '2'},
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
        {'link': 'AND'}
    ]
    planejados_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_planejados,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )
    
    # Resolvidos (status 5)
    criteria_resolvidos = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': STATUS_SOLVED},
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
        {'link': 'AND'}
    ]
    resolvidos_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_resolvidos,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )
    
    return {
        'novos': len(novos_data),
        'pendentes': len(pendentes_data),
        'planejados': len(planejados_data),
        'resolvidos': len(resolvidos_data)
    }


def generate_status_totals(
    api_url: str,
    session_headers: Dict[str, str],
) -> Dict[str, int]:
    """
    Gera totais gerais por status, espelhando o script PowerShell.
    Sem filtro de datas: conta todos os tickets por status.

    Retorna:
        Dict com: novos (1), nao_solucionados (2+4), planejados (3), solucionados (5), fechados (6), resolvidos (5+6)
    """
    # Novos (1)
    novos_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[{'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '1'}],
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Em progresso/Atribuídos (2)
    status2_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[{'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '2'}],
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Em andamento/Pendentes (4)
    status4_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[{'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '4'}],
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Planejados (3)
    planejados_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[{'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '3'}],
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Solucionados (5)
    solucionados_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[{'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '5'}],
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Fechados (6)
    fechados_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=[{'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '6'}],
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    nao_solucionados = len(status2_data) + len(status4_data)
    resolvidos = len(solucionados_data) + len(fechados_data)

    return {
        'novos': len(novos_data),
        'nao_solucionados': nao_solucionados,
        'planejados': len(planejados_data),
        'solucionados': len(solucionados_data),
        'fechados': len(fechados_data),
        'resolvidos': resolvidos,
    }


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
    # Buscar tickets do período com ID de entidade bruto
    criteria = [
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
        {'link': 'AND'}
    ]

    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[str(FIELD_ENTITY)],
        uid_cols=False,
        range_step=300,
        extra_params={'display_type': '2'}
    )

    # Contar por ID de entidade
    id_counts: Dict[str, int] = {}
    for row in tickets_data:
        eid = str(row.get(str(FIELD_ENTITY), '0'))
        if not eid:
            eid = '0'
        id_counts[eid] = id_counts.get(eid, 0) + 1

    if not id_counts:
        return []

    # Buscar nomes das entidades
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
        # Remoção básica de entidades HTML comuns
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

    # Ordenar e mapear nomes
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

    Etapas:
    - Busca todos os tickets com ID de entidade bruto (display_type=2)
    - Conta por ID de entidade
    - Busca entidades para mapear ID -> nome (completename/name)
    - Retorna top N ordenado por contagem
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
    # Buscar todos os tickets no período
    criteria = [
        {'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
        {'link': 'AND'}
    ]
    
    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[FIELD_ID, FIELD_CATEGORY],
        uid_cols=True
    )
    
    # Contar por categoria
    category_counts: Dict[str, int] = {}
    for ticket in tickets_data:
        category_name = ticket.get(FIELD_CATEGORY, 'Sem Categoria')
        if isinstance(category_name, str) and category_name:
            category_counts[category_name] = category_counts.get(category_name, 0) + 1
    
    # Ordenar e pegar top N
    sorted_categories = sorted(
        category_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    return [
        {'category_name': name, 'ticket_count': count}
        for name, count in sorted_categories
    ]


def get_maintenance_new_tickets(
    api_url: str,
    session_headers: Dict[str, str],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Busca os tickets novos mais recentes de manutenção.
    
    Returns:
        Lista de tickets novos com id, titulo, solicitante, data, entidade
    """
    # Buscar tickets com status Novo (1)
    criteria = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': STATUS_NEW}
    ]

    # Campos conforme DTIC: Título(1), ID(2), Requisitante(4), Data de Criação(15), Entidade(80)
    forced = [str(FIELD_NAME), str(FIELD_ID), '4', str(FIELD_CREATED), str(FIELD_ENTITY)]
    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=forced,
        uid_cols=False,
        range_step=100,
        extra_params={'expand_dropdowns': '1', 'is_recursive': '1'}
    )

    if not tickets_data:
        return []

    # Ordena por ID desc e limita
    def safe_int(v: Any) -> int:
        try:
            return int(str(v))
        except Exception:
            return 0

    sorted_tickets = sorted(tickets_data, key=lambda x: safe_int(x.get(str(FIELD_ID))), reverse=True)[:limit]

    # Extrai IDs de requisitante para resolver nomes em lote
    def get_first_numeric_id(value: Any):
        if value is None:
            return None
        if isinstance(value, list):
            for v in value:
                v_str = str(v)
                if v_str.isdigit():
                    return int(v_str)
            return None
        v_str = str(value)
        return int(v_str) if v_str.isdigit() else None

    requester_ids = []
    for t in sorted_tickets:
        rid = get_first_numeric_id(t.get('4'))
        if isinstance(rid, int):
            requester_ids.append(rid)

    names_map = glpi_client.get_user_names_in_batch_with_fallback(session_headers, api_url, requester_ids)

    # Formatar resposta alinhada ao DTIC
    result: List[Dict[str, Any]] = []
    for t in sorted_tickets:
        ticket_id = safe_int(t.get(str(FIELD_ID)))
        titulo = t.get(str(FIELD_NAME)) or 'Sem título'
        created_raw = t.get(str(FIELD_CREATED))

        # Formatação de data: dd/MM/YYYY HH:mm
        data_fmt = ''
        if isinstance(created_raw, str) and created_raw:
            try:
                from datetime import datetime
                dt = datetime.strptime(created_raw, "%Y-%m-%d %H:%M:%S")
                data_fmt = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                data_fmt = created_raw[:16]

        # Solicitante: se expand_dropdowns já trouxe nome legível, usa; senão, resolve pelo mapa
        solicitante = 'Não informado'
        raw_req = t.get('4')
        if isinstance(raw_req, str) and not raw_req.isdigit():
            solicitante = raw_req
        else:
            rid = get_first_numeric_id(raw_req)
            if isinstance(rid, int) and rid in names_map:
                solicitante = names_map[rid]

        entidade = t.get(str(FIELD_ENTITY)) or 'Sem entidade'

        result.append({
            'id': ticket_id,
            'titulo': titulo,
            'solicitante': solicitante,
            'data': data_fmt,
            'entidade': entidade
        })

    return result


def generate_category_top_all(
    api_url: str,
    session_headers: Dict[str, str],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Top N de atribuição por categorias (sem filtro de datas),
    espelhando o script PowerShell top_categories.ps1.

    Etapas:
    - Busca todos os tickets com ID de categoria bruto (display_type=2)
    - Conta por ID de categoria (fallback 0 quando ausente)
    - Busca categorias para mapear ID -> nome (completename/name)
    - Retorna top N ordenado por contagem
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
