import os
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from .cache import cache
from . import metrics
from ..config import name_workers, timeouts_sec

def resolve_user_names_fast(headers: Dict[str, str], api_url: str, user_ids: List[int]) -> Dict[int, str]:
    """
    Resolve nomes de usuários do GLPI com cache e concorrência.
    - Usa cache global para reduzir chamadas repetidas.
    - Faz GET /User/{id} em paralelo com timeout agressivo.
    """
    # Normaliza IDs e filtra inválidos
    unique_ids = sorted({int(uid) for uid in user_ids if isinstance(uid, int) and uid > 0})
    names_map: Dict[int, str] = {}
    to_fetch: List[int] = []

    for uid in unique_ids:
        cached = cache.get(f"user_name_{uid}")
        if cached:
            names_map[uid] = cached
            metrics.increment('cache.hit', tags={'resource': 'user_name'})
        else:
            to_fetch.append(uid)
            metrics.increment('cache.miss', tags={'resource': 'user_name'})

    def fetch(uid: int) -> tuple[int, str]:
        try:
            url = f"{api_url}/User/{uid}"
            import time
            t0 = time.perf_counter()
            resp = requests.get(url, headers=headers, timeout=timeouts_sec())
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data:
                data = data[0]
            first_name = data.get('firstname', '')
            last_name = data.get('realname', '')
            full_name = f"{first_name} {last_name}".strip()
            name = full_name if full_name else f"Usuário ID {uid}"
            t1 = time.perf_counter()
            metrics.record_timing('glpi.user_lookup_ms', (t1 - t0) * 1000, tags={'user_id': str(uid)})
            return uid, name
        except requests.exceptions.Timeout:
            metrics.increment('glpi.timeout', tags={'stage': 'user_lookup'})
            return uid, f"Usuário ID {uid} (Timeout)"
        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', None)
            if status == 403:
                return uid, f"Usuário ID {uid} (Sem Permissão)"
            elif status == 404:
                return uid, f"Usuário ID {uid} (Não Encontrado)"
            else:
                return uid, f"Usuário ID {uid} (Erro HTTP {status})"
        except requests.exceptions.RequestException:
            metrics.increment('glpi.network_error', tags={'stage': 'user_lookup'})
            return uid, f"Usuário ID {uid} (Erro de Rede)"
        except Exception:
            return uid, f"Usuário ID {uid} (Dados Incompletos)"

    if to_fetch:
        max_workers = name_workers()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch, uid): uid for uid in to_fetch}
            for fut in as_completed(futures):
                uid, name = fut.result()
                names_map[uid] = name
                try:
                    cache.set(f"user_name_{uid}", name)
                except Exception:
                    pass

    return names_map