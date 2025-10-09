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

Endpoints consumidos pelo dashboard:
- `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD` — cinco métricas por período: Novos, Em atendimento, Pendentes, Planejados, Resolvidos.
- `GET /api/v1/manutencao/ranking-entidades?inicio&fim&top` — ranking por entidade no período.
- `GET /api/v1/manutencao/ranking-categorias?inicio&fim&top` — ranking por categoria no período.
- `GET /api/v1/manutencao/tickets-novos?limit` — últimos tickets criados.

Observação:
- O endpoint `status-totais` não é consumido pelo dashboard; “Em atendimento” agora vem de `stats-gerais` com filtro de datas, garantindo consistência entre as cinco métricas.

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
- `useDashboardData`: centraliza carregamento inicial, atualização quando `dateRange/topN` mudam e polling interno configurável via `VITE_REALTIME_POLL_INTERVAL_SEC`. O componente não cria intervalos de dados.
- Parâmetros de URL: `replaceUrlParams` persiste `dateRange` e `topN`. A ação “Aplicar período” usa os estados atuais, evitando refs e closures obsoletas.

## Notas de endpoints e ranking

- Top N padrão: o dashboard utiliza `top = 10` como valor padrão para rankings.
- CategoryRanking: ao buscar categorias, solicitamos mais itens para suportar agrupamento por área sem reconsulta. A regra é `max(top * 3, 15)`.
- Tickets novos: o endpoint `tickets-novos` recebe apenas `limit` e não é afetado por `inicio/fim` do painel; a filtragem temporal, quando aplicável, é responsabilidade do backend.
- Ranking de Técnicos: não há cache global no frontend. Se o backend responder `404` ou `501`, consideramos como ausência de dados e retornamos lista vazia. Demais erros são propagados para tratamento no hook/componente. (Semântica sujeita à confirmação com o backend.)