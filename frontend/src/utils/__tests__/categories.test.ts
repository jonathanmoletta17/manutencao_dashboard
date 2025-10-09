import { describe, it, expect } from 'vitest';
import { transformCategoryRanking, normalize } from '../../utils/categories';

describe('normalize()', () => {
  it('removes diacritics, collapses spaces, and lowercases', () => {
    expect(normalize('  Hidráulica   Avançada ')).toBe('hidraulica avancada');
    expect(normalize('Conservação')).toBe('conservacao');
  });
});

describe('transformCategoryRanking()', () => {
  const sample = [
    { category_name: 'Manutenção > Marcenaria > Outras Atividades', ticket_count: 8 },
    { category_name: 'Manutenção > Marcenaria', ticket_count: 7 },
    { category_name: 'Manutenção > Pedreiro', ticket_count: 6 },
    { category_name: 'Manutenção > Hidráulica > Reparo/Conserto', ticket_count: 4 },
    { category_name: 'Manutenção > Hidráulica', ticket_count: 3 },
    { category_name: 'Conservação > Hidráulica', ticket_count: 99 },
    { category_name: 'Conservação > Marcenaria', ticket_count: 5 },
  ];

  it('aggregates by second level within Manutenção', () => {
    const res = transformCategoryRanking(sample, 'Manutenção', 'aggregated');
    expect(res).toEqual([
      { category_name: 'Manutenção > Marcenaria', ticket_count: 15 },
      { category_name: 'Manutenção > Hidráulica', ticket_count: 7 },
      { category_name: 'Manutenção > Pedreiro', ticket_count: 6 },
    ]);
  });

  it('does not mix areas', () => {
    const man = transformCategoryRanking(sample, 'Manutenção', 'aggregated');
    const cons = transformCategoryRanking(sample, 'Conservação', 'aggregated');
    expect(man.find((x) => x.category_name.includes('Conservação'))).toBeUndefined();
    expect(cons.find((x) => x.category_name.includes('Manutenção'))).toBeUndefined();
  });

  it('original mode keeps items and sorts by count desc then label', () => {
    const res = transformCategoryRanking(sample, 'Conservação', 'original');
    expect(res.map((x) => x.category_name)).toEqual([
      'Conservação > Hidráulica',
      'Conservação > Marcenaria',
    ]);
  });
});