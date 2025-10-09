import { useMemo } from 'react';
import { removeDiacritics } from '../utils/strings';
import type { CategoryRankingItem } from '../types/maintenance-api.d';

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
export function useCategoryGrouping(categoryRanking: CategoryRankingItem[] | null) {
  return useMemo(() => {
    const man: CategoryRankingItem[] = [];
    const cons: CategoryRankingItem[] = [];
    (categoryRanking ?? []).forEach((item) => {
      const raw = (item.category_name ?? '').trim();
      const norm = removeDiacritics(raw).toLowerCase();
      // Ocultar itens inválidos como 'None', 'null' ou vazio
      if (!raw || norm === 'none' || norm === 'null') return;
      const grp = classifyMacroArea(item.category_name);
      if (grp === 'Manutenção') man.push(item);
      else if (grp === 'Conservação') cons.push(item);
      // Ignora itens fora das macro áreas conhecidas
    });
    man.sort((a, b) => (b.ticket_count ?? 0) - (a.ticket_count ?? 0));
    cons.sort((a, b) => (b.ticket_count ?? 0) - (a.ticket_count ?? 0));
    return { manCategories: man, consCategories: cons };
  }, [categoryRanking]);
}