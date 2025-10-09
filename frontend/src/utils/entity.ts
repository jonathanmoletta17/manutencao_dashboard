import { normalizeArrowSpaces, toKeyLower } from './strings';

const PARENT = 'Origem > PIRATINI';
const PARENT_KEY = toKeyLower(PARENT);

export function stripParentPrefix(name: string) {
  const s = (name || '').trim();
  const norm = normalizeArrowSpaces(s);
  const lower = toKeyLower(norm);
  if (lower === PARENT_KEY) return s;
  if (lower.startsWith(PARENT_KEY + ' > ')) {
    // remove prefixo padrão seguido de ' > '
    return norm.slice(PARENT.length + 3).trim();
  }
  return s;
}

export function abbreviateEntityName(rawName: string) {
  const name = stripParentPrefix(rawName ?? '');
  const norm = normalizeArrowSpaces(name);
  if (!norm) return name;
  // Não abrevia o caso exato "Origem > Piratini"
  const normLower = toKeyLower(norm);
  if (normLower === 'origem > piratini') return norm;

  const parts = norm.split(' > ').map((p) => p.trim()).filter(Boolean);
  if (parts.length <= 1) return parts[0] ?? name;
  const first = parts[0];
  const last = parts[parts.length - 1];

  const SIGLAS_PRIMEIRO: Record<string, string> = {
    'casa civil': 'CC',
    'gabinete do governador': 'GG',
    'gabinete do vice-governador': 'GVG',
    'secom': 'SECOM',
    'casa militar': 'CM',
  };
  const firstKey = toKeyLower(first);
  let sigla = SIGLAS_PRIMEIRO[firstKey];
  if (!sigla) {
    const stop = new Set(['da','de','do','dos','das','e']);
    const words = firstKey.split(/\s+/).filter((w) => w && !stop.has(w));
    sigla = words.filter((w) => w.length >= 3).map((w) => w[0]).join('').slice(0,4).toUpperCase();
    if (!sigla) sigla = (first.trim().slice(0,3) || first).toUpperCase();
  }

  if (!last || toKeyLower(last) === firstKey) return first; // evita duplicação
  return `${sigla} > ${last}`;
}