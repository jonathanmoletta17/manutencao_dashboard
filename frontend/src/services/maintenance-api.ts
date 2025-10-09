import type {
  MaintenanceGeneralStats,
  EntityRankingItem,
  CategoryRankingItem,
  MaintenanceNewTicketItem,
  TechnicianRankingItem,
} from '../types/maintenance-api.d';
import { APIError, formatApiError } from './errors';

// Base da API e prefixo de versão (uso direto para permitir substituição estática do Vite)
const RAW_BASE = import.meta.env.VITE_API_BASE_URL as string | undefined;
const RAW_VERSION = (import.meta.env.VITE_API_VERSION_PREFIX as string | undefined) ?? '/api/v1';

// Normaliza partes da URL evitando erros de "Invalid base URL"
function trimTrailingSlash(s: string): string {
  return s.replace(/\/$/, '');
}

function ensureLeadingSlash(s: string): string {
  return s.startsWith('/') ? s : `/${s}`;
}

// Resolve origem e prefixo de path conforme ambiente
let API_BASE_ORIGIN: string;
let API_PATH_PREFIX: string;
if (RAW_BASE && RAW_BASE.startsWith('/')) {
  // Base relativa atrás de Nginx: usa a origem atual do browser
  API_BASE_ORIGIN = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000';
  API_PATH_PREFIX = trimTrailingSlash(RAW_BASE);
} else if (RAW_BASE) {
  // Base absoluta fornecida (dev externo): respeita host e porta
  API_BASE_ORIGIN = trimTrailingSlash(RAW_BASE);
  API_PATH_PREFIX = ensureLeadingSlash(RAW_VERSION);
} else {
  // Fallback: mesma origem com prefixo padrão
  API_BASE_ORIGIN = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000';
  API_PATH_PREFIX = ensureLeadingSlash(RAW_VERSION);
}

function buildURL(endpoint: string, query?: Record<string, unknown>) {
  const base = trimTrailingSlash(API_BASE_ORIGIN);
  const prefix = trimTrailingSlash(API_PATH_PREFIX);
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  let url = `${base}${prefix}${path}`;
  if (query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null) continue;
      params.append(key, String(value));
    }
    const q = params.toString();
    if (q) url += `?${q}`;
  }
  return url;
}

async function fetchFromAPI<T>(endpoint: string, init?: RequestInit & { query?: Record<string, unknown> }): Promise<T> {
  const url = buildURL(endpoint, init?.query);
  const { query: _ignored, headers, ...rest } = init ?? {};
  const isJsonBody = rest.body && typeof rest.body === 'string';
  const mergedHeaders = {
    ...(isJsonBody ? { 'Content-Type': 'application/json' } : {}),
    ...headers,
  } as HeadersInit;

  const response = await fetch(url, { method: rest.method ?? 'GET', headers: mergedHeaders, body: rest.body });

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const data = await response.json();
      detail = (data && (data.detail || data.error)) as string | undefined;
    } catch {
      // Ignorar parsing errors
    }
    const message = formatApiError(endpoint, response.status, response.statusText, detail);
    throw new APIError(endpoint, message, response.status, detail);
  }

  return response.json() as Promise<T>;
}

// Endpoints específicos para Manutenção

export const fetchMaintenanceGeneralStats = (inicio?: string, fim?: string) => {
  return fetchFromAPI<MaintenanceGeneralStats>(`/manutencao/stats-gerais`, { query: { inicio, fim } });
};

export const fetchEntityRanking = (inicio?: string, fim?: string, top: number = 10) => {
  return fetchFromAPI<EntityRankingItem[]>(`/manutencao/ranking-entidades`, { query: { inicio, fim, top } });
};

export const fetchCategoryRanking = (inicio?: string, fim?: string, top: number = 10) => {
  return fetchFromAPI<CategoryRankingItem[]>(`/manutencao/ranking-categorias`, { query: { inicio, fim, top } });
};

export const fetchMaintenanceNewTickets = (limit: number = 10) => {
  return fetchFromAPI<MaintenanceNewTicketItem[]>(`/manutencao/tickets-novos`, { query: { limit } });
};

// Ranking de Técnicos (por período). Se o endpoint não existir ainda, retorna [] ao invés de falhar.
export const fetchTechnicianRanking = async (inicio?: string, fim?: string, top: number = 10) => {
  try {
    return await fetchFromAPI<TechnicianRankingItem>(`/manutencao/ranking-tecnicos`, { query: { inicio, fim, top } }) as unknown as TechnicianRankingItem[];
  } catch (err) {
    if (err instanceof APIError && (err.status === 404 || err.status === 501)) {
      // Considera ausência de dados sem quebrar o layout
      return [] as TechnicianRankingItem[];
    }
    throw err;
  }
};