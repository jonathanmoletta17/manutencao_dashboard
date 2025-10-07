import type {
  MaintenanceGeneralStats,
  EntityRankingItem,
  CategoryRankingItem,
  MaintenanceNewTicketItem,
  TechnicianRankingItem,
} from '../types/maintenance-api.d';

// Prefixo da API de manutenção
// Fallback absoluto para backend local se variável não estiver definida
const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
const API_BASE_URL = env?.VITE_API_BASE_URL ?? 'http://127.0.0.1:8010/api/v1';

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

// Top atribuição por entidades (global, sem filtro de datas)
export const fetchTopEntityAttribution = (top: number = 10) => {
  return fetchFromAPI<EntityRankingItem[]>(`/manutencao/top-atribuicao-entidades?top=${top}`);
};

// Top atribuição por categorias (global, sem filtro de datas)
export const fetchTopCategoryAttribution = (top: number = 10) => {
  return fetchFromAPI<CategoryRankingItem[]>(`/manutencao/top-atribuicao-categorias?top=${top}`);
};

// Ranking de Técnicos (por período). Se o endpoint não existir ainda, retorna [] ao invés de falhar.
export const fetchTechnicianRanking = async (inicio?: string, fim?: string, top: number = 10) => {
  const qs = inicio && fim ? `?inicio=${encodeURIComponent(inicio)}&fim=${encodeURIComponent(fim)}&top=${top}` : `?top=${top}`;
  const url = `${API_BASE_URL}/manutencao/ranking-tecnicos${qs}`;
  // Guardar último valor válido para evitar "piscar" vazio em erros intermitentes
  // Escopo de módulo: persiste enquanto a página estiver carregada
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const globalAny = globalThis as any;
  if (!globalAny.__lastTechnicianRanking) {
    globalAny.__lastTechnicianRanking = [] as TechnicianRankingItem[];
  }
  try {
    const response = await fetch(url);
    if (!response.ok) {
      // Tratar 404/501 como ausência de dados, para não quebrar o layout
      if (response.status === 404 || response.status === 501) {
        // manter último conhecido, mesmo que vazio inicialmente
        return globalAny.__lastTechnicianRanking as TechnicianRankingItem[];
      }
      const errorData = await response.json().catch(() => ({ detail: `Erro ${response.status} ao acessar ${url}` }));
      throw new Error(errorData.detail || `Falha ao buscar ranking de técnicos`);
    }
    const data = (await response.json()) as TechnicianRankingItem[];
    globalAny.__lastTechnicianRanking = data;
    return data;
  } catch (err) {
    console.error('Erro de rede ao buscar ranking de técnicos:', err);
    // Retornar último valor válido ao invés de zerar
    return globalAny.__lastTechnicianRanking as TechnicianRankingItem[];
  }
};