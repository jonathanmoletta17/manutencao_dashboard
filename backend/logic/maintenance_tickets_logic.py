"""
Lógica de tickets (novos) para o Dashboard de Manutenção
Separada por responsabilidade (tickets)
"""
from typing import Dict, List, Any
from .. import glpi_client
from .glpi_constants import (
    FIELD_STATUS, FIELD_CREATED, FIELD_ID, FIELD_NAME,
    FIELD_ENTITY, FIELD_REQUESTER,
    STATUS_NEW,
)
from .criteria_helpers import add_status
from ..utils.convert import to_int_zero, first_numeric_id


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
    criteria = add_status([], STATUS_NEW)

    # Campos forçados: título, id, solicitante, data, entidade
    forced = [str(FIELD_NAME), str(FIELD_ID), str(FIELD_REQUESTER), str(FIELD_CREATED), str(FIELD_ENTITY)]
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

    # Ordenação por ID desc e aplicação do limite
    sorted_tickets = sorted(
        tickets_data,
        key=lambda x: to_int_zero(x.get(str(FIELD_ID))),
        reverse=True
    )[:limit]

    requester_ids = []
    for t in sorted_tickets:
        rid = first_numeric_id(t.get('4'))
        if isinstance(rid, int):
            requester_ids.append(rid)

    names_map = glpi_client.get_user_names_in_batch_with_fallback(session_headers, api_url, requester_ids)

    result: List[Dict[str, Any]] = []
    for t in sorted_tickets:
        ticket_id = to_int_zero(t.get(str(FIELD_ID)))
        titulo = t.get(str(FIELD_NAME)) or 'Sem título'
        created_raw = t.get(str(FIELD_CREATED))

        data_fmt = ''
        if isinstance(created_raw, str) and created_raw:
            try:
                from datetime import datetime
                dt = datetime.strptime(created_raw, "%Y-%m-%d %H:%M:%S")
                data_fmt = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                data_fmt = created_raw[:16]

        solicitante = 'Não informado'
        raw_req = t.get('4')
        if isinstance(raw_req, str) and not raw_req.isdigit():
            solicitante = raw_req
        else:
            rid = first_numeric_id(raw_req)
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