import type {
  MaintenanceGeneralStats,
  MaintenanceStatusTotals,
  EntityRankingItem,
  CategoryRankingItem,
  MaintenanceNewTicketItem,
} from '../types/maintenance-api.d';

// Prefixo da API de manutenção
// Fallback absoluto para backend local se variável não estiver definida
const API_BASE_URL = (import.meta as any)?.env?.VITE_API_BASE_URL ?? 'http://127.0.0.1:8010/api/v1';

/**
 * Função genérica para buscar dados da API de Manutenção
 */
async function fetchFromAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: `Erro de rede: ${response.statusText} ao acessar o endpoint ${endpoint}`,
    }));
    throw new Error(errorData.detail || 'Ocorreu um erro desconhecido na API.');
  }

  return response.json();
}

// Endpoints específicos para Manutenção

export const fetchMaintenanceGeneralStats = (inicio?: string, fim?: string) => {
  const qs = inicio && fim ? `?inicio=${encodeURIComponent(inicio)}&fim=${encodeURIComponent(fim)}` : '';
  return fetchFromAPI<MaintenanceGeneralStats>(`/manutencao/stats-gerais${qs}`);
};

export const fetchMaintenanceStatusTotals = () => {
  return fetchFromAPI<MaintenanceStatusTotals>(`/manutencao/status-totais`);
};

export const fetchEntityRanking = (inicio?: string, fim?: string, top: number = 10) => {
  const qs = inicio && fim ? `?inicio=${encodeURIComponent(inicio)}&fim=${encodeURIComponent(fim)}&top=${top}` : '';
  return fetchFromAPI<EntityRankingItem[]>(`/manutencao/ranking-entidades${qs}`);
};

export const fetchCategoryRanking = (inicio?: string, fim?: string, top: number = 10) => {
  const qs = inicio && fim ? `?inicio=${encodeURIComponent(inicio)}&fim=${encodeURIComponent(fim)}&top=${top}` : '';
  return fetchFromAPI<CategoryRankingItem[]>(`/manutencao/ranking-categorias${qs}`);
};

export const fetchMaintenanceNewTickets = (limit: number = 10) => {
  return fetchFromAPI<MaintenanceNewTicketItem[]>(`/manutencao/tickets-novos?limit=${limit}`);
};