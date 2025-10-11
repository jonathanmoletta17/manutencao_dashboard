# Manutenção Dashboard — Execução Simples

Projeto FastAPI servindo a UI estática de Vite/React diretamente, sem Nginx, padronizando a porta `8000`.

## Como rodar
- Build:
  - `docker compose build --no-cache --progress=plain`
- Subir:
  - `docker compose up -d`
- Validar saúde:
  - `http://localhost:8000/health` → retorna `{"status":"ok"}`
- Abrir UI:
  - `http://localhost:8000/dashboard/`
- Parar:
  - `docker compose down`

## Detalhes
- Serviço/container: `manutencao-backend` mapeado em `8000:8000`.
- Backend monta `StaticFiles` em `/dashboard` e redireciona `/` → `/dashboard/`.
- `vite.config.ts` define base `/dashboard/` no build; não usamos `--base` no Dockerfile.

## Endpoints principais
- `GET /health`
- `GET /dashboard/`
- `GET /api/v1/manutencao/...` (demais rotas de API)

## Desenvolvimento (opcional)
- `frontend`: `npm run dev` (porta 5002) para hot-reload. Em produção, a UI é servida pelo FastAPI.