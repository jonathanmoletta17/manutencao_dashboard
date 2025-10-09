export function removeDiacritics(s: string) {
  return s ? s.normalize('NFD').replace(/[\u0300-\u036f]/g, '') : s;
}

export function normalizeArrowSpaces(s: string) {
  return (s || '').replace(/\s*>\s*/g, ' > ').trim();
}

export function toKeyLower(s: string) {
  return removeDiacritics(s).toLowerCase().trim();
}