"""
Helpers de critérios para buscas na API GLPI.

Objetivos:
- Centralizar montagem de critérios (status, intervalo de datas) para evitar repetição.
- Normalizar datas para limites de dia (início 00:00:00, fim 23:59:59).
- Evitar efeitos colaterais: funções são puras e retornam nova lista.

Uso típico:
    criteria = add_status([], '1')
    criteria = add_date_range(criteria, '2024-01-01', '2024-01-31')

Observações sobre indexação de critérios:
- O cliente (`glpi_client.search_paginated`) indexa cada critério na ordem do array
  como `criteria[{i}][...]`. Manter a ordem garante consistência da query.
"""
from typing import Any, Dict, List, Tuple

from .glpi_constants import FIELD_CREATED, FIELD_STATUS


def normalize_date_range(inicio: str, fim: str) -> Tuple[str, str]:
    """
    Normaliza datas para incluir limites de dia.

    - Se `inicio` não tiver parte de hora, adiciona `00:00:00`.
    - Se `fim` não tiver parte de hora, adiciona `23:59:59`.

    Não valida formato; assume entradas no padrão `YYYY-MM-DD` ou
    `YYYY-MM-DD HH:MM:SS`.
    """
    has_time_start = " " in inicio
    has_time_end = " " in fim

    inicio_norm = inicio if has_time_start else f"{inicio} 00:00:00"
    fim_norm = fim if has_time_end else f"{fim} 23:59:59"
    return inicio_norm, fim_norm


def add_date_range(
    criteria: List[Dict[str, Any]],
    inicio: str,
    fim: str,
    field: str = FIELD_CREATED,
) -> List[Dict[str, Any]]:
    """
    Adiciona critérios de intervalo de datas (>= inicio, <= fim) ao array.

    - Preserva a lista original e retorna uma nova.
    - O primeiro critério adicionado omite `link` se o array estava vazio.
      Caso contrário, usa `link='AND'`.
    - O segundo critério sempre usa `link='AND'`.
    """
    inicio_norm, fim_norm = normalize_date_range(inicio, fim)

    new_criteria = list(criteria)  # cópia rasa
    # Primeiro critério (>= inicio)
    first = {
        'field': field,
        'searchtype': 'morethan',
        'value': inicio_norm,
    }
    if len(new_criteria) > 0:
        first['link'] = 'AND'
    new_criteria.append(first)

    # Segundo critério (<= fim)
    second = {
        'link': 'AND',
        'field': field,
        'searchtype': 'lessthan',
        'value': fim_norm,
    }
    new_criteria.append(second)

    return new_criteria


def add_status(
    criteria: List[Dict[str, Any]],
    status: str,
    field: str = FIELD_STATUS,
    searchtype: str = 'equals',
) -> List[Dict[str, Any]]:
    """
    Adiciona critério de status ao array de critérios.

    - O critério usa `searchtype='equals'` por padrão.
    - Inclui `link='AND'` se já houver critérios anteriores.
    - Retorna nova lista sem mutar a original.
    """
    new_criteria = list(criteria)
    status_crit: Dict[str, Any] = {
        'field': field,
        'searchtype': searchtype,
        'value': str(status),
    }
    if len(new_criteria) > 0:
        status_crit['link'] = 'AND'
    new_criteria.append(status_crit)
    return new_criteria