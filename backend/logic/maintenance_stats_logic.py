"""
Lógica de métricas e totais de status para o Dashboard de Manutenção
Separada por responsabilidade (stats)
"""
from typing import Dict
from .. import glpi_client
from .glpi_constants import (
    FIELD_STATUS, FIELD_CREATED, FIELD_ID,
    STATUS_NEW, STATUS_ASSIGNED, STATUS_PLANNED, STATUS_PENDING, STATUS_SOLVED, STATUS_CLOSED,
)
from .criteria_helpers import add_date_range, add_status


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
    # Helpers internos para reduzir repetição e manter código limpo
    def _count_by_status_in_range(status: int | str) -> int:
        criteria = add_date_range(
            add_status([], status),
            inicio,
            fim,
            field=FIELD_CREATED,
        )
        data = glpi_client.search_paginated(
            headers=session_headers,
            api_url=api_url,
            itemtype='Ticket',
            criteria=criteria,
            forcedisplay=[FIELD_ID],
            uid_cols=False,
        )
        return len(data)


    # Em atendimento (status 2 - Atribuído/Em progresso)
    novos = _count_by_status_in_range(STATUS_NEW)
    em_atendimento = _count_by_status_in_range(STATUS_ASSIGNED)

    # Pendentes (status 4)
    pendentes = _count_by_status_in_range(STATUS_PENDING)

    # Planejados (status 3 - Planejado)
    # Alinhado com os totais globais.
    planejados = _count_by_status_in_range(STATUS_PLANNED)

    # Resolvidos devem incluir Solucionados (5) e Fechados (6)
    resolvidos = _count_by_status_in_range(STATUS_SOLVED) + _count_by_status_in_range(STATUS_CLOSED)

    return {
        'novos': novos,
        'em_atendimento': em_atendimento,
        'pendentes': pendentes,
        'planejados': planejados,
        'resolvidos': resolvidos,
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
        criteria=add_status([], '1'),
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Em progresso/Atribuídos (2)
    status2_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=add_status([], '2'),
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Em andamento/Pendentes (4)
    status4_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=add_status([], '4'),
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Planejados (3)
    planejados_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=add_status([], '3'),
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Solucionados (5)
    def _count_by_status_total(status: int | str) -> int:
        data = glpi_client.search_paginated(
            headers=session_headers,
            api_url=api_url,
            itemtype='Ticket',
            criteria=add_status([], status),
            forcedisplay=[FIELD_ID],
            uid_cols=False,
        )
        return len(data)

    novos_data = _count_by_status_total(STATUS_NEW)
    status2_data = _count_by_status_total(STATUS_ASSIGNED)
    status4_data = _count_by_status_total(STATUS_PENDING)
    planejados_data = _count_by_status_total(STATUS_PLANNED)
    solucionados_data = _count_by_status_total(STATUS_SOLVED)
    fechados_data = _count_by_status_total(STATUS_CLOSED)

    em_atendimento = status2_data
    nao_solucionados = em_atendimento + status4_data
    resolvidos = solucionados_data + fechados_data

    return {
        'novos': novos_data,
        'em_atendimento': em_atendimento,
        'nao_solucionados': nao_solucionados,
        'planejados': planejados_data,
        'solucionados': solucionados_data,
        'fechados': fechados_data,
        'resolvidos': resolvidos,
    }