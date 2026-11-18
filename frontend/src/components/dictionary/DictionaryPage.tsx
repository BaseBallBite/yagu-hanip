
import { useState, useEffect } from 'react';
import {
  DICTIONARY_CARDS,
  getTermDetailOrDefault,
} from '../../data/mockDictionaryData';
import type {
  TermDetail,
  RAGSource,
} from '../../data/mockDictionaryData';

import { DictionarySearchBar } from './DictionarySearchBar';
import { CategoryTermsNav } from './CategoryTermsNav';
import { TermDetailPanel } from './TermDetailPanel';

import {
  Sparkles,
  AlertCircle,
  LoaderCircle,
} from 'lucide-react';

import type { RecentSearchTerm } from '../../data/mockMyData';

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  'http://localhost:8000';

const RECENT_TERMS_KEY = 'yagu_recent_terms';
const DICTIONARY_TARGET_KEY = 'yagu_dictionary_target';
const MAX_RECENT_TERMS = 4;

const initialCardId = DICTIONARY_CARDS['term.double_play']
  ? 'term.double_play'
  : Object.keys(DICTIONARY_CARDS)[0] ?? '';

type ApiObject = Record<string, unknown>;

function asObject(value: unknown): ApiObject | null {
  return value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value)
    ? (value as ApiObject)
    : null;
}

function asString(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];

  return value
    .map((item) => {
      if (typeof item === 'string') return item;

      const obj = asObject(item);
      return obj ? asString(obj.id) : '';
    })
    .filter(Boolean);
}

function convertSources(value: unknown): RAGSource[] {
  if (!Array.isArray(value)) return [];

  return value.map((item) => {
    const source = asObject(item);

    if (!source) {
      return {
        title: String(item),
        sourceType: '참고자료',
      };
    }

    return {
      title:
        [
          asString(source.name),
          asString(source.ref),
        ]
          .filter(Boolean)
          .join(' · ') ||
        asString(source.title) ||
        '출처 정보',

      sourceType:
        asString(source.note) ||
        asString(source.sourceType) ||
        '참고자료',

      referenceUrl:
        asString(source.url) ||
        asString(source.referenceUrl) ||
        undefined,
    };
  });
}

function convertApiCard(
  response: unknown,
  cardId: string
): TermDetail | null {
  const outer = asObject(response);
  if (!outer) return null;

  const card =
    asObject(outer.card) ||
    asObject(outer.item) ||
    outer;

  const id = asString(card.id) || cardId;
  const local = getTermDetailOrDefault(id);

  const title =
    asString(card.title) ||
    asString(card.name) ||
    local?.name ||
    '';

  if (!title) return null;

  const kind =
    card.kind === 'rule' || card.kind === 'term'
      ? card.kind
      : local?.kind || 'term';

  const related = asStringArray(
    card.related ?? card.relatedTerms
  );

  const image =
    asString(card.image) ||
    local?.image ||
    null;

  const imageStatic =
    asString(card.image_static) ||
    local?.image_static ||
    null;

  return {
    id,
    kind,
    name: title,

    englishName:
      asString(card.englishName) ||
      local?.englishName ||
      '',

    category:
      asString(card.category) ||
      local?.category ||
      '',

    oneLineSummary:
      asString(card.one_liner) ||
      asString(card.oneLineSummary) ||
      local?.oneLineSummary ||
      '',

    beginnerExplanation:
      asString(card.easy) ||
      asString(card.beginnerExplanation) ||
      local?.beginnerExplanation ||
      '',

    example:
      asString(card.example) ||
      local?.example,

    more: Array.isArray(card.more)
      ? asStringArray(card.more)
      : local?.more || [],

    gameFlow: local?.gameFlow || [],

    relatedTerms: related.length
      ? related.filter((relatedId) =>
          Boolean(DICTIONARY_CARDS[relatedId])
        )
      : local?.relatedTerms || [],

    sources:
      card.source !== undefined
        ? convertSources(card.source)
        : card.sources !== undefined
          ? convertSources(card.sources)
          : local?.sources || [],

    reviewStatus:
      asString(card.review_status) ||
      asString(card.reviewStatus) ||
      local?.reviewStatus ||
      'draft',

    image,
    image_static: imageStatic,
  };
}

