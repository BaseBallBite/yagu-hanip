import { useEffect, useRef, useState } from 'react';
import { DICTIONARY_CARDS, DICTIONARY_CATEGORIES, TOTAL_DICTIONARY_CARDS } from '../../data/mockDictionaryData';
import { Bookmark, Check, ChevronDown, ChevronRight } from 'lucide-react';

interface Props {
  selectedTermName: string;
  onSelectTerm: (id: string) => void;
  searchMatchedIds?: string[];
}
const ESSENTIAL = ['볼넷','삼진','도루','병살','안타','홈런','스트라이크','파울','아웃','타점'];

export function CategoryTermsNav({ selectedTermName, onSelectTerm, searchMatchedIds = [] }: Props) {
  const [kind, setKind] = useState<'rule'|'term'>('rule');
  const [openCategory, setOpenCategory] = useState<string | null>(null);
  const selectedRef = useRef<HTMLButtonElement | null>(null);
  const selectedCard = DICTIONARY_CARDS[selectedTermName];
  useEffect(() => {
    if (!selectedCard) return;
    setKind(selectedCard.kind);
    setOpenCategory(`${selectedCard.kind}:${selectedCard.category}`);
  }, [selectedTermName]);
  useEffect(() => {
    if (selectedRef.current) selectedRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [selectedTermName, kind, openCategory]);
  const essentialIds = ESSENTIAL.flatMap(title => {
    const matched = Object.values(DICTIONARY_CARDS).find(card => card.title === title);
    return matched ? [matched.id] : [];
  });
  const matched = new Set(searchMatchedIds);
  const groups = DICTIONARY_CATEGORIES.filter(c => c.id.startsWith(`${kind}:`));
  return <div className="w-full rounded-3xl border border-gray-100 bg-white p-5 shadow-xl shadow-purple-950/5 sm:p-6">
    <div className="mb-4 flex items-center justify-between border-b border-gray-100 pb-4">
      <div className="flex items-center gap-2"><Bookmark className="h-4 w-4 text-purple-600"/><div><h2 className="text-base font-black">용어·규칙 탐색</h2><p className="text-xs text-gray-400">필요한 분류만 펼쳐서 살펴보세요</p></div></div>
      <span className="rounded-full bg-purple-50 px-2 py-1 text-xs font-bold text-purple-700">{TOTAL_DICTIONARY_CARDS}개</span>
    </div>
    {searchMatchedIds.length === 0 && <section className="mb-4 rounded-2xl border border-purple-100 bg-purple-50/50 p-3">
      <p className="mb-2 text-xs font-black text-purple-800">처음이라면 · 초보자 필수 용어</p>
      <div className="flex flex-wrap gap-1.5">{essentialIds.map(id => <button type="button" key={id} onClick={() => onSelectTerm(id)} className={`rounded-lg border px-2 py-1 text-xs font-semibold ${id === selectedTermName ? 'border-purple-600 bg-purple-600 text-white' : 'border-purple-100 bg-white text-gray-700 hover:bg-purple-100'}`}>{DICTIONARY_CARDS[id].title}</button>)}</div>
    </section>}
    <div className="mb-4 grid grid-cols-2 gap-2" role="tablist" aria-label="야구사전 종류">
      {(['rule','term'] as const).map(value => <button key={value} type="button" role="tab" aria-selected={kind === value} onClick={() => {setKind(value);setOpenCategory(null);}} className={`rounded-xl px-3 py-2 text-sm font-bold ${kind === value ? 'bg-purple-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-purple-50'}`}>{value === 'rule' ? '규칙' : '용어'}</button>)}
    </div>
    <div className="max-h-[650px] space-y-2 overflow-y-auto pr-1">
      {groups.map(group => {
        const visibleIds = searchMatchedIds.length ? group.terms.filter(id => matched.has(id)) : group.terms;
        if (!visibleIds.length) return null;
        const opened = openCategory === group.id || (searchMatchedIds.length > 0);
        return <div key={group.id} className="rounded-xl border border-gray-200">
          <button type="button" onClick={() => setOpenCategory(opened && searchMatchedIds.length === 0 ? null : group.id)} className="flex w-full items-center justify-between gap-2 rounded-xl px-3 py-3 text-left hover:bg-purple-50" aria-expanded={opened}>
            <span className="text-xs font-extrabold text-gray-800">{group.name.replace(/^(규칙|용어) · /, '')} <span className="text-gray-400">({visibleIds.length})</span></span>
            {opened ? <ChevronDown className="h-4 w-4 text-purple-600"/> : <ChevronRight className="h-4 w-4 text-gray-400"/>}
          </button>
          {opened && <div className="flex flex-wrap gap-1.5 border-t border-gray-100 p-3">{visibleIds.map(id => {
            const card = DICTIONARY_CARDS[id]; if (!card) return null;
            const isSelected = selectedTermName === id;
            return <button ref={isSelected ? selectedRef : undefined} type="button" key={id} onClick={() => onSelectTerm(id)} className={`flex items-center gap-1 rounded-lg border px-2.5 py-1.5 text-xs font-semibold ${isSelected ? 'border-purple-600 bg-purple-600 text-white' : 'border-gray-200 bg-gray-50 text-gray-700 hover:border-purple-300 hover:bg-purple-50'}`}>{card.title}{isSelected && <Check className="h-3 w-3"/>}</button>;
          })}</div>}
        </div>;
      })}
      {groups.every(group => searchMatchedIds.length && !group.terms.some(id => matched.has(id))) && <p className="py-5 text-center text-xs text-gray-400">이 종류에 해당하는 검색 결과가 없어요.</p>}
    </div>
  </div>;
}
