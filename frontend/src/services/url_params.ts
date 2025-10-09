// Utilitário central para leitura/validação e persistência de parâmetros de URL
// Foca nos parâmetros: inicio, fim

const toYmd = (d: Date) => d.toISOString().slice(0, 10);

// Cache simples para garantir identidade estável de objetos DateRange
const dateRangeCache = new Map<string, Readonly<DateRange>>();
const getStableDateRange = (inicio: string, fim: string): Readonly<DateRange> => {
  const key = `${inicio}|${fim}`;
  const cached = dateRangeCache.get(key);
  if (cached) return cached;
  const obj = Object.freeze({ inicio, fim });
  dateRangeCache.set(key, obj);
  return obj;
};

export interface DateRange {
  inicio: string;
  fim: string;
}

export type CategoryMode = 'original' | 'aggregated';

export function getDefaultDateRange(now: Date = new Date()): DateRange {
  const end = new Date(now);
  const start = new Date(now);
  start.setDate(start.getDate() - 30);
  return { inicio: toYmd(start), fim: toYmd(end) };
}

export function readDateRangeFromUrl(href: string, fallback?: DateRange): DateRange {
  const def = fallback ?? getDefaultDateRange();
  try {
    const url = new URL(href);
    const qsInicio = url.searchParams.get('inicio');
    const qsFim = url.searchParams.get('fim');
    if (qsInicio && qsFim && qsInicio <= qsFim) {
      return getStableDateRange(qsInicio, qsFim);
    }
    return getStableDateRange(def.inicio, def.fim);
  } catch {
    return getStableDateRange(def.inicio, def.fim);
  }
}

export function replaceUrlParams(dateRange: DateRange): void {
  try {
    const url = new URL(window.location.href);
    url.searchParams.set('inicio', dateRange.inicio);
    url.searchParams.set('fim', dateRange.fim);
    window.history.replaceState(null, '', `${url.pathname}?${url.searchParams.toString()}`);
  } catch {
    // Ignorar falhas silenciosamente para não quebrar a UI
  }
}

export function readCategoryModeFromUrl(href: string, fallback: CategoryMode = 'original'): CategoryMode {
  try {
    const url = new URL(href);
    const raw = (url.searchParams.get('cat') || '').toLowerCase();
    if (raw === 'agg' || raw === 'aggregated' || raw === '2') return 'aggregated';
    if (raw === 'orig' || raw === 'original' || raw === '1') return 'original';
    return fallback;
  } catch {
    return fallback;
  }
}

export function replaceCategoryModeInUrl(mode: CategoryMode): void {
  try {
    const url = new URL(window.location.href);
    const val = mode === 'aggregated' ? 'agg' : 'orig';
    url.searchParams.set('cat', val);
    window.history.replaceState(null, '', `${url.pathname}?${url.searchParams.toString()}`);
  } catch {
    // Ignorar falhas silenciosamente
  }
}