function extractSearchIds(response: unknown): string[] {
  if (Array.isArray(response)) return response.flatMap(extractSearchIds);
  const obj = asObject(response);
  if (!obj) return [];
  const id = asString(obj.id) || asString(obj.card_id);
  if (id) return [id];
  for (const key of ['items', 'results', 'cards', 'matches']) {
    const value = obj[key];
    if (value !== undefined) {
      if (asObject(value)) return Object.keys(asObject(value) || {});
      return extractSearchIds(value);
    }
  }
  return [];
}
function findLocalMatches(query: string): string[] {
  const normalized = query.replace(/\s/g, '').toLowerCase();
  return Object.values(DICTIONARY_CARDS)
    .filter(card => [card.title, card.category, card.one_liner, ...(card.aliases || [])]
      .some(value => typeof value === 'string' && value.replace(/\s/g, '').toLowerCase().includes(normalized)))
    .map(card => card.id);
}

async function fetchApi(
  path: string,
  signal?: AbortSignal
): Promise<unknown> {
  const response = await fetch(`${API_BASE}${path}`, {
    signal,
  });

  if (!response.ok) {
    throw new Error(
      `사전 API 요청 실패 (HTTP ${response.status})`
    );
  }

  return response.json();
}

function saveRecentTerm(detail: TermDetail) {
  const newTerm: RecentSearchTerm = {
    id: detail.id,
    name: detail.name,
    category: detail.category,
    description: detail.oneLineSummary,
  };

  try {
    const stored = localStorage.getItem(RECENT_TERMS_KEY);
    const parsed: unknown = stored ? JSON.parse(stored) : [];

    const previous: RecentSearchTerm[] = Array.isArray(parsed)
      ? parsed
      : [];

    const updated = [
      newTerm,
      ...previous.filter(
        (term) => term.id !== detail.id
      ),
    ].slice(0, MAX_RECENT_TERMS);

    localStorage.setItem(
      RECENT_TERMS_KEY,
      JSON.stringify(updated)
    );

    window.dispatchEvent(
      new Event('yagu-recent-terms-updated')
    );
  } catch (error) {
    console.error('최근 야구 용어 저장 실패:', error);
  }
}

