# Execução e Operação do Manutenção Dashboard

Este documento descreve, de forma objetiva, como configurar, instalar e executar o projeto, além de orientações para evitar implementações desnecessárias e complexidade de código.

## Visão Geral
- Backend: FastAPI (Uvicorn) servindo dados da GLPI.
- Frontend: Vite/React, empacotado para produção.
- Container único: Nginx serve o frontend em `/dashboard/` e faz proxy de `/api/` para o backend no mesmo container.

## Pré-requisitos
- Docker Desktop instalado e em execução.
- (Opcional) Node.js LTS e `npm` para desenvolvimento do frontend.

## Configuração
- Copie `backend/.env.example` para `backend/.env` e preencha as variáveis (credenciais/endpoints GLPI).
- O frontend, em produção, é servido sob `/dashboard/`. Por isso a base de build do Vite está configurada para `/dashboard/`.

## Executar (Container Único – recomendado)
1. Subir o serviço:
   - `docker compose -f docker-compose.single.yml up -d`
   - Para reconstruir ao aplicar mudanças: `docker compose -f docker-compose.single.yml up --build -d`
2. Validar saúde:
   - `http://localhost:8000/health` → deve retornar `{"status":"ok"}`.
3. Acessar o dashboard:
   - `http://localhost:8000/dashboard/`
4. Parar serviço:
   - `docker compose -f docker-compose.single.yml down`
5. Limpar órfãos (se necessário):
   - `docker compose -f docker-compose.single.yml up -d --remove-orphans`

## Executar (Desenvolvimento – serviços separados)
1. Backend:
   - `docker compose -f docker-compose.dev.yml up --build -d backend`
   - Health: `http://127.0.0.1:8010/health`
2. Frontend:
   - `cd frontend && npm ci && npm run dev`
   - Acessar: `http://localhost:5002/`
   - Proxy local de `/api/v1` aponta para `http://127.0.0.1:8010`.

## Endpoints principais
- Stats gerais: `GET /api/v1/manutencao/stats-gerais?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
- Ranking entidades: `GET /api/v1/manutencao/ranking-entidades?inicio=YYYY-MM-DD&fim=YYYY-MM-DD&top=5`
- Ranking categorias: `GET /api/v1/manutencao/ranking-categorias?inicio=YYYY-MM-DD&fim=YYYY-MM-DD&top=5`
- Ranking técnicos: `GET /api/v1/manutencao/ranking-tecnicos?inicio=YYYY-MM-DD&fim=YYYY-MM-DD&top=5`

## Boas práticas (evitar complexidade desnecessária)
- Preferir o container único para operação: reduz dependências e pontos de falha.
- Manter o Vite com base `/dashboard/` apenas no build (produção) e `/` no dev – já configurado no `vite.config.ts`.
- Evitar duplicar serviços e portar múltiplos Nginx: o `frontend/nginx.single.conf` já cobre SPA e proxy.
- Não introduzir frameworks adicionais de estado/roteamento sem necessidade; o dashboard é uma SPA simples.

## Solução de problemas
- Porta 8000 ocupada:
  - Pare quem está usando: `docker stop dtic-dashboard-backend`
  - Suba novamente: `docker compose -f docker-compose.single.yml up -d`
- `/dashboard` sem barra final:
  - Existe redirecionamento para `/dashboard/` no Nginx (`location = /dashboard { return 301 /dashboard/; }`). Use a URL com barra.
- Assets não carregam no dashboard:
  - Garanta rebuild após ajustes de frontend: `docker compose -f docker-compose.single.yml up --build -d`.
  - O `vite.config.ts` define `base: '/dashboard/'` quando `command === 'build'`.
- “Failed to fetch” no dev:
  - Confirme que o backend está em `http://127.0.0.1:8010` e que o proxy do Vite está ativo.

## Arquivos relevantes
- `Dockerfile.single`: build do frontend e runtime backend+Nginx.
- `frontend/nginx.single.conf`: Nginx servindo `/dashboard/` e proxy de `/api`.
- `start.sh`: inicializa Uvicorn e Nginx no container.
- `frontend/vite.config.ts`: base `/dashboard/` no build e proxy dev de `/api/v1`.
- `docker-compose.single.yml`: serviço único publicado em `8000`.

---
Mantemos foco em simplicidade e clareza: um único container que entrega UI e API, com rotas estáveis e sem sobre-engenharia.