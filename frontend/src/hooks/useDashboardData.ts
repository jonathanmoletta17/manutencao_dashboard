import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  MaintenanceGeneralStats,
  EntityRankingItem,
  CategoryRankingItem,
  MaintenanceNewTicketItem,
} from '../types/maintenance-api.d';
import {
  fetchMaintenanceGeneralStats,
  fetchMaintenanceNewTickets,
  fetchEntityRanking,
  fetchCategoryRanking,
} from '../services/maintenance-api';

export interface DateRange {
  inicio: string;
  fim: string;
}

export function useDashboardData(dateRange: DateRange) {
  const [generalStats, setGeneralStats] = useState<MaintenanceGeneralStats | null>(null);
  const [entityRanking, setEntityRanking] = useState<EntityRankingItem[] | null>(null);
  const [categoryRanking, setCategoryRanking] = useState<CategoryRankingItem[] | null>(null);
  const [newTickets, setNewTickets] = useState<MaintenanceNewTicketItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshInFlight = useRef(false);
  const dateRangeRef = useRef(dateRange);

  useEffect(() => {
    dateRangeRef.current = dateRange;
  }, [dateRange]);

  // Top N removido: sempre buscamos lista completa, TTL curto mantém responsividade

  const refresh = useCallback(async () => {
    if (refreshInFlight.current) return;
    refreshInFlight.current = true;
    const { inicio, fim } = dateRangeRef.current;
    try {
      setError(null);
      // Paraleliza chamadas independentes (sem ranking de técnicos)

      const results = await Promise.allSettled([
        fetchMaintenanceGeneralStats(inicio, fim),
        fetchEntityRanking(inicio, fim),
        fetchCategoryRanking(inicio, fim),
        fetchMaintenanceNewTickets(8),
      ]);

      const [gsRes, erRes, crRes, ntRes] = results;
      let firstError: string | null = null;

      if (gsRes.status === 'fulfilled') setGeneralStats(gsRes.value);
      else firstError = firstError ?? String(gsRes.reason);

      if (erRes.status === 'fulfilled') setEntityRanking(erRes.value);
      else firstError = firstError ?? String(erRes.reason);

      if (crRes.status === 'fulfilled') setCategoryRanking(crRes.value);
      else firstError = firstError ?? String(crRes.reason);

      if (ntRes.status === 'fulfilled') setNewTickets(ntRes.value);
      else firstError = firstError ?? String(ntRes.reason);

      if (firstError) setError(firstError);
    } finally {
      refreshInFlight.current = false;
    }
  }, []);

  // Carregamento inicial e quando dateRange mudar (com debounce leve)
  useEffect(() => {
    const t = setTimeout(() => { refresh(); }, 350);
    return () => clearTimeout(t);
  }, [dateRange.inicio, dateRange.fim, refresh]);

  // Polling interno configurável via .env (VITE_REALTIME_POLL_INTERVAL_SEC)
  useEffect(() => {
    const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
    const rawPollSec = env?.VITE_REALTIME_POLL_INTERVAL_SEC;
    const intervalMs = rawPollSec !== undefined ? Number(rawPollSec) * 1000 : 15000;
    const id = setInterval(async () => {
      if (refreshInFlight.current) return;
      await refresh();
    }, intervalMs);
    return () => clearInterval(id);
  }, [refresh]);

  return {
    generalStats,
    entityRanking,
    categoryRanking,
    newTickets,
    refresh,
    error,
  };
}