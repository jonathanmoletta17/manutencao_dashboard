export const fmt = (n: number | undefined | null) =>
  n !== undefined && n !== null ? new Intl.NumberFormat('pt-BR').format(n) : '-';

// (remoção de helper para manter implementação enxuta)

// Formatação segura de datas e horas vindas do backend
export function fmtYmd(ymd: string | undefined | null): string {
  const s = (ymd || '').trim();
  if (!s) return '-';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return s; // mantém formato desconhecido
  const [y, m, d] = s.split('-');
  return `${d}/${m}/${y}`;
}

function fmtHms(hms: string | undefined | null): string {
  const s = (hms || '').trim();
  if (!s) return '';
  if (!/^\d{2}:\d{2}(:\d{2})?$/.test(s)) return s; // mantém formato desconhecido
  // Exibir apenas HH:MM para compacidade
  return s.slice(0, 5);
}

/**
 * Divide uma string datetime em partes formatadas para exibição (data e hora).
 * Aceita formatos "YYYY-MM-DD HH:MM[:SS]" ou ISO "YYYY-MM-DDTHH:MM[:SS]Z".
 */
export function fmtDateTimeParts(datetime: string | undefined | null): { date: string; time: string } {
  const s = (datetime || '').trim();
  if (!s) return { date: '-', time: '' };
  // Formato com espaço
  const spaceParts = s.split(/\s+/);
  if (spaceParts.length === 2) {
    return { date: fmtYmd(spaceParts[0]), time: fmtHms(spaceParts[1]) };
  }
  // Formato ISO com 'T' e possivelmente 'Z' ou frações
  const tParts = s.split('T');
  if (tParts.length === 2) {
    const datePart = tParts[0];
    const timePart = tParts[1].replace('Z', '').split('.')[0];
    return { date: fmtYmd(datePart), time: fmtHms(timePart) };
  }
  // Fallback: devolve tudo como data
  return { date: s, time: '' };
}

// Formata um valor de data (Date/epoch/string) para HH:MM.
export function fmtTimeOfDay(value: Date | number | string | undefined | null): string {
  if (value === undefined || value === null) return '';
  let d: Date;
  if (value instanceof Date) {
    d = value;
  } else if (typeof value === 'number') {
    d = new Date(value);
  } else {
    const s = String(value).trim();
    if (!s) return '';
    const parsed = new Date(s);
    if (isNaN(parsed.getTime())) return '';
    d = parsed;
  }
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}