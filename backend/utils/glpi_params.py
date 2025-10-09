"""
Helpers para construção de parâmetros de busca do GLPI.

Objetivo: centralizar a montagem de `criteria`, `forcedisplay`, `uid_cols`
e `extra_params` em um único ponto reutilizável e testável.
"""
from typing import Any, Dict, List, Optional


def build_search_params(
    uid_cols: bool = True,
    forcedisplay: Optional[List[str]] = None,
    criteria: Optional[List[Dict[str, Any]]] = None,
    extra_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if uid_cols:
        params['uid_cols'] = '1'
    if forcedisplay:
        for i, f in enumerate(forcedisplay):
            params[f'forcedisplay[{i}]'] = f
    if criteria:
        for i, c in enumerate(criteria):
            for k, v in c.items():
                params[f'criteria[{i}][{k}]'] = v
    if extra_params:
        for k, v in extra_params.items():
            params[str(k)] = v
    return params


def mask_sensitive_keys(d: Dict[str, Any], sensitive_substrings: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Retorna uma cópia de `d` com valores mascarados para chaves que contenham
    substrings sensíveis (ex.: 'token').
    """
    if sensitive_substrings is None:
        sensitive_substrings = ['token']
    masked: Dict[str, Any] = {}
    for k, v in d.items():
        lk = str(k).lower()
        if any(sub in lk for sub in sensitive_substrings):
            masked[k] = '***'
        else:
            masked[k] = v
    return masked