/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  Bookmark, 
  HelpCircle, 
  Trash2, 
  ChevronDown, 
  ChevronUp, 
  ArrowRight, 
  Sparkles, 
  ExternalLink,
  RotateCcw,
  BookOpen,
  Tv
} from 'lucide-react';
import { SavedQuestion, INITIAL_SAVED_QUESTIONS } from '../../data/mockMyData';

interface SavedQuestionsCardProps {
  questions: SavedQuestion[];
  onDeleteQuestion: (id: string) => void;
  onRestoreQuestions?: () => void;
  onNavigate: (path: string) => void;
}

export function SavedQuestionsCard({
  questions,
  onDeleteQuestion,
  onRestoreQuestions,
  onNavigate
}: SavedQuestionsCardProps) {
  // State for which question is expanded to show its answer preview (default: first question expanded)
  const [expandedId, setExpandedId] = useState<string | null>('sq-1');

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-base shadow-xs">
              <Bookmark className="w-4 h-4 text-purple-600 fill-purple-600" />
            </span>
            <h2 className="text-xl font-bold text-gray-900 tracking-tight">저장한 질문</h2>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-purple-100/70 text-purple-700">
              {questions.length}개
            </span>
          </div>
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            🤔 왜? 해설에서 저장한 질문을 다시 확인할 수 있어요.
          </p>
        </div>

        {questions.length === 0 && onRestoreQuestions && (
          <button
            type="button"
            onClick={onRestoreQuestions}
            className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 text-xs font-medium text-gray-600 hover:text-purple-700 transition cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>예시 다시 불러오기</span>
          </button>
        )}
      </div>

      {/* List or Empty State */}
      {questions.length === 0 ? (
        <div className="py-12 px-4 rounded-2xl bg-gray-50/70 border border-dashed border-gray-200 flex flex-col items-center justify-center text-center">
          <div className="w-14 h-14 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center mb-3">
            <HelpCircle className="w-7 h-7 stroke-[1.8]" />
          </div>
          <h3 className="text-base font-bold text-gray-900 mb-1">
            아직 저장한 질문이 없어요.
          </h3>
          <p className="text-xs sm:text-sm text-gray-500 max-w-sm leading-relaxed mb-4">
            🤔 왜? 해설이나 야구사전에서 궁금한 내용을 저장하면 여기에 모여요.
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onNavigate('/game')}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs transition shadow-xs cursor-pointer"
            >
              경기 해설 보러가기
            </button>
            <button
              type="button"
              onClick={() => onNavigate('/dictionary')}
              className="px-4 py-2 rounded-xl bg-white border border-gray-200 hover:border-purple-300 text-gray-700 hover:text-purple-700 font-semibold text-xs transition cursor-pointer"
            >
              야구사전 둘러보기
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {questions.map((item) => {
            const isExpanded = expandedId === item.id;
            const isDict = item.category === '야구사전';

            return (
              <div
                key={item.id}
                className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
                  isExpanded
                    ? 'border-purple-200 bg-purple-50/20 shadow-xs'
                    : 'border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50/40'
                }`}
              >
                {/* Question Item Header Row */}
                <div 
                  onClick={() => toggleExpand(item.id)}
                  className="p-4 sm:p-4.5 flex items-start justify-between gap-3 cursor-pointer select-none"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <span
                        className={`text-[11px] font-bold px-2 py-0.5 rounded-md border flex items-center gap-1 ${
                          isDict
                            ? 'bg-blue-50 text-blue-700 border-blue-100'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-100'
                        }`}
                      >
                        {isDict ? (
                          <BookOpen className="w-3 h-3 text-blue-600" />
                        ) : (
                          <Tv className="w-3 h-3 text-emerald-600" />
                        )}
                        <span>{item.category}</span>
                      </span>

                      <span className="text-[11px] text-gray-400 font-medium">
                        저장일 {item.savedDate}
                      </span>

                      {item.sourceContext && (
                        <span className="hidden sm:inline-block text-[11px] text-gray-400 truncate max-w-[200px]">
                          • {item.sourceContext}
                        </span>
                      )}
                    </div>

                    <h4 className="text-sm sm:text-base font-bold text-gray-900 group-hover:text-purple-700 transition-colors">
                      {item.question}
                    </h4>
                  </div>

                  {/* Actions on row */}
                  <div className="flex items-center gap-1 shrink-0 ml-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteQuestion(item.id);
                      }}
                      className="p-2 rounded-xl text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
                      title="저장 질문 삭제"
                      aria-label="저장한 질문 삭제"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>

                    <button
                      type="button"
                      className="p-2 rounded-xl text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition-colors cursor-pointer"
                      aria-label={isExpanded ? '답변 닫기' : '답변 보기'}
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-purple-600" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Expanded Answer Preview Panel */}
                {isExpanded && (
                  <div className="px-4 pb-4 pt-1 sm:px-5 sm:pb-4 border-t border-purple-100/60 bg-white/70">
                    <div className="rounded-xl p-3.5 bg-purple-50/40 border border-purple-100/60 mb-3">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-purple-700 mb-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                        <span>AI 요약 해설</span>
                      </div>
                      <p className="text-xs sm:text-sm text-gray-700 leading-relaxed">
                        {item.previewAnswer}
                      </p>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      {item.sourceContext ? (
                        <span className="text-[11px] text-gray-400 font-medium">
                          출처: {item.sourceContext}
                        </span>
                      ) : <span />}

                      <button
                        type="button"
                        onClick={() => onNavigate(item.targetPath)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs transition shadow-xs cursor-pointer"
                      >
                        <span>다시 보기</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
