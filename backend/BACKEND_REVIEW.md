# Revisão Backend — Dashboard de Manutenção

Este documento consolida sugestões de melhorias para o backend, focando em simplificação, consistência, eficiência e coesão do projeto, preservando a funcionalidade atual. As recomendações são baseadas na análise dos módulos `api/`, `logic/`, `utils/` e `glpi_client.py`.

## Remoções e Simplificações
- Unificar nomes de variáveis de ambiente para GLPI:
  - Padronizar uso de `API_URL` como base (substituir checagens mistas com `GLPI_BASE_URL`).
  - Padronizar `APP_TOKEN` e `USER_TOKEN` (remover alias `GLPI_APP_TOKEN` e `GLPI_USER_TOKEN` quando possível, mantendo backward-compat por um ciclo).
- Centralizar timeouts e `range_step` em um único ponto de configuração:
  - Hoje há `timeout=(1, 2.5)` espalhado em `glpi_client.py` e `utils/user_names.py`.
  - Criar `config.py` com `GLPI_TIMEOUT_CONN_MS`, `GLPI_TIMEOUT_READ_MS`, `GLPI_RANGE_STEP_TICKETS`, e ler nesses pontos.
- Reduzir duplicidade de montagem de parâmetros:
  - Preferir `search_paginated_iter` em lógicas que só contam ou acumulam (ex.: `maintenance_stats_logic.py`) para evitar alocação de listas grandes.
- Padronizar tratamento de entity display:
  - Confirmar que o uso consistente de `display_type='2'` e `is_recursive='1'` está aplicado e movê-los para constantes/configuração compartilhada.
- Consolidar chaves de cache:
  - Documentar padrão de construção de chaves (`prefixo_função_parametros_normalizados`) e aplicar nos três roteadores para evitar colisões e inconsistências.

## Inconsistências Identificadas
- Mapeamento de erros nas rotas:
  - `ranking-tecnicos` devolve `[]` em alguns erros (auth/network/search) quando não há `stale`, enquanto outras rotas retornam `HTTP 502`.
  - Sugerir resposta consistente: usar `stale` quando disponível; caso contrário, diferenciar HTTP conforme tipo de erro.
- Variáveis de ambiente misturadas:
  - Alguns endpoints usam `API_URL` ou `GLPI_BASE_URL` de forma alternada. Padronizar.
- Cache TTL único e global:
  - `utils/cache.py` tem `DEFAULT_TTL` global (por env). Considerar TTLs distintos por recurso (ex.: rankings vs. métricas gerais) via `cache.set(key, value, ttl=...)`.
- Critérios e parâmetros:
  - `maintenance_stats_logic` usa `search_paginated` (lista). Outras partes usam `search_paginated_iter` (gerador). Padronizar.
- Métricas/logs:
  - Uso de `metrics.increment` e `record_timing` com `logger.info`. Considerar `DEBUG` para métricas de alta frequência.

## Melhorias de Eficiência
- Timeout configurável e retries leves com backoff:
  - Em `glpi_client.authenticate` e buscas, habilitar retries simples para `GLPINetworkError` (ex.: 2 tentativas com backoff exponencial). Evitar retries em `401/403`.
  - Centralizar timeouts via config e permitir override por env.
- Streaming de resultados e early-stop:
  - Priorizar `search_paginated_iter` em contagens e agregações para reduzir latência e memória.
- Cache com `stale` mais explícito:
  - Já existe `get_stale`. Documentar o fallback e usar TTLs por endpoint.
- Concorrência controlada no `utils/user_names.py`:
  - `max_workers` via `GLPI_NAME_WORKERS` com clamp (ex.: `min(max(1, env), 16)`).
  - Observação: mantemos timeouts agressivos, mas agora configuráveis.
- Reduzir duplicidade de chamadas por entidade/categoria:
  - Resolver nomes com cache local (já feito) e evitar múltiplos GETs quando possível.

## Coesão do Projeto
- Criar `backend/config.py` centralizando:
  - `API_URL`, `APP_TOKEN`, `USER_TOKEN`.
  - `SESSION_TTL_SEC`, `GLPI_CHANGE_ENTITY`.
  - Timeouts (`GLPI_TIMEOUT_CONN_MS`, `GLPI_TIMEOUT_READ_MS`).
  - Range step (`GLPI_RANGE_STEP_TICKETS`).
  - Limites (ex.: `TECH_RANK_TOP_LIMIT`, clamp de `GLPI_NAME_WORKERS`).
- Padronizar respostas de erro nas rotas:
  - `GLPINetworkError(timeout=True)` -> `HTTP 504` (Timeout do gateway).
  - `GLPINetworkError` genérico -> `HTTP 502`.
  - `GLPIAuthError` -> `HTTP 502` (upstream auth failure) ou `401` interno apenas se o backend exigir auth própria.
  - `GLPISearchError` -> `HTTP 502`.
  - `Exception` -> `HTTP 500`.
  - Sempre tentar `stale` do cache antes de erro.
