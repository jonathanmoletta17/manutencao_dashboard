// Tipos específicos para o Dashboard de Manutenção
// Mantêm correspondência direta com os modelos Pydantic do backend.

export interface MaintenanceGeneralStats {
  /** Novos (status 1) no período selecionado */
  novos: number;
  /** Em atendimento (status 2 - Atribuído/Em progresso) no período */
  em_atendimento: number;
  /** Pendentes (status 4) no período */
  pendentes: number;
  /** Planejados (status 3) no período */
  planejados: number;
  /** Resolvidos (status 5 + 6) no período */
  resolvidos: number;
}

export interface EntityRankingItem {
  /** Nome completo da entidade (ou label resolvido) */
  entity_name: string;
  /** Total de tickets atribuídos à entidade */
  ticket_count: number;
}

export interface CategoryRankingItem {
  /** Nome completo da categoria (ou label resolvido) */
  category_name: string;
  /** Total de tickets atribuídos à categoria */
  ticket_count: number;
}

/** Corresponde ao schema de ranking de técnicos (nome e total de tickets). */
export interface TechnicianRankingItem {
  /** Nome do técnico */
  tecnico: string;
  /** Total de tickets atribuídos ao técnico */
  tickets: number;
}

export interface MaintenanceNewTicketItem {
  /** ID do ticket */
  id: number;
  /** Título do ticket */
  titulo: string;
  /** Nome do solicitante (resolvido quando possível) */
  solicitante: string;
  /** Data de criação formatada (dd/MM/yyyy HH:mm) */
  data: string;
  /** Nome da entidade associada ao ticket */
  entidade: string;
}