export function DictionaryPage() {
  const [selectedTermId, setSelectedTermId] =
    useState(initialCardId);

  const [searchQuery, setSearchQuery] = useState('');

  const [searchNotFoundTerm, setSearchNotFoundTerm] =
    useState<string | null>(null);

  const [currentTermDetail, setCurrentTermDetail] =
    useState<TermDetail | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSearching, setIsSearching] = useState(false);
  const [searchMatchedIds, setSearchMatchedIds] = useState<string[]>([]);
  const [error, setError] = useState('');

  // B7 카드 상세 API
  useEffect(() => {
    if (!selectedTermId) {
      setIsLoading(false);
      return;
    }

    const controller = new AbortController();
    let active = true;

    async function loadDetail() {
      setIsLoading(true);
      setError('');
      setCurrentTermDetail(null);

      try {
        const response = await fetchApi(
          `/dict/cards/${encodeURIComponent(selectedTermId)}`,
          controller.signal
        );

        if (!active) return;

        const detail = convertApiCard(
          response,
          selectedTermId
        );

        if (!detail) {
          throw new Error(
            '카드 상세 응답 형식을 확인할 수 없어요.'
          );
        }

        setCurrentTermDetail(detail);
        saveRecentTerm(detail);
      } catch (err) {
        if (!active || controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : '사전 카드 정보를 불러오지 못했어요.'
        );
      } finally {
        if (active) setIsLoading(false);
      }
    }

    loadDetail();

    return () => {
      active = false;
      controller.abort();
    };
  }, [selectedTermId]);

  // MY에서 최근 검색한 용어 클릭 시 해당 카드 열기
  useEffect(() => {
    const targetId = sessionStorage.getItem(
      DICTIONARY_TARGET_KEY
    );

    if (targetId) {
      sessionStorage.removeItem(
        DICTIONARY_TARGET_KEY
      );

      if (DICTIONARY_CARDS[targetId]) {
        setSelectedTermId(targetId);
      }
    }
  }, []);

  const handleSelectTerm = (id: string) => {
    if (!DICTIONARY_CARDS[id]) return;

    setSearchNotFoundTerm(null);
    setSearchMatchedIds([]);
    setSelectedTermId(id);
    setError('');
  };

  // B7 API 검색: 여러 후보를 모두 보여주고, 선택은 사용자가 직접 하도록 처리
  const handleSearchSubmit = async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed) { setSearchNotFoundTerm(null); setSearchMatchedIds([]); return; }
    setIsSearching(true);
    setError('');
    setSearchNotFoundTerm(null);
    try {
      const response = await fetchApi(`/dict/search?q=${encodeURIComponent(trimmed)}`);
      const apiIds = extractSearchIds(response).filter(id => Boolean(DICTIONARY_CARDS[id]));
      const localIds = findLocalMatches(trimmed);
      const allIds = Array.from(new Set([...apiIds, ...localIds]));
      setSearchMatchedIds(allIds);
      if (allIds.length === 0) setSearchNotFoundTerm(trimmed);
      else if (allIds.length === 1) setSelectedTermId(allIds[0]);
    } catch (err) {
      setError(err instanceof Error ? err.message : '사전 검색에 실패했어요.');
    } finally { setIsSearching(false); }
  };

  return (
    <div className="w-full flex-1 py-6 sm:py-8 animate-fade-in">
      <div className="max-w-[1350px] w-full mx-auto px-4 sm:px-6">

        <div className="mb-8 text-center max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/90 text-purple-700 text-xs font-bold mb-2">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>야구 규칙·용어 카드 기반 지식 백과</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight">
            야구사전
          </h1>

          <p className="text-sm sm:text-base text-gray-500 mt-1.5 mb-6">
            모르는 야구 용어와 규칙을 초보자 눈높이로
            쉽게 확인해보세요.
          </p>

          <DictionarySearchBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSearchSubmit={handleSearchSubmit}
          />

          {searchMatchedIds.length > 0 && (
            <div className="mt-3 rounded-2xl border border-purple-100 bg-white p-3 text-left shadow-sm">
              <p className="mb-2 text-xs font-bold text-gray-600">검색 결과 {searchMatchedIds.length}개 · 원하는 용어를 선택해 주세요.</p>
              <div className="flex max-h-36 flex-wrap gap-2 overflow-y-auto">
                {searchMatchedIds.map(id => <button type="button" key={id} onClick={() => handleSelectTerm(id)} className="rounded-lg border border-purple-200 bg-purple-50 px-2.5 py-1.5 text-xs font-bold text-purple-700 hover:bg-purple-100">{DICTIONARY_CARDS[id]?.title}</button>)}
              </div>
            </div>
          )}

          {isSearching && (
            <p className="mt-2 text-xs text-purple-600">
              용어 검색 중...
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

          <div className="lg:col-span-5 w-full">
            <CategoryTermsNav
              selectedTermName={selectedTermId}
              onSelectTerm={handleSelectTerm}
              searchMatchedIds={searchMatchedIds}
            />
          </div>

          <div className="lg:col-span-7 w-full">
            {error ? (
              <div className="w-full bg-white rounded-3xl p-10 border border-red-100 flex flex-col items-center text-center">
                <AlertCircle className="w-9 h-9 text-red-500 mb-3" />
                <h3 className="font-bold text-gray-900 mb-2">
                  사전 데이터를 불러오지 못했어요.
                </h3>
                <p className="text-sm text-gray-500">
                  {error}
                </p>
                <p className="text-xs text-gray-400 mt-3">
                  백엔드 서버(localhost:8000)를 확인해 주세요.
                </p>
              </div>
            ) : searchNotFoundTerm ? (
              <div className="w-full bg-white rounded-3xl p-10 sm:p-12 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col items-center text-center">
                <AlertCircle className="w-10 h-10 text-amber-600 mb-4" />

                <h3 className="text-xl font-black text-gray-900 mb-2">
                  검색 결과가 없어요.
                </h3>

                <p className="text-sm text-gray-500 leading-relaxed">
                  '{searchNotFoundTerm}'에 해당하는
                  등록 용어나 규칙이 없어요.
                </p>
              </div>
            ) : isLoading ? (
              <div className="w-full min-h-[300px] bg-white rounded-3xl p-10 border border-gray-100 flex flex-col items-center justify-center gap-3">
                <LoaderCircle className="w-7 h-7 text-purple-600 animate-spin" />
                <p className="text-sm text-gray-500">
                  사전 카드 불러오는 중...
                </p>
              </div>
            ) : currentTermDetail ? (
              <TermDetailPanel
                key={currentTermDetail.id}
                term={currentTermDetail}
                onSelectRelatedTerm={handleSelectTerm}
              />
            ) : (
              <p className="text-sm text-gray-500">
                사전 데이터를 찾을 수 없어요.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
