Manutenção Backend

Endpoints

- `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - Estatísticas gerais por período, com filtro de datas.
  - Campos: Novos (1), Em atendimento (2), Pendentes (4), Planejados (3), Resolvidos (5+6).
  - Usa cache com TTL (`CACHE_TTL_SEC`).

- `GET /api/v1/manutencao/status-totais`
  - Totais gerais por status, sem filtro de datas.
  - Campos: Novos (1), Em atendimento (2), Não solucionados (2+4), Planejados (3), Solucionados (5), Fechados (6), Resolvidos (5+6).
  - Usa cache com TTL (`CACHE_TTL_SEC`).

- `GET /api/v1/manutencao/top-atribuicao-entidades?top=10`
  - Ranking global por entidade com contagem de tickets.
  - Implementa busca de IDs brutos (`display_type=2`) e mapeamento para nomes completos.

- `GET /api/v1/manutencao/top-atribuicao-categorias?top=10`
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