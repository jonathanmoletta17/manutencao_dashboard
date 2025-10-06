# Backend Manutenção

Back-end FastAPI contendo apenas o router de Manutenção.

Conteúdo esperado:
- `main.py` com montagem de `maintenance_router`.
- `api/maintenance_router.py`, `logic/maintenance_logic.py`, `schemas_maintenance.py`.
- `glpi_constants_manutencao.py` contendo somente IDs/status usados pelo domínio de Manutenção.
- Utilitários necessários (`glpi_client`, `criteria_helpers`, `cache`, `logging_setup`).

Env Vars (exemplo):
- `API_URL`, `APP_TOKEN`, `USER_TOKEN` (GLPI)
- `ACTIVE_ENTITY_ID` (se aplicável)
- `CACHE_TTL_SECONDS` (se aplicável)

Execução:
- `python -m uvicorn main:app --reload --host 127.0.0.1 --port 8010`