"""
Lógica de métricas e totais de status para o Dashboard de Manutenção
Separada por responsabilidade (stats)
"""
from typing import Dict
from .. import glpi_client
from .glpi_constants import (
    FIELD_STATUS, FIELD_CREATED, FIELD_ID,
    STATUS_NEW, STATUS_SOLVED
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
    # Novos (status 1)
    criteria_novos = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': STATUS_NEW},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]
    novos_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_novos,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )


    # Em atendimento (status 2 - Atribuído/Em progresso)
    criteria_em_atendimento = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '2'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]
    em_atendimento_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_em_atendimento,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Pendentes (status 4)
    criteria_pendentes = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '4'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
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
    # Ajuste: Planejados devem refletir status 3 (Planejado),
    # alinhando com os totais globais.
    criteria_planejados = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '3'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]
    planejados_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_planejados,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    # Resolvidos devem incluir Solucionados (5) e Fechados (6)
    criteria_resolvidos_5 = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '5'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]
    resolvidos_5_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_resolvidos_5,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    criteria_resolvidos_6 = [
        {'field': FIELD_STATUS, 'searchtype': 'equals', 'value': '6'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'morethan', 'value': f'{inicio} 00:00:00'},
        {'link': 'AND', 'field': FIELD_CREATED, 'searchtype': 'lessthan', 'value': f'{fim} 23:59:59'},
    ]
    resolvidos_6_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria_resolvidos_6,
        forcedisplay=[FIELD_ID],
        uid_cols=False
    )

    return {
        'novos': len(novos_data),
        'em_atendimento': len(em_atendimento_data),
        'pendentes': len(pendentes_data),
        'planejados': len(planejados_data),
        'resolvidos': (len(resolvidos_5_data) + len(resolvidos_6_data))
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

    em_atendimento = len(status2_data)
    nao_solucionados = em_atendimento + len(status4_data)
    resolvidos = len(solucionados_data) + len(fechados_data)

    return {
        'novos': len(novos_data),
        'em_atendimento': em_atendimento,
        'nao_solucionados': nao_solucionados,
        'planejados': len(planejados_data),
        'solucionados': len(solucionados_data),
        'fechados': len(fechados_data),
        'resolvidos': resolvidos,
    }