- Terminologia e nomes de chaves:
  - Usar língua consistente (`manutencao_*`) e incluir incluir/excluir em português nas chaves (`inclui`/`nao_inclui`).

## Prioridades (Baixo esforço, alto ganho)
- Padronizar retorno de erro em `ranking-tecnicos` para alinhar com demais endpoints.
- Extrair `config.py` e mover timeouts/range_step/env reads.
- Aplicar `search_paginated_iter` nas contagens de `maintenance_stats_logic`.
- Ajustar construção de chaves de cache e adicionar TTLs por endpoint.
- Unificar leitura de `API_URL`/tokens via `config.py`.

## Ajustes Opcionais
- Implementar retries com `requests` simples (até 2) para `GET` mais críticos, com backoff (ex.: 200ms, 600ms).
- Adicionar `AbortController`-equivalente no Python: usar `requests.Session` com `adapter` e `max_retries` para falhas de conexão específicas.
- Expor métrica de hit/miss do cache via endpoint interno de diagnóstico (apenas dev/ops).
- Mover logs de métricas para `DEBUG` e agregar contadores por janela.
- Adicionar testes unitários para `utils/cache` e `config` (TTL por recurso, stale fallback, clamps de workers/timeouts).

## Configuração e Variáveis de Ambiente
- Propostas de variáveis:
  - `API_URL`: URL base da API GLPI (`.../apirest.php`).
  - `APP_TOKEN`, `USER_TOKEN`: tokens GLPI.
  - `SESSION_TTL_SEC`: TTL do cache de sessão (default 300s).
  - `GLPI_CHANGE_ENTITY`: `1`/`0` para alternar entidade ativa (default `1`).
  - `GLPI_TIMEOUT_CONN_MS`: timeout de conexão em ms (default 1000).
  - `GLPI_TIMEOUT_READ_MS`: timeout de leitura em ms (default 2500).
  - `GLPI_RANGE_STEP_TICKETS`: tamanho do `range` na paginação (default 1000).
  - `TECH_RANK_TOP_LIMIT`: limite máximo de TOP no ranking de técnicos (default 20).
  - `GLPI_NAME_WORKERS`: número de workers para nomes (default 8, clamp <= 16).
- Documentar deprecados/aliases por um ciclo para migração suave (`GLPI_BASE_URL`, `GLPI_APP_TOKEN`, `GLPI_USER_TOKEN`).

## Observações por Arquivo
- `backend/glpi_client.py`:
  - Timeouts fixos `(1, 2.5)` nos `requests.get/post`. Mover para `config` e considerar `requests.Session` com `HTTPAdapter` para retries controlados.
  - Cache de sessão com TTL e lock: robusto; sugerir invalidação imediata em `GLPIAuthError` (resetar `_SESSION_HEADERS`).
  - `search_paginated` e `search_paginated_iter`: manter ambos, mas preferir `iter` em agregações grandes.
- `backend/api/maintenance_ranking_router.py`:
  - Fallback `stale` aplicado; inconsistência nos códigos de erro vs. `ranking-tecnicos`. Uniformizar.
  - Padronizar leitura de env via `config`.
- `backend/api/maintenance_stats_router.py` e `maintenance_tickets_router.py`:
  - Resposta 502 única para network/search; diferenciar timeout com 504 quando disponível.
  - Considerar `stale` para métricas/tickets quando apropriado.
- `backend/logic/*`:
  - `maintenance_stats_logic.py`: substituir `search_paginated` por `search_paginated_iter` com early-stop.
  - `maintenance_ranking_logic.py`: confirmar `expand_dropdowns='0'` e parâmetros consistentes.
- `backend/utils/cache.py`:
  - Suporte atual a `stale`. Adicionar TTL por recurso nos `set` dos roteadores.
- `backend/utils/user_names.py`:
  - Timeouts e `max_workers` parametrizáveis; adicionar clamp e documentar.
  - Métricas de alta frequência: reduzir nível de log.
- `backend/utils/metrics.py`:
  - Logging `INFO`; considerar `DEBUG` e (futuramente) integração com coletor externo.

## Plano de Ação Sugerido (em pequenos PRs)
1) Criar `backend/config.py` e migrar leituras de env/timeouts/limits.
2) Uniformizar erros e `stale` nos roteadores, diferenciando `timeout` com 504.
3) Aplicar `search_paginated_iter` onde couber e ajustar TTLs por endpoint.
4) Revisar `glpi_client` para invalidar sessão em `GLPIAuthError` e configurar retries leves.
5) Ajustar concorrência e logs em `utils/user_names.py` e `utils/metrics.py`.

Estas mudanças mantêm a simplicidade atual e aumentam previsibilidade, desempenho e consistência do serviço.