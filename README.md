# App Manutenção (Plano de Extração)

Objetivo: separar completamente o dashboard de Manutenção do app DTIC, evitando definições misturadas.

Escopo a ser extraído do projeto atual:

Backend Manutenção:
- `backend/api/maintenance_router.py`
- `backend/logic/maintenance_logic.py`
- `backend/schemas_maintenance.py`
- Dependências compartilhadas necessárias: `backend/glpi_client.py`, `backend/logic/criteria_helpers.py`, `backend/utils/cache.py`, `backend/utils/logging_setup.py`
- Constantes: atualmente em `backend/logic/glpi_constants.py` (há mistura). No app separado, criar uma versão específica `glpi_constants_manutencao.py` apenas com campos/status usados pela Manutenção.

Frontend Manutenção:
- `frontend/src/MaintenanceDashboard.tsx`
- `frontend/src/services/maintenance-api.ts` (se existir; senão criar a partir das chamadas usadas no dashboard)
- `frontend/src/types/maintenance-api.d.ts`
- `frontend/src/components/DateRangePicker.tsx` (se usada pelo dashboard; pode ser movida ou ficar em `packages/ui` compartilhado)
- Rotas: remover a rota de Manutenção do `frontend/src/main.tsx` do DTIC e criar `main.tsx` próprio para Manutenção.

Arquitetura Proposta (Monorepo):
- `apps/manutencao/backend/` (FastAPI com apenas o router de Manutenção)
- `apps/manutencao/frontend/` (Vite React com apenas as telas de Manutenção)
- `packages/shared/` (opcional): `glpi_client`, `criteria_helpers`, `cache`, componentes UI genéricos; evite colocar constantes específicas aqui.

Passos da Extração:
1. Copiar arquivos listados acima para `apps/manutencao/backend/` e `apps/manutencao/frontend/`.
2. Criar `apps/manutencao/backend/main.py` incluindo somente `maintenance_router` e carregando `.env` próprio.
3. Criar `apps/manutencao/frontend/main.tsx` com rota raiz para `/manutencao`.
4. Duplicar `backend/.env.example` para `apps/manutencao/backend/.env.example` com apenas variáveis necessárias e tokens corretos.
5. Ajustar constantes: criar `glpi_constants_manutencao.py` e referenciar no `maintenance_logic.py`.
6. Remover referências de Manutenção do app DTIC (rota em `frontend/src/main.tsx` e quaisquer imports).

Execução Independente:
- Backend Manutenção: `uvicorn main:app --reload --port 8010` no diretório `apps/manutencao/backend/`.
- Frontend Manutenção: `npm run dev` com `vite.config.ts` próprio no diretório `apps/manutencao/frontend/` (porta, por exemplo, `5002`).

Observações:
- Manter caches e clientes GLPI isolados para cada app, ou mover para `packages/shared` com inicialização por app.
- Logs devem ser segregados por app para facilitar diagnóstico.