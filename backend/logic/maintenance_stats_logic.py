"""
Lógica de métricas e totais de status para o Dashboard de Manutenção
Separada por responsabilidade (stats)
"""
from typing import Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    def _criteria_for_status(status: int | str) -> list[dict]:
        return add_date_range(
            add_status([], status),
            inicio,
            fim,
            field=FIELD_CREATED,
        )

    def _count_total(status: int | str) -> int:
        return glpi_client.search_totalcount(
            headers=session_headers,
            api_url=api_url,
            itemtype='Ticket',
            criteria=_criteria_for_status(status),
            uid_cols=False,
        )

    # Paralelizar contagens por status para reduzir latência
    status_map = {
        'novos': STATUS_NEW,
        'em_atendimento': STATUS_ASSIGNED,
        'pendentes': STATUS_PENDING,
        'planejados': STATUS_PLANNED,
        'solucionados': STATUS_SOLVED,
        'fechados': STATUS_CLOSED,
    }

    results: Dict[str, int] = {k: 0 for k in status_map.keys()}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_count_total, st): name for name, st in status_map.items()}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                results[name] = int(fut.result())
            except Exception:
                # Em caso de falha pontual, mantém zero e segue adiante
                results[name] = 0

    resolvidos = results['solucionados'] + results['fechados']
    novos = results['novos']
    em_atendimento = results['em_atendimento']
    pendentes = results['pendentes']
    planejados = results['planejados']

    return {
        'novos': novos,
        'em_atendimento': em_atendimento,
        'pendentes': pendentes,
        'planejados': planejados,
        'resolvidos': resolvidos,
    }


# Removida função de totais globais por status por duplicidade com métricas por período