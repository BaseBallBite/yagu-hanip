
import { useState, useEffect } from 'react';
import {
  DICTIONARY_CARDS,
  getTermDetailOrDefault,
  searchDictionary,
} from '../../data/mockDictionaryData';
import { DictionarySearchBar } from './DictionarySearchBar';
import { CategoryTermsNav } from './CategoryTermsNav';
import { TermDetailPanel } from './TermDetailPanel';
import { Sparkles, AlertCircle } from 'lucide-react';
import type { RecentSearchTerm } from '../../data/mockMyData';

const RECENT_TERMS_KEY = 'yagu_recent_terms';
const DICTIONARY_TARGET_KEY = 'yagu_dictionary_target';
const MAX_RECENT_TERMS = 4;

const initialCardId = DICTIONARY_CARDS['term.double_play']
  ? 'term.double_play'
  : Object.keys(DICTIONARY_CARDS)[0] ?? '';

function saveRecentTerm(id: string) {
  const card = DICTIONARY_CARDS[id];
  if (!card) return;

  const detail = getTermDetailOrDefault(id);

  const newTerm: RecentSearchTerm = {
    id,
    name: String(card.title ?? id),
    category: String(card.category ?? ''),
    description: String(detail?.description ?? ''),
  };

  try {
    const stored = localStorage.getItem(RECENT_TERMS_KEY);
    const parsed: unknown = stored ? JSON.parse(stored) : [];
    const previous: RecentSearchTerm[] = Array.isArray(parsed)
      ? parsed
      : [];

    // 같은 용어가 있으면 중복 제거 후 맨 앞으로 이동
    const updated = [
      newTerm,
      ...previous.filter((term) => term.id !== id),
    ].slice(0, MAX_RECENT_TERMS);

    localStorage.setItem(RECENT_TERMS_KEY, JSON.stringify(updated));
    window.dispatchEvent(new Event('yagu-recent-terms-updated'));
  } catch (error) {
    console.error('최근 야구 용어 저장 실패:', error);
  }
}

export function DictionaryPage() {
  const [selectedTermId, setSelectedTermId] = useState(initialCardId);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchNotFoundTerm, setSearchNotFoundTerm] = useState<string | null>(null);

  const currentTermDetail = getTermDetailOrDefault(selectedTermId);

  const handleSelectTerm = (id: string) => {
    if (!DICTIONARY_CARDS[id]) return;

    setSelectedTermId(id);
    setSearchNotFoundTerm(null);
    saveRecentTerm(id);
  };

  // MY에서 최근 용어를 클릭해 이동한 경우 해당 카드 열기
  useEffect(() => {
    const targetId = sessionStorage.getItem(DICTIONARY_TARGET_KEY);

    if (targetId) {
      sessionStorage.removeItem(DICTIONARY_TARGET_KEY);

      if (DICTIONARY_CARDS[targetId]) {
        handleSelectTerm(targetId);
      }
    }
  }, []);

  const handleSearchSubmit = (query: string) => {
    const trimmed = query.trim();

    if (!trimmed) {
      setSearchNotFoundTerm(null);
      return;
    }

    const matchedId = searchDictionary(trimmed);

    if (matchedId) {
      handleSelectTerm(matchedId);
    } else {
      setSearchNotFoundTerm(trimmed);
    }
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
            모르는 야구 용어와 규칙을 초보자 눈높이로 쉽게 확인해보세요.
          </p>

          <DictionarySearchBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSearchSubmit={handleSearchSubmit}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

          <div className="lg:col-span-5 w-full">
            <CategoryTermsNav
              selectedTermName={selectedTermId}
              onSelectTerm={handleSelectTerm}
            />
          </div>

          <div className="lg:col-span-7 w-full">
            {searchNotFoundTerm ? (
              <div className="w-full bg-white rounded-3xl p-10 sm:p-12 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col items-center justify-center text-center">
                <AlertCircle className="w-10 h-10 text-amber-600 mb-4" />

                <h3 className="text-xl font-black text-gray-900 mb-2">
                  검색 결과가 없어요.
                </h3>

                <p className="text-sm text-gray-500 leading-relaxed">
                  '{searchNotFoundTerm}'에 해당하는 등록 용어나 규칙이 없어요.
                  <br />
                  다른 이름이나 줄임말로 검색해 보세요.
                </p>
              </div>
            ) : currentTermDetail ? (
              <TermDetailPanel
                key={currentTermDetail.id}
                term={currentTermDetail}
                onSelectRelatedTerm={handleSelectTerm}
              />
            ) : (
              <p>사전 데이터를 찾을 수 없어요.</p>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
