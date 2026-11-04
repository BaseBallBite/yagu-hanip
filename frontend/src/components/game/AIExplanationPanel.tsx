/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  Sparkles, 
  HelpCircle, 
  BookOpen, 
  CheckCircle2, 
  Layers, 
  Database, 
  ArrowUpRight,
  Bot,
  RotateCcw
} from 'lucide-react';
import { AtBatPlay } from '../../data/mockGameData';

interface AIExplanationPanelProps {
  atBat: AtBatPlay;
  isLoading: boolean;
  hasAsked: boolean;
  onTriggerAsk: () => void;
  onSelectDictionaryTerm?: (term: string) => void;
}

export function AIExplanationPanel({
  atBat,
  isLoading,
  hasAsked,
  onTriggerAsk,
  onSelectDictionaryTerm,
}: AIExplanationPanelProps) {
  const [activeTermToast, setActiveTermToast] = useState<string | null>(null);

  const handleChipClick = (term: string) => {
    setActiveTermToast(term);
    if (onSelectDictionaryTerm) {
      onSelectDictionaryTerm(term);
    }
    setTimeout(() => {
      setActiveTermToast(null);
    }, 2400);
  };

  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col justify-between transition-all duration-300 min-h-[460px]">
      
      {/* Panel Top Header */}
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shadow-xs">
              <Bot className="w-4 h-4 text-purple-600" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black text-gray-900 tracking-tight flex items-center gap-1.5">
                <span>AI 경기 해설</span>
                <Sparkles className="w-4 h-4 text-purple-600" />
              </h2>
            </div>
          </div>

          <span className="text-[11px] font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100">
            초보자 맞춤형 해설
          </span>
        </div>

        {/* State 1: Loading State */}
        {isLoading && (
          <div className="py-16 flex flex-col items-center justify-center text-center animate-in fade-in duration-200">
            <div className="relative w-14 h-14 mb-4">
              <div className="absolute inset-0 rounded-2xl bg-purple-200 animate-ping opacity-60" />
              <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-purple-600/30">
                <Sparkles className="w-6 h-6 animate-spin" />
              </div>
            </div>
            <div className="text-base font-extrabold text-gray-900 mb-1">
              경기 데이터 분석 중...
            </div>
            <p className="text-xs text-gray-500 max-w-xs">
              현재 타석 투구 궤적과 KBO 공식 규칙을 바탕으로 초보자용 해설을 생성하고 있어요.
            </p>
          </div>
        )}

        {/* State 2: Default Prompt Before '🤔 왜?' Click */}
        {!isLoading && !hasAsked && (
          <div className="py-12 sm:py-16 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-3xl bg-purple-50 text-purple-600 flex items-center justify-center mb-4 text-2xl shadow-inner border border-purple-100">
              🤔
            </div>
            
            <h3 className="text-lg font-black text-gray-900 mb-2">
              궁금한 플레이에서 <span className="text-purple-600 font-black">🤔 왜?</span>를 눌러보세요.
            </h3>
            
            <p className="text-xs sm:text-sm text-gray-500 max-w-xs leading-relaxed mb-6">
              방금 던진 공이 왜 삼진인지, 주자가 왜 뛰었는지 AI가 1초 만에 알기 쉽게 설명해 드립니다.
            </p>

            {/* Quick Prompt Button to trigger */}
            <button
              type="button"
              onClick={onTriggerAsk}
              className="px-5 py-2.5 rounded-xl bg-purple-100 hover:bg-purple-200 text-purple-800 font-bold text-xs sm:text-sm transition-all duration-200 cursor-pointer flex items-center gap-2 hover:scale-105"
            >
              <Sparkles className="w-4 h-4 text-purple-600" />
              <span>방금 장면 해설해줘!</span>
            </button>
          </div>
        )}

        {/* State 3: Active AI Answer Display */}
        {!isLoading && hasAsked && (
          <div className="mt-5 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* AI Speech Bubble */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-700 text-white shadow-xl shadow-purple-900/15 border border-purple-400/30 relative">
              <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/15">
                <div className="flex items-center gap-1.5 text-xs font-bold text-purple-100">
                  <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                  <span>실시간 판정 요약 해설</span>
                </div>
                <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded-full text-purple-100 font-medium">
                  생성 완료
                </span>
              </div>

              {/* Explanation Text */}
              <p className="text-sm sm:text-[15px] font-medium leading-relaxed text-purple-50 whitespace-pre-line">
                {atBat.aiExplanation.summary}
              </p>
            </div>

            {/* Key Terms Chips Section */}
            <div className="mt-5 p-4 rounded-2xl bg-gray-50 border border-gray-100">
              <div className="flex items-center justify-between mb-2.5">
                <span className="text-xs font-bold text-gray-500 flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-purple-600" />
                  <span>핵심 용어</span>
                </span>
                <span className="text-[11px] text-gray-400">클릭하여 사전 연결</span>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {atBat.aiExplanation.keyTerms.map((term, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleChipClick(term)}
                    className="px-3 py-1.5 rounded-xl bg-white border border-gray-200 hover:border-purple-300 hover:bg-purple-50 text-gray-800 hover:text-purple-700 font-bold text-xs transition-all duration-150 cursor-pointer shadow-2xs hover:-translate-y-0.5 flex items-center gap-1 group"
                  >
                    <span>{term}</span>
                    <ArrowUpRight className="w-3 h-3 text-gray-400 group-hover:text-purple-600 transition-colors" />
                  </button>
                ))}
              </div>

              {/* Toast Feedback on chip click */}
              {activeTermToast && (
                <div className="mt-2.5 text-[11px] text-purple-700 bg-purple-100/90 px-3 py-1.5 rounded-lg flex items-center gap-1.5 animate-in fade-in duration-150 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-purple-600" />
                  <span>{activeTermToast} 단어는 추후 야구사전 페이지와 연동됩니다!</span>
                </div>
              )}
            </div>

            {/* AI Grounding / Evidence Section */}
            <div className="mt-4 p-4 rounded-2xl bg-slate-50/70 border border-slate-200/70">
              <div className="text-xs font-bold text-gray-700 flex items-center gap-1.5 mb-2">
                <Database className="w-3.5 h-3.5 text-purple-600" />
                <span>이 설명은 무엇을 보고 만들었나요?</span>
              </div>
              <ul className="space-y-1.5 text-xs text-gray-600">
                {atBat.aiExplanation.evidenceSources.map((source, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5 shrink-0" />
                    <span>{source}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Footer Info / Replay Hint */}
      <div className="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-400">
        <span>야구한입 멀티모달 해설 엔진</span>
        {hasAsked && !isLoading && (
          <button
            type="button"
            onClick={onTriggerAsk}
            className="text-purple-600 hover:text-purple-800 font-semibold flex items-center gap-1 transition"
          >
            <RotateCcw className="w-3 h-3" />
            <span>해설 다시 받기</span>
          </button>
        )}
      </div>

    </div>
  );
}
