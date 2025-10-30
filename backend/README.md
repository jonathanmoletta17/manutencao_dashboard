Manutenção Backend

Endpoints

- `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - Estatísticas gerais por período, com filtro de datas.
  - Campos: Novos (1), Em atendimento (2), Pendentes (4), Planejados (3), Resolvidos (5+6).
  - Usa cache com TTL (`CACHE_TTL_SEC`).

<!-- Endpoint removido por duplicidade com métricas por período (stats-gerais) -->

- `GET /api/v1/manutencao/top-atribuicao-entidades?top=10` (omita `top` ou use `top=0` para todos)
  - Ranking global por entidade com contagem de tickets.
  - Implementa busca de IDs brutos (`display_type=2`) e mapeamento para nomes completos.

- `GET /api/v1/manutencao/top-atribuicao-categorias?top=10` (omita `top` ou use `top=0` para todos)
  - Ranking global por categoria com contagem de tickets.
  - Espelha o script `top_categories.ps1`: busca IDs brutos (`display_type=2`), conta por ID e mapeia para `ITILCategory.completename`/`name`.

Modelos de resposta (exemplos)

Entidades:
```
[
  { "entity_name": "DTIC > Manutenção", "ticket_count": 42 },
  { "entity_name": "DTIC > Conservação", "ticket_count": 31 }
]
```

Categorias:
```
[
  { "category_name": "Infraestrutura > Eletricidade", "ticket_count": 27 },
  { "category_name": "Hidráulica", "ticket_count": 19 }
]
```

Configuração

- Backend requer variáveis de ambiente:
  - `GLPI_BASE_URL` (ou `API_URL`)
  - `GLPI_APP_TOKEN` (ou `APP_TOKEN`)
  - `GLPI_USER_TOKEN` (ou `USER_TOKEN`)
  - `CACHE_TTL_SEC` (opcional, padrão definido no código)
  - Ajustes de desempenho (opcionais):
    - `MAX_WORKERS` → número de workers para busca concorrente em ranking de técnicos (padrão: `3`).
    - `RANGE_STEP_TICKETS` → tamanho do passo de paginação de tickets (padrão: `300`).
    - `RANGE_STEP_TICKETS_UNASSIGNED` → passo alternativo quando `incluirNaoAtribuido=true`; se ausente, aplica ajuste dinâmico com limite de `1000`.
    - `EXCLUDE_STATUS_NEW` → se `true`, exclui `STATUS_NEW (1)` no ranking de técnicos, reduzindo paginação.

Critérios de busca

- Helpers centralizados em `logic/criteria_helpers.py` montam critérios de forma pura e consistente.
- `add_date_range(inicio, fim)`: normaliza datas (`00:00:00`/`23:59:59`) e aplica `AND` corretamente.
- `add_status(status)`: adiciona filtro de status, incluindo `link='AND'` quando já há critérios prévios.
- A ordem dos critérios no array é usada para indexação (`criteria[{i}]`) pelo cliente GLPI.

Status e Constantes

- Os status e campos utilizados no dashboard estão centralizados em `backend/logic/glpi_constants.py`.
- Mapeamentos principais de status (GLPI Ticket.status):
  - `STATUS_NEW = 1` → Novo
  - `STATUS_ASSIGNED = 2` → Em atendimento
  - `STATUS_PLANNED = 3` → Planejado
  - `STATUS_PENDING = 4` → Pendente
  - `STATUS_SOLVED = 5` → Solucionado
  - `STATUS_CLOSED = 6` → Fechado
- Campos de busca relevantes:
  - `FIELD_STATUS = 12` (status)
  - `FIELD_CREATED = 15` (data de criação)
  - `FIELD_REQUESTER = 4` (solicitante)
  - `FIELD_ENTITY = 80` (entidade)
  - `FIELD_CATEGORY = 7` (categoria)

Semântica dos agregados

- `stats-gerais` (por período):
  - `novos`: tickets com `STATUS_NEW` dentro do intervalo.
  - `em_atendimento`: tickets com `STATUS_ASSIGNED` dentro do intervalo.
  - `pendentes`: tickets com `STATUS_PENDING` dentro do intervalo.

Testes

- Os testes unitários do cliente GLPI estão em `backend/tests/test_glpi_client.py`.
- Como executar:
  - `python -m unittest discover backend/tests -v`
- Cobertura principal:
  - `authenticate`: sucesso, timeout, HTTP 401/403, HTTP 500.
  - `search_paginated`: sucesso (1–2 páginas), timeout, HTTP 403, HTTP 500.
  - `get_user_names_in_batch_with_fallback`: sucesso, nomes vazios, timeout, HTTP 403/404/outros, erros de rede, dados incompletos.

Configuração de cache e entidade

- `SESSION_TTL_SEC`: TTL do cache de sessão (padrão `300`). Pode ser injetado via argumento em `authenticate(...)`.
- `GLPI_CHANGE_ENTITY`: controla troca de entidade ativa (default habilitado: `1`). Pode ser desabilitado com `0`/`false` ou via parâmetro `change_entity=False` em `authenticate(...)`.
  - `planejados`: tickets com `STATUS_PLANNED` dentro do intervalo.
  - `resolvidos`: soma de `STATUS_SOLVED` + `STATUS_CLOSED` dentro do intervalo.
  - `novos`: total com `STATUS_NEW`.
  - `em_atendimento`: total com `STATUS_ASSIGNED`.
  - `nao_solucionados`: soma de `STATUS_ASSIGNED` + `STATUS_PENDING` (em atendimento ou pendente).
  - `planejados`: total com `STATUS_PLANNED`.
  - `solucionados`: total com `STATUS_SOLVED`.
  - `fechados`: total com `STATUS_CLOSED`.
  - `resolvidos`: soma de `STATUS_SOLVED` + `STATUS_CLOSED`.

Observações de contrato

- `resolvidos` agrega estados finais (`solucionado` e `fechado`), mantendo coerência visual.
- `nao_solucionados` representa o trabalho em curso ou bloqueado (atribuição + pendência), sem incluir `novo`.
- Comentários e implementações foram alinhados para refletir corretamente `planejados = status 3`.