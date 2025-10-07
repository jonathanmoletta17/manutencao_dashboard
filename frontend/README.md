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

Endpoints consumidos pelo dashboard:
- `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD` — cinco métricas por período: Novos, Em atendimento, Pendentes, Planejados, Resolvidos.
- `GET /api/v1/manutencao/ranking-entidades?inicio&fim&top` — ranking por entidade no período.
- `GET /api/v1/manutencao/ranking-categorias?inicio&fim&top` — ranking por categoria no período.
- `GET /api/v1/manutencao/tickets-novos?limit` — últimos tickets criados.

Observação:
- O endpoint `status-totais` não é consumido pelo dashboard; “Em atendimento” agora vem de `stats-gerais` com filtro de datas, garantindo consistência entre as cinco métricas.