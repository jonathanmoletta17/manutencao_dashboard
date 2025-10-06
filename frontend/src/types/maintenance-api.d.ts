// Tipos específicos para o Dashboard de Manutenção

export interface MaintenanceGeneralStats {
  novos: number;
  pendentes: number;
  planejados: number;
  resolvidos: number;
}

export interface EntityRankingItem {
  entity_name: string;
  ticket_count: number;
}

export interface CategoryRankingItem {
  category_name: string;
  ticket_count: number;
}

export interface MaintenanceNewTicketItem {
  id: number;
  titulo: string;
  solicitante: string;
  data: string;
  entidade: string;
}