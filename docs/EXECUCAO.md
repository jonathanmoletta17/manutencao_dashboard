# Execução e Operação do Manutenção Dashboard

Este documento descreve como configurar e executar o projeto com FastAPI servindo a UI estática diretamente, sem Nginx, padronizando a porta 8000.

## Visão Geral
- Backend: FastAPI (Uvicorn) servindo dados da GLPI e arquivos estáticos.
- Frontend: Vite/React, empacotado e servido em `/dashboard/` pelo próprio FastAPI.
- Container único: um serviço expõe `8000` para API e UI.

## Pré-requisitos
- Docker Desktop instalado e em execução.
- (Opcional) Node.js LTS e `npm` para desenvolvimento do frontend.

## Configuração
- Copie `backend/.env.example` para `backend/.env` e preencha as variáveis (credenciais/endpoints GLPI).
- O Vite já define a base em `/dashboard/` no `vite.config.ts` para o build de produção.

## Executar (Produção simples com Docker Compose)
1. Build sem cache:
   - `docker compose build --no-cache --progress=plain`
2. Subir o serviço:
   - `docker compose up -d`
3. Validar saúde:
   - `http://localhost:8000/health` → deve retornar `{"status":"ok"}`.
4. Acessar o dashboard:
   - `http://localhost:8000/dashboard/`
5. Parar serviço:
   - `docker compose down`

## Desenvolvimento (opcional)
- Executar `npm run dev` no diretório `frontend/` para hot-reload da UI (porta 5002). O backend pode ser executado com Uvicorn localmente em outra porta. Em produção, a UI é servida por FastAPI.

## Endpoints principais
- Saúde: `GET /health`
- UI: `GET /dashboard/`
- API de manutenção (exemplos):
  - `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - `GET /api/v1/manutencao/ranking-entidades?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - `GET /api/v1/manutencao/ranking-categorias?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - `GET /api/v1/manutencao/ranking-tecnicos?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`

## Boas práticas
- Manter a base do Vite apenas no `vite.config.ts` (sem passar `--base` ao build).
- Evitar adicionar Nginx quando FastAPI já serve estáticos de forma simples.
- Usar a porta única `8000` para expor API e UI.

## Solução de problemas
- Porta 8000 ocupada:
  - Pare o serviço que usa a porta ou execute `docker compose down` antes de subir novamente.
- Assets não carregam no dashboard:
  - Refaça o build: `docker compose build --no-cache --progress=plain` e `docker compose up -d`.
- Chamadas tentando `/@vite/client` em produção:
  - Isso só ocorre no dev; valide que está usando o bundle de produção (sem `vite dev`).

## Arquivos relevantes
- `docker-compose.yml`: serviço único `manutencao-backend` publicado em `8000`.
- `Dockerfile`: build do frontend e runtime do backend servindo estáticos.
- `backend/main.py`: monta `StaticFiles("/dashboard")` e redireciona `/` para `/dashboard/`.
- `frontend/vite.config.ts`: base `/dashboard/` no build e proxy dev.

---
Operação simples: um container, uma porta, FastAPI entrega UI e API sem Nginx.