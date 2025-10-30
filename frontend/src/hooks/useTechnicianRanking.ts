import { useCallback, useEffect, useRef, useState } from 'react';
import type { TechnicianRankingItem } from '../types/maintenance-api.d';
import { fetchTechnicianRanking } from '../services/maintenance-api';

export interface DateRange {
  inicio: string;
  fim: string;
}

/**
 * Hook dedicado para carregar o Ranking de Técnicos de forma independente.
 * - Mantém estado de carregamento prolongado (items === null) até concluir ou esgotar retries
 * - Em caso de timeout/resultado vazio, tenta novamente algumas vezes
 * - Se existir dado em cache (stale), exibe-o enquanto processa
 */
export function useTechnicianRanking(dateRange: DateRange) {
  const [items, setItems] = useState<TechnicianRankingItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const dateRangeRef = useRef(dateRange);

  // Cache simples com TTL maior para permitir fallback em timeout real
  const cacheRef = useRef<{ key: string; data: TechnicianRankingItem[]; ts: number } | null>(null);

  useEffect(() => {
    dateRangeRef.current = dateRange;
  }, [dateRange]);

  const refresh = useCallback(async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    setError(null);
    const { inicio, fim } = dateRangeRef.current;
    const key = `${inicio}|${fim}|all`;

    // Configuráveis via .env (valores padrão sensatos)
    const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
    const maxAttempts = env?.VITE_TECH_RANK_RETRY_ATTEMPTS !== undefined
      ? Math.max(1, Number(env.VITE_TECH_RANK_RETRY_ATTEMPTS))
      : 3;
    const retryDelayMs = env?.VITE_TECH_RANK_RETRY_MS !== undefined
      ? Math.max(500, Number(env.VITE_TECH_RANK_RETRY_MS))
      : 4000;
    const staleTtlMs = env?.VITE_TECH_RANK_STALE_TTL_MS !== undefined
      ? Math.max(1000, Number(env.VITE_TECH_RANK_STALE_TTL_MS))
      : 5 * 60 * 1000; // 5min

    // Mostra stale imediatamente, se existir e estiver fresco
    const now = Date.now();
    const cached = cacheRef.current;
    const hasFreshStale = cached && cached.key === key && (now - cached.ts) < staleTtlMs && (cached.data?.length ?? 0) > 0;
    if (hasFreshStale) {
      setItems(cached!.data);
    } else {
      setItems(null); // força "Carregando…" enquanto processa
    }

    let attempt = 0;
    let lastResult: TechnicianRankingItem[] | null = null;
    let lastErr: unknown = null;

    try {
      while (attempt < maxAttempts) {
        try {
          const data = await fetchTechnicianRanking(inicio, fim);
          lastResult = data;
          if (Array.isArray(data) && data.length > 0) {
            cacheRef.current = { key, data, ts: Date.now() };
            setItems(data);
            setError(null);
            return;
          }
          // Se veio vazio, aguarda e tenta novamente (possível timeout no backend/GLPI)
        } catch (err) {
          lastErr = err;
        }

        attempt += 1;
        if (attempt < maxAttempts) {
          await new Promise((res) => setTimeout(res, retryDelayMs));
        }
      }

      // Esgotou tentativas:
      // - Se há stale válido, mantém (consistência visual)
      // - Se não há stale e o último resultado foi vazio ou erro, mantém carregando para evitar "indisponível" prematuro
      if (hasFreshStale) {
        setItems(cached!.data);
        setError(lastErr ? String(lastErr) : null);
      } else {
        const isEmptyArray = Array.isArray(lastResult) && lastResult.length === 0;
        if (isEmptyArray || lastErr) {
          // Mantém carregando para não exibir indisponível enquanto ainda há chance de concluir
          setItems(null);
          setError(lastErr ? String(lastErr) : null);
        } else if (lastResult) {
          // Caso raro: algum dado não vazio chegou aqui
          cacheRef.current = { key, data: lastResult, ts: Date.now() };
          setItems(lastResult);
          setError(null);
        } else {
          // Sem stale e sem dado: mantém carregando
          setItems(null);
          setError(lastErr ? String(lastErr) : null);
        }
      }
    } finally {
      inFlightRef.current = false;
    }
  }, []);

  // Carregamento inicial e quando o intervalo mudar
  useEffect(() => {
    const t = setTimeout(() => { refresh(); }, 250);
    return () => clearTimeout(t);
  }, [dateRange.inicio, dateRange.fim, refresh]);

  // Polling opcional independente (reutiliza stale entre ciclos)
  useEffect(() => {
    const env = (import.meta as unknown as { env: Record<string, string | undefined> }).env;
    const rawPollSec = env?.VITE_REALTIME_POLL_INTERVAL_SEC;
    const intervalMs = rawPollSec !== undefined ? Number(rawPollSec) * 1000 : 15000;
    const id = setInterval(() => {
      if (inFlightRef.current) return;
      refresh();
    }, intervalMs);
    return () => clearInterval(id);
  }, [refresh]);

  return { items, refresh, error };
}

export default useTechnicianRanking;