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
from ..config import range_step_tickets


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
        count = 0
        for _row in glpi_client.search_paginated_iter(
            headers=session_headers,
            api_url=api_url,
            itemtype='Ticket',
            criteria=criteria,
            forcedisplay=[FIELD_ID],
            uid_cols=False,
            range_step=range_step_tickets(),
        ):
            count += 1
        return count


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


# Removida função de totais globais por status por duplicidade com métricas por período