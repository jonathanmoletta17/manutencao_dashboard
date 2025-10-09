import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  MaintenanceGeneralStats,
  EntityRankingItem,
  CategoryRankingItem,
  MaintenanceNewTicketItem,
  TechnicianRankingItem,
} from '../types/maintenance-api.d';
import {
  fetchMaintenanceGeneralStats,
  fetchMaintenanceNewTickets,
  fetchEntityRanking,
  fetchCategoryRanking,
  fetchTechnicianRanking,
} from '../services/maintenance-api';

export interface DateRange {
  inicio: string;
  fim: string;
}

export function useDashboardData(dateRange: DateRange) {
  const [generalStats, setGeneralStats] = useState<MaintenanceGeneralStats | null>(null);
  const [entityRanking, setEntityRanking] = useState<EntityRankingItem[] | null>(null);
  const [categoryRanking, setCategoryRanking] = useState<CategoryRankingItem[] | null>(null);
  const [technicianRanking, setTechnicianRanking] = useState<TechnicianRankingItem[] | null>(null);
  const [newTickets, setNewTickets] = useState<MaintenanceNewTicketItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshInFlight = useRef(false);
  const dateRangeRef = useRef(dateRange);
  // Cache leve para ranking de técnicos com TTL curto
  const techCacheRef = useRef<{ key: string; data: TechnicianRankingItem[]; ts: number } | null>(null);

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
      // Paraleliza chamadas independentes
      const getTechnicianRanking = async () => {
        const key = `${inicio}|${fim}|all`;
        const ttlMs = 5000; // reutiliza resultado por até 5s se parâmetros não mudarem
        const cached = techCacheRef.current;
        const now = Date.now();
        if (cached && cached.key === key && (now - cached.ts) < ttlMs) {
          return cached.data;
        }
        const data = await fetchTechnicianRanking(inicio, fim);
        techCacheRef.current = { key, data, ts: now };
        return data;
      };

      const results = await Promise.allSettled([
        fetchMaintenanceGeneralStats(inicio, fim),
        fetchEntityRanking(inicio, fim),
        fetchCategoryRanking(inicio, fim),
        fetchMaintenanceNewTickets(8),
        getTechnicianRanking(),
      ]);

      const [gsRes, erRes, crRes, ntRes, tkRes] = results;
      let firstError: string | null = null;

      if (gsRes.status === 'fulfilled') setGeneralStats(gsRes.value);
      else firstError = firstError ?? String(gsRes.reason);

      if (erRes.status === 'fulfilled') setEntityRanking(erRes.value);
      else firstError = firstError ?? String(erRes.reason);

      if (crRes.status === 'fulfilled') setCategoryRanking(crRes.value);
      else firstError = firstError ?? String(crRes.reason);

      if (ntRes.status === 'fulfilled') setNewTickets(ntRes.value);
      else firstError = firstError ?? String(ntRes.reason);

      if (tkRes.status === 'fulfilled') setTechnicianRanking(tkRes.value);
      else firstError = firstError ?? String(tkRes.reason);

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
    technicianRanking,
    newTickets,
    refresh,
    error,
  };
}