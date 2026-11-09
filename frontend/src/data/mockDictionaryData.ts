/**
 * Baseball dictionary adapter for data/dict/dict.json.
 * The source of truth is cards/*.yaml; do not edit generated dict.json by hand.
 */
import rawDictionary from './dict.json';

export interface DictionaryCategory {
  id: string;
  name: string;
  terms: string[];
}

export interface RAGSource {
  title: string;
  sourceType: string;
  referenceUrl?: string;
}

export interface TermDetail {
  id: string;
  kind: 'term' | 'rule';
  name: string;
  englishName: string;
  category: string;
  oneLineSummary: string;
  beginnerExplanation: string;
  example?: string;
  more: string[];
  relatedTerms: string[];
  sources: RAGSource[];
  reviewStatus: string;
  defaultFollowUpQuestion?: string;
  defaultFollowUpAnswer?: string;
  // Preserved for other components that might depend on this field.
  gameFlow: string[];
}

interface DictionarySource {
  name?: string;
  ref?: string;
  note?: string;
  url?: string;
}

interface DictionaryCard {
  id: string;
  kind: 'term' | 'rule';
  title: string;
  category: string;
  one_liner: string;
  easy: string;
  example?: string;
  more?: string[];
  source?: DictionarySource[];
  related?: string[];
  aliases?: string[];
  review_status?: string;
}

interface DictionaryJSON {
  cards: Record<string, DictionaryCard>;
  alias_index?: Record<string, string | string[]>;
  event_index?: Record<string, string[]>;
}

const dictionary = rawDictionary as unknown as DictionaryJSON;
export const DICTIONARY_CARDS = dictionary.cards;
const cards = Object.values(DICTIONARY_CARDS);

// '규칙' and '용어' may have identically named category groups; keep them separate.
const categoryGroups = new Map<string, DictionaryCategory>();
for (const card of cards) {
  const key = `${card.kind}:${card.category}`;
  if (!categoryGroups.has(key)) {
    categoryGroups.set(key, {
      id: key,
      name: `${card.kind === 'rule' ? '규칙' : '용어'} · ${card.category}`,
      terms: [],
    });
  }
  categoryGroups.get(key)!.terms.push(card.id);
}
export const DICTIONARY_CATEGORIES: DictionaryCategory[] = [...categoryGroups.values()];

export function getTermDetailOrDefault(cardId: string): TermDetail | null {
  const card = DICTIONARY_CARDS[cardId];
  if (!card) return null;
  return {
    id: card.id,
    kind: card.kind,
    name: card.title,
    englishName: '', // Dictionary has no official English title field.
    category: card.category,
    oneLineSummary: card.one_liner,
    beginnerExplanation: card.easy,
    example: card.example,
    more: card.more ?? [],
    gameFlow: [], // Do not fabricate a stepwise play sequence from a single example.
    relatedTerms: (card.related ?? []).filter(id => Boolean(DICTIONARY_CARDS[id])),
    sources: (card.source ?? []).map(source => ({
      title: [source.name, source.ref].filter(Boolean).join(' · ') || '출처 정보',
      sourceType: source.note || '참고자료',
      referenceUrl: source.url,
    })),
    reviewStatus: card.review_status ?? 'draft',
  };
}

function normalize(value: string): string {
  return value.toLocaleLowerCase().replace(/\s+/g, '').replace(/^#/, '').trim();
}

export function searchDictionary(query: string): string | null {
  const q = normalize(query);
  if (!q) return null;

  // Prefer exact matches before partial ones.
  const exact = cards.find(card =>
    [card.title, card.id, ...(card.aliases ?? [])].some(term => normalize(term) === q)
  );
  if (exact) return exact.id;

  const partial = cards.find(card =>
    [card.title, ...(card.aliases ?? [])].some(term => normalize(term).includes(q))
  );
  return partial?.id ?? null;
}

export const TOTAL_DICTIONARY_CARDS = cards.length;
