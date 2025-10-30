# Revisão e Plano de Melhorias — Frontend

Objetivo: simplificar, tornar consistente e manter a funcionalidade atual do dashboard, reduzindo duplicações e estilos ad-hoc.

## Remoções e Simplificações
- Remover ou escopar `overflow-hotfix.css` (evita `overflow-y: hidden` global em `html, body`). Aplicar scroll apenas em contêineres específicos.
- Consolidar estilos de scrollbar: criar uma classe utilitária única (ex.: `.scroll-thin-blue`) em `dtic-index.css` e reutilizar nos módulos que rolam.
- Usar chaves estáveis em listas (ex.: `entity_name`, `tecnico`) em vez de índices (`idx`).
- Unificar formatação de entidades em um helper único (ex.: `formatEntityLabel`) em substituição ao uso combinado de `stripParentPrefix` e `abbreviateEntityName` nos componentes.
- Mover normalização de strings usada em `TechnicianRanking` para `utils/strings.ts` e reutilizar.
- Remover comentários legados (ex.: referências a “Top N”) e alinhar documentação mínima ao estado atual.

## Inconsistências a Corrigir
- Evitar cores hardcoded (`#5A9BD4`) e gradientes locais; preferir tokens de tema (`text-primary`, `bg-primary`) e variantes de UI (`badgeVariants`, `buttonVariants`).
- Padronizar bordas: decidir se `Card` tem borda por padrão; remover bordas manuais redundantes em filhos para consistência.
- Unificar textos de estado: “Carregando…” vs “Ranking indisponível”; manter copy consistente e considerar skeletons leves em áreas de carregamento prolongado.
- Adicionar variantes semânticas no `Badge` para top 3 (`gold`, `silver`, `bronze`) e substituir classes inline em `TechnicianRanking`.
- Definir padrão para uso de `error` em hooks: ou exibir indicação discreta na UI ou remover do retorno se não for utilizado.

## Melhorias de Eficiência
- Centralizar ou coordenar polling: `useDashboardData` e `useTechnicianRanking` usam o mesmo `VITE_REALTIME_POLL_INTERVAL_SEC`; avaliar um scheduler único ou intervalos ajustados por dado.
- Introduzir `AbortController` com timeout leve (ex.: 10–12s) em `fetchFromAPI` para evitar pendências prolongadas no navegador.
- Consolidar persistência de `dateRange` no URL apenas no “Aplicar”; manter debounce apenas para carga de dados.
- Tornar `fetchMaintenanceNewTickets(8)` configurável via env (`VITE_NEW_TICKETS_LIMIT`) e centralizar leitura em `src/config.ts`.
- Considerar memoização leve para normalizações de strings apenas se houver custo real (guiado por profiling).

## Coesão de Projeto
- Criar `src/config.ts` para leitura de variáveis de ambiente (poll interval, limites, retry/TTL, base URL) com defaults consistentes; reutilizar em hooks e serviços.
- Documentar util classes aprovadas em `dtic-index.css` (scroll, gradientes, cores) e remover variações ad-hoc nos componentes.
- Padronizar terminologia: copy de estados, capitalização de “Manutenção/Conservação”, uso de labels no dashboard.
- Manter abordagem de “um hook por tipo de dado” retornando `{ data|null, refresh, error|null }` para evitar acoplamentos.
- Avaliar a criação de um pequeno guia `docs/frontend-style.md` com convenções de copy, cores, e UI.

## Ações Prioritárias
1. Escopar/remover `overflow-hotfix.css` e criar a util de scrollbar.
2. Substituir chaves por valores estáveis nas listas.
3. Padronizar cores via tema e variantes (`badge`, `button`, `card`).
4. Consolidar persistência de `dateRange` (apenas no “Aplicar”).
5. Introduzir `src/config.ts` e migrar leituras de env (poll/retry/TTL/limits).

## Ajustes Opcionais
- Adicionar timeout com `AbortController` em `fetchFromAPI`.
- Introduzir skeletons leves em áreas de carregamento prolongado (ranking de técnicos).
- Expor `formatEntityLabel` e simplificar uso de helpers nos componentes.
- Variantes `gold/silver/bronze` no `Badge` para top 3.

## Notas de Configuração
- Hook `useTechnicianRanking` aceita variáveis: `VITE_TECH_RANK_RETRY_ATTEMPTS`, `VITE_TECH_RANK_RETRY_MS`, `VITE_TECH_RANK_STALE_TTL_MS` (documentadas em `.env.example`).
- Considerar `VITE_NEW_TICKETS_LIMIT` e consolidar `VITE_REALTIME_POLL_INTERVAL_SEC` em `src/config.ts`.