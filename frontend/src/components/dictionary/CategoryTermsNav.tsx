import {
  DICTIONARY_CARDS,
  DICTIONARY_CATEGORIES,
  TOTAL_DICTIONARY_CARDS,
} from '../../data/mockDictionaryData';
import { Bookmark, Check } from 'lucide-react';

interface CategoryTermsNavProps {
  selectedTermName: string; // Card ID, not display name.
  onSelectTerm: (cardId: string) => void;
}

export function CategoryTermsNav({ selectedTermName, onSelectTerm }: CategoryTermsNavProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-5 sm:p-6 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col gap-6">
      <div className="flex items-center justify-between pb-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
            <Bookmark className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-black text-gray-900 tracking-tight">용어·규칙 탐색</h2>
            <p className="text-xs text-gray-400">카테고리별 야구 용어 및 규칙</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-100">
          {TOTAL_DICTIONARY_CARDS}개 카드
        </span>
      </div>
      <div className="space-y-6 max-h-[800px] overflow-y-auto pr-1">
        {DICTIONARY_CATEGORIES.map(cat => (
          <div key={cat.id}>
            <div className="flex items-center gap-1.5 mb-3">
              <span className="w-1.5 h-3.5 bg-purple-600 rounded-full" />
              <h3 className="text-xs sm:text-sm font-extrabold text-gray-700">{cat.name}</h3>
              <span className="text-[11px] text-gray-400 font-medium">({cat.terms.length})</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {cat.terms.map(id => {
                const card = DICTIONARY_CARDS[id];
                if (!card) return null;
                const isSelected = selectedTermName === id;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => onSelectTerm(id)}
                    className={`px-3 py-1.5 rounded-xl text-xs sm:text-[13px] font-bold transition-all duration-150 cursor-pointer flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-purple-600 text-white shadow-md shadow-purple-600/25 ring-2 ring-purple-300'
                        : 'bg-gray-50/80 hover:bg-purple-50 text-gray-700 hover:text-purple-700 border border-gray-200/80 hover:border-purple-300'
                    }`}
                  >
                    {card.title}
                    {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
