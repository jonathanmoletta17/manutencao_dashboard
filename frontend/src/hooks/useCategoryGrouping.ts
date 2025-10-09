import { useMemo } from 'react';
import { removeDiacritics } from '../utils/strings';
import type { CategoryRankingItem } from '../types/maintenance-api.d';
import { transformCategoryRanking } from '../utils/categories';

export type MacroArea = 'Manutenção' | 'Conservação';

// usa utilitário compartilhado para normalização de acentos

export function classifyMacroArea(label: string | undefined | null): MacroArea | null {
  if (!label) return null;
  const first = label.split('>', 1)[0].trim();
  const plain = removeDiacritics(first).toLowerCase();
  if (plain.startsWith('manutencao')) return 'Manutenção';
  if (plain.startsWith('conservacao')) return 'Conservação';
  return null;
}

/**
 * Agrupa categorias por macro área, filtrando valores inválidos e ordenando por `ticket_count` desc.
 */
export function useCategoryGrouping(
  categoryRanking: CategoryRankingItem[] | null,
  mode: 'original' | 'aggregated' = 'original',
) {
  return useMemo(() => {
    const items = (categoryRanking ?? []).filter((it) => {
      const raw = (it.category_name ?? '').trim();
      const norm = removeDiacritics(raw).toLowerCase();
      return Boolean(raw) && norm !== 'none' && norm !== 'null';
    });
    const man = transformCategoryRanking(items, 'Manutenção', mode);
    const cons = transformCategoryRanking(items, 'Conservação', mode);
    return { manCategories: man, consCategories: cons };
  }, [categoryRanking, mode]);
}