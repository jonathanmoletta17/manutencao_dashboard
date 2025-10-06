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
- `python -m uvicorn apps.manutencao.backend.main:app --reload --host 127.0.0.1 --port 8010`

Endpoints:
- `GET /api/v1/manutencao/status-totais`
  - Totais gerais por status (Novos, Não solucionados 2+4, Planejados 3, Solucionados 5, Fechados 6, Resolvidos 5+6)
  - Sem filtro de datas; usa cache com TTL (`CACHE_TTL_SEC`).
- `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - Estatísticas no período por status (Novos 1, Pendentes 4, Planejados 2, Resolvidos 5).
- `GET /api/v1/manutencao/ranking-entidades?inicio=YYYY-MM-DD&fim=YYYY-MM-DD&top=10`
- `GET /api/v1/manutencao/ranking-categorias?inicio=YYYY-MM-DD&fim=YYYY-MM-DD&top=10`
- `GET /api/v1/manutencao/tickets-novos?limit=10`
- `GET /api/v1/manutencao/top-atribuicao-entidades?top=10`
  - Ranking global (sem filtro de data) de atribuição por entidades, espelhando `top_entities.ps1`.