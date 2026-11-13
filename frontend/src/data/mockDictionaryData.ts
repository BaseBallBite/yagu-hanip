
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
  gameFlow: string[];

  // SVG 이미지 경로
  image?: string | null;
  image_static?: string | null;
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

  // 원본 dict.json의 SVG 필드
  image?: string | null;
  image_static?: string | null;
}

interface DictionaryJSON {
  cards: Record<string, DictionaryCard>;
  alias_index?: Record<string, string | string[]>;
  event_index?: Record<string, string[]>;
}

const dictionary = rawDictionary as unknown as DictionaryJSON;

export const DICTIONARY_CARDS = dictionary.cards;

const cards = Object.values(DICTIONARY_CARDS);

// 규칙·용어 카테고리는 구분해서 유지
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

export const DICTIONARY_CATEGORIES: DictionaryCategory[] = [
  ...categoryGroups.values(),
];

export function getTermDetailOrDefault(
  cardId: string
): TermDetail | null {
  const card = DICTIONARY_CARDS[cardId];

  if (!card) return null;

  return {
    id: card.id,
    kind: card.kind,
    name: card.title,
    englishName: '',
    category: card.category,
    oneLineSummary: card.one_liner,
    beginnerExplanation: card.easy,
    example: card.example,
    more: card.more ?? [],
    gameFlow: [],
    relatedTerms: (card.related ?? []).filter(
      id => Boolean(DICTIONARY_CARDS[id])
    ),

    sources: (card.source ?? []).map(source => ({
      title:
        [source.name, source.ref]
          .filter(Boolean)
          .join(' · ') || '출처 정보',
      sourceType: source.note || '참고자료',
      referenceUrl: source.url,
    })),

    reviewStatus: card.review_status ?? 'draft',

    // SVG 이미지 필드를 상세 화면으로 전달
    image: card.image ?? null,
    image_static: card.image_static ?? null,
  };
}

function normalize(value: string): string {
  return value
    .toLocaleLowerCase()
    .replace(/\s+/g, '')
    .replace(/^#/, '')
    .trim();
}

export function searchDictionary(
  query: string
): string | null {
  const q = normalize(query);

  if (!q) return null;

  // 정확히 일치하는 용어 우선
  const exact = cards.find(card =>
    [card.title, card.id, ...(card.aliases ?? [])].some(
      term => normalize(term) === q
    )
  );

  if (exact) return exact.id;

  // 부분 일치 검색
  const partial = cards.find(card =>
    [card.title, ...(card.aliases ?? [])].some(
      term => normalize(term).includes(q)
    )
  );

  return partial?.id ?? null;
}

export const TOTAL_DICTIONARY_CARDS = cards.length;
