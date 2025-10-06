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


def generate_entity_ranking(
    api_url: str,
    session_headers: Dict[str, str],
    inicio: str,
    fim: str,
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Gera ranking de tickets por entidade.
    
    Returns:
        Lista de {entity_name, ticket_count} ordenada por count
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
        forcedisplay=[FIELD_ID, FIELD_ENTITY],
        uid_cols=True
    )
    
    # Contar por entidade
    entity_counts: Dict[str, int] = {}
    for ticket in tickets_data:
        entity_name = ticket.get(FIELD_ENTITY, 'Sem Entidade')
        if isinstance(entity_name, str) and entity_name:
            entity_counts[entity_name] = entity_counts.get(entity_name, 0) + 1
    
    # Ordenar e pegar top N
    sorted_entities = sorted(
        entity_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    return [
        {'entity_name': name, 'ticket_count': count}
        for name, count in sorted_entities
    ]


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
    
    # Campos: ID, Nome (título), Solicitante(4), Data(15), Entidade(80)
    tickets_data = glpi_client.search_paginated(
        headers=session_headers,
        api_url=api_url,
        itemtype='Ticket',
        criteria=criteria,
        forcedisplay=[FIELD_ID, FIELD_NAME, '4', FIELD_CREATED, FIELD_ENTITY],
        uid_cols=True,
        range_step=limit
    )
    
    # Formatar resposta
    result = []
    for ticket in tickets_data[:limit]:
        result.append({
            'id': ticket.get(FIELD_ID, 0),
            'titulo': ticket.get(FIELD_NAME, 'Sem título'),
            'solicitante': ticket.get('4', 'Não informado'),
            'data': ticket.get(FIELD_CREATED, '')[:10] if ticket.get(FIELD_CREATED) else '',
            'entidade': ticket.get(FIELD_ENTITY, 'Sem entidade')
        })
    
    return result
