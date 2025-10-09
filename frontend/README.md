# Frontend Manutenção

Frontend Vite/React contendo apenas telas e serviços do dashboard de Manutenção.

Conteúdo esperado:
- `MaintenanceDashboard.tsx`
- `services/maintenance-api.ts`
- `types/maintenance-api.d.ts`
- `components/DateRangePicker.tsx` (opcional, ou mover para `packages/ui` compartilhado)
- `main.tsx` com rota raiz `/manutencao`
- `vite.config.ts` próprio (proxy para backend `http://127.0.0.1:8010`)

Execução:
- `npm install`
- `npm run dev` (porta sugerida: `5002`)

Config:
- `.env`/`.env.production` com `VITE_API_BASE_URL` apontando para o backend de Manutenção.
- Opcional: `VITE_API_VERSION_PREFIX` para parametrizar o prefixo da API (padrão: `/api/v1`).

Parâmetros de URL (persistência)
- `inicio`, `fim`: intervalo de datas (YYYY-MM-DD), lidos e persistidos pelo utilitário `src/services/url_params.ts`.
- `cat`: modo de exibição do ranking de categorias.
  - `cat=orig` → modo original (A > B > C)
  - `cat=agg` → modo agregado por segundo nível (A > B)
  - O `MaintenanceDashboard` inicializa o estado a partir da URL e atualiza com `replaceCategoryModeInUrl`.

Endpoints consumidos pelo dashboard:
- `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD` — cinco métricas por período: Novos, Em atendimento, Pendentes, Planejados, Resolvidos.
- `GET /api/v1/manutencao/ranking-entidades?inicio&fim` — ranking por entidade no período (lista completa).
- `GET /api/v1/manutencao/ranking-categorias?inicio&fim` — ranking por categoria no período (lista completa).
- `GET /api/v1/manutencao/tickets-novos?limit` — últimos tickets criados.

Observação:
 - O dashboard utiliza apenas `stats-gerais` com filtro de datas para compor as métricas exibidas, incluindo “Em atendimento”.

## Contratos de dados

- As interfaces em `src/types/maintenance-api.d.ts` espelham os modelos Pydantic do backend e mantêm campos em `snake_case`.
- Formatos e tipos:
  - Datas em `MaintenanceNewTicketItem.data`: string no formato `dd/MM/yyyy HH:mm`.
  - Contagens: números inteiros (`int` no backend, `number` no frontend).
- As descrições de campos foram alinhadas entre backend (via `Field(description=...)`) e frontend (comentários JSDoc), facilitando navegação e validação.

## Geração automática de tipos (avaliação)

- Opção A (OpenAPI): usar `openapi-typescript` para gerar `src/types/openapi.d.ts` a partir de `http://127.0.0.1:8010/openapi.json`.
- Opção B (Pydantic direto): usar `datamodel-code-generator` ou `pydantic2ts` para gerar tipos a partir dos modelos Python.
- Recomenda-se a abordagem OpenAPI por cobrir todos os contratos (inclui rotas e schemas) e manter-se estável com FastAPI.

## Configuração do carrossel de categorias

O carrossel que alterna entre as macro áreas "Manutenção" e "Conservação" lê o intervalo de rotação via variáveis de ambiente do Vite:

- `VITE_CATEGORY_CAROUSEL_INTERVAL_MS`: intervalo em milissegundos.
- `VITE_CATEGORY_CAROUSEL_INTERVAL_SEC`: intervalo em segundos.

Regras de precedência e padrão:
- Se `VITE_CATEGORY_CAROUSEL_INTERVAL_MS` estiver definido, ele é usado diretamente.
- Caso contrário, se `VITE_CATEGORY_CAROUSEL_INTERVAL_SEC` estiver definido, ele é convertido para ms e usado.
- Se nenhum estiver definido, o padrão é `15000` ms (15 segundos).

Exemplos de `.env`:
```
# usar 12s (em segundos)
VITE_CATEGORY_CAROUSEL_INTERVAL_SEC=12

# ou usar 18000 ms (18s, tem precedência sobre SEC)
VITE_CATEGORY_CAROUSEL_INTERVAL_MS=18000
```

Observações operacionais:
- Interações manuais (avançar/retroceder/ir para indicador) pausam temporariamente a rotação automática por 20s para melhorar a leitura.
- Esses comportamentos são implementados pelo hook `useCarousel` utilizado no `MaintenanceDashboard`.

## Estado derivado e relógio

- `useClock`: o `MaintenanceDashboard` usa o hook `useClock` para atualizar o horário exibido a cada segundo, isolando o `setInterval` do componente principal.
- Estado derivado: listas como `manCategories` e `consCategories` são derivadas exclusivamente de `categoryRanking` via `useCategoryGrouping`. Evite duplicar estado; derive sempre de uma fonte única.
- `useDashboardData`: centraliza carregamento inicial, atualização quando `dateRange` muda e polling interno configurável via `VITE_REALTIME_POLL_INTERVAL_SEC`. Inclui debounce leve ao mudar datas.
- Parâmetros de URL: `replaceUrlParams` persiste apenas `dateRange`.

## Notas de endpoints e ranking

- Rankings sem limite: o dashboard solicita listas completas dos rankings, sem parâmetro `top`.
- CategoryRanking: agrupamento por área usa todos os itens retornados pelo backend.
- Tickets novos: o endpoint `tickets-novos` recebe apenas `limit` e não é afetado por `inicio/fim` do painel; a filtragem temporal, quando aplicável, é responsabilidade do backend.
- Ranking de Técnicos: não há cache global no frontend. Se o backend responder `404` ou `501`, consideramos como ausência de dados e retornamos lista vazia. Demais erros são propagados para tratamento no hook/componente. (Semântica sujeita à confirmação com o backend.)

## Limpezas realizadas

- Removido `src/components/TopNSelect.tsx` por não ser utilizado no `MaintenanceDashboard` (o dashboard exibe todos os itens dos rankings).
- Padronizada a leitura/persistência do modo de categorias via `cat=orig|agg` na URL.