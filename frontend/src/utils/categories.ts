import { removeDiacritics } from '../utils/strings';
import type { CategoryRankingItem } from '../types/maintenance-api.d';

export type Area = 'Manutenção' | 'Conservação';
export type Mode = 'original' | 'aggregated';

export function normalize(s: string) {
  const base = (s || '').replace(/\s+/g, ' ');
  return removeDiacritics(base).toLowerCase().trim();
}

function isAreaMatch(firstLabel: string, area: Area): boolean {
  const first = normalize(firstLabel);
  if (area === 'Manutenção') return first.startsWith('manutencao');
  if (area === 'Conservação') return first.startsWith('conservacao');
  return false;
}

export function transformCategoryRanking(
  items: CategoryRankingItem[],
  area: Area,
  mode: Mode,
): CategoryRankingItem[] {
  const filtered = items.filter((it) => {
    const raw = (it.category_name ?? '').trim();
    if (!raw) return false;
    const parts = raw.split('>').map((s) => s.trim()).filter(Boolean);
    if (parts.length < 1) return false;
    return isAreaMatch(parts[0], area);
  });

  if (mode === 'original') {
    return filtered
      .filter((it) => (it.ticket_count ?? 0) > 0)
      .sort((a, b) => (b.ticket_count ?? 0) - (a.ticket_count ?? 0) || a.category_name.localeCompare(b.category_name));
  }

  const map = new Map<string, { display: string; count: number }>();
  for (const it of filtered) {
    const parts = (it.category_name || '').split('>').map((s) => s.trim()).filter(Boolean);
    if (parts.length < 2) continue; // sem nível 2, ignora
    if (!isAreaMatch(parts[0], area)) continue; // não mistura áreas
    const second = parts[1];
    const key = normalize(second);
    const prev = map.get(key);
    if (prev) prev.count += (it.ticket_count ?? 0);
    else map.set(key, { display: `${area} > ${second}`, count: (it.ticket_count ?? 0) });
  }

  return [...map.values()]
    .map((v) => ({ category_name: v.display, ticket_count: v.count }))
    .sort((a, b) => (b.ticket_count ?? 0) - (a.ticket_count ?? 0) || a.category_name.localeCompare(b.category_name));
}