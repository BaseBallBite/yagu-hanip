
import { DICTIONARY_CARDS, TermDetail } from '../../data/mockDictionaryData';
import { BookOpen, Database, ArrowRight } from 'lucide-react';

interface TermDetailPanelProps {
  term: TermDetail;
  onSelectRelatedTerm: (cardId: string) => void;
}

export function TermDetailPanel({ term, onSelectRelatedTerm }: TermDetailPanelProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-gray-100">
        <div>
          <span className="text-xs font-bold text-purple-700 bg-purple-100 px-2.5 py-0.5 rounded-full">
            {term.category} {term.kind === 'rule' ? '규칙' : '용어'}
          </span>
          <h2 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight mt-2">
            {term.name}
          </h2>
        </div>
      </div>

      {/* 한 줄 핵심 요약 */}
      <div className="mt-4 p-4 rounded-2xl bg-gradient-to-r from-purple-50/90 via-purple-50/50 to-indigo-50/40 border border-purple-200/70 text-purple-950">
        <div className="text-[11px] font-bold text-purple-600 mb-1">
          한 줄 핵심 요약
        </div>
        <div className="text-base sm:text-lg font-black leading-snug">
          {term.oneLineSummary}
        </div>
      </div>

      {/* 초보자 눈높이 해설 */}
      <div className="mt-5 text-gray-700">
        <div className="text-xs font-bold text-gray-400 mb-2 flex items-center gap-1">
          <BookOpen className="w-3.5 h-3.5 text-purple-600" />
          초보자 눈높이 해설
        </div>
        <p className="text-sm sm:text-base leading-relaxed whitespace-pre-line text-gray-800 bg-slate-50/70 p-4 sm:p-5 rounded-2xl border border-slate-100">
          {term.beginnerExplanation}
        </p>
      </div>

      {/* 경기 상황 예시 */}
      {term.example && (
        <div className="mt-5 p-4 sm:p-5 rounded-2xl bg-white border border-gray-200/90">
          <div className="text-xs font-extrabold text-gray-700 mb-2">
            경기에서는 이렇게 나와요
          </div>
          <p className="text-sm leading-relaxed text-gray-800">
            {term.example}
          </p>
        </div>
      )}

      {/* 추가 설명 */}
      {term.more.length > 0 && (
        <div className="mt-5 p-4 rounded-2xl bg-purple-50/40 border border-purple-100">
          <div className="text-xs font-bold text-purple-700 mb-2">
            더 알아보기
          </div>
          {term.more.map((item, i) => (
            <p key={i} className="text-sm text-gray-700 leading-relaxed">
              {item}
            </p>
          ))}
        </div>
      )}

      {/* 관련 용어 및 규칙 */}
      {term.relatedTerms.length > 0 && (
        <div className="mt-5">
          <div className="text-xs font-bold text-gray-400 mb-2.5">
            같이 알아두면 좋은 용어·규칙
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {term.relatedTerms.map((id) => (
              <button
                key={id}
                type="button"
                onClick={() => onSelectRelatedTerm(id)}
                className="px-3 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold text-xs border border-purple-200/70 flex items-center gap-1"
              >
                {DICTIONARY_CARDS[id]?.title ?? id}
                <ArrowRight className="w-3 h-3" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 참고 출처 */}
      <div className="mt-5 p-4 rounded-2xl bg-slate-50 border border-slate-200/80">
        <div className="text-xs font-extrabold text-gray-700 flex items-center gap-1.5 mb-2 pb-1.5 border-b border-slate-200">
          <Database className="w-3.5 h-3.5 text-purple-600" />
          설명의 참고 출처
        </div>

        {term.sources.length ? (
          <ul className="space-y-2 text-xs text-gray-700">
            {term.sources.map((source, i) => (
              <li key={i} className="leading-relaxed">
                {source.referenceUrl ? (
                  <a
                    href={source.referenceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-700 underline"
                  >
                    {source.title}
                  </a>
                ) : (
                  source.title
                )}

                {source.sourceType !== '참고자료' && (
                  <span className="text-gray-500">
                    {' '}— {source.sourceType}
                  </span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-gray-500">
            등록된 출처가 없어요.
          </p>
        )}
      </div>
    </div>
  );
}
