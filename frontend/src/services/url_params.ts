// Utilitário central para leitura/validação e persistência de parâmetros de URL
// Foca nos parâmetros: inicio, fim, top
import { ALLOWED_TOP } from '../constants/top';

const toYmd = (d: Date) => d.toISOString().slice(0, 10);

export interface DateRange {
  inicio: string;
  fim: string;
}

export function getDefaultDateRange(now: Date = new Date()): DateRange {
  const end = new Date(now);
  const start = new Date(now);
  start.setDate(start.getDate() - 30);
  return { inicio: toYmd(start), fim: toYmd(end) };
}

export function readTopNFromUrl(href: string, fallback: number = 5): number {
  try {
    const url = new URL(href);
    const qsTop = url.searchParams.get('top');
    const n = qsTop ? Number(qsTop) : NaN;
    return ALLOWED_TOP.includes(n as 5 | 10 | 15) ? n : fallback;
  } catch {
    return fallback;
  }
}

export function readDateRangeFromUrl(href: string, fallback?: DateRange): DateRange {
  const def = fallback ?? getDefaultDateRange();
  try {
    const url = new URL(href);
    const qsInicio = url.searchParams.get('inicio');
    const qsFim = url.searchParams.get('fim');
    if (qsInicio && qsFim && qsInicio <= qsFim) {
      return { inicio: qsInicio, fim: qsFim };
    }
    return def;
  } catch {
    return def;
  }
}

export function replaceUrlParams(dateRange: DateRange, topN: number): void {
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('inicio', dateRange.inicio);
    url.searchParams.set('fim', dateRange.fim);
    url.searchParams.set('top', String(topN));
    window.history.replaceState(null, '', `${url.pathname}?${url.searchParams.toString()}`);
  } catch {
    // Ignorar falhas silenciosamente para não quebrar a UI
  }
}