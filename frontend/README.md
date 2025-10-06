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