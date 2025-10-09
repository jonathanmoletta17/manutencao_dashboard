"""
Helpers de conversão e extração numérica comuns ao backend.

Objetivo: evitar duplicação de lógica como `safe_int` e
`get_first_numeric_id` entre diferentes módulos de lógica.
"""
from typing import Any, Optional


def to_int_zero(value: Any) -> int:
    """
    Converte um valor para inteiro de forma segura, retornando 0 em caso de falha.
    Usa `str(value)` para lidar com valores como `None`, números em string, etc.
    """
    try:
        return int(str(value))
    except Exception:
        return 0


def first_numeric_id(value: Any) -> Optional[int]:
    """
    Extrai o primeiro ID numérico de um valor potencialmente heterogêneo.
    - Se `value` for lista, retorna o primeiro elemento que for dígito.
    - Se `value` for string/numérico, retorna o inteiro se `isdigit()`.
    - Caso contrário, retorna None.
    """
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