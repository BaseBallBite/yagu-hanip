/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { HighlightItem } from '../../data/mockHighlightsData';
import { MockVideoPlayer } from './MockVideoPlayer';
import { 
  Sparkles, 
  HelpCircle, 
  ArrowRight, 
  BookOpen, 
  CheckCircle2, 
  GitCommit, 
  Layers,
  ArrowUpRight,
  TrendingUp,
  AlertCircle
} from 'lucide-react';

interface HighlightDetailPanelProps {
  scene: HighlightItem;
}

export function HighlightDetailPanel({ scene }: HighlightDetailPanelProps) {
  const [isLoadingAi, setIsLoadingAi] = useState<boolean>(false);
  const [hasAskedAi, setHasAskedAi] = useState<boolean>(true); // default true for vivid initial presentation
  const [activeChipToast, setActiveChipToast] = useState<string | null>(null);

  const handleAskImportance = () => {
    setIsLoadingAi(true);
    setTimeout(() => {
      setIsLoadingAi(false);
      setHasAskedAi(true);
    }, 450);
  };

  const handleChipClick = (term: string) => {
    setActiveChipToast(term);
    setTimeout(() => {
      setActiveChipToast(null);
    }, 2400);
  };

  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col gap-6 transition-all duration-300">
      
      {/* 1. Header: Selected Scene Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-gray-100">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-purple-700 bg-purple-100 px-2.5 py-0.5 rounded-full">
              {scene.inning}
            </span>
            <span className="text-xs font-bold text-gray-400">
              {scene.playerName} ({scene.playerTeam})
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
            {scene.playResult}
          </h2>
        </div>

        <div className="text-xs font-medium text-gray-500 bg-gray-50 px-3 py-1.5 rounded-xl border border-gray-100 self-start sm:self-auto">
          {scene.playShortSummary}
        </div>
      </div>

      {/* 2. Video Player Area */}
      <MockVideoPlayer scene={scene} />

      {/* 3. Scene Context: 장면 직전 상황 & 결과 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 직전 상황 */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-bold text-gray-500 mb-2">
            <span className="flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-gray-400" />
              이 장면 직전 상황
            </span>
            <span className="text-[11px] font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
              {scene.context.priorSituation.score}
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs sm:text-sm font-black text-gray-800">
            <span className="px-2 py-1 rounded bg-white border border-gray-200">
              {scene.context.priorSituation.inning}
            </span>
            <span className="px-2 py-1 rounded bg-white border border-gray-200">
              {scene.context.priorSituation.outs}
            </span>
            <span className="px-2 py-1 rounded bg-purple-100 text-purple-800 border border-purple-200">
              {scene.context.priorSituation.runners}
            </span>
          </div>
        </div>

        {/* 결과 */}
        <div className="p-4 rounded-2xl bg-purple-50/60 border border-purple-200/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-bold text-purple-700 mb-2">
            <span className="flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-purple-600" />
              결과
            </span>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
              {scene.context.resultSituation.scoredRunners}
            </span>
          </div>

          <div className="text-sm sm:text-base font-extrabold text-gray-900 flex items-center gap-2">
            <span>{scene.context.resultSituation.action}</span>
            <span className="text-purple-700 font-black">{scene.context.resultSituation.summary}</span>
          </div>
        </div>
      </div>

      {/* 4. AI Importance Button CTA */}
      <div className="pt-2">
        <button
          type="button"
          onClick={handleAskImportance}
          className="w-full py-4 px-6 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-black text-base sm:text-lg flex items-center justify-center gap-2.5 transition-all duration-200 cursor-pointer shadow-lg shadow-purple-600/25 hover:shadow-xl hover:shadow-purple-600/35 hover:scale-[1.01] active:scale-[0.99] group"
        >
          <span className="text-xl">🤔</span>
          <span>이 장면 왜 중요해?</span>
          <Sparkles className="w-5 h-5 text-yellow-300 ml-1 group-hover:rotate-12 transition-transform" />
        </button>
      </div>

      {/* 5. AI Explanation Display Panel */}
      {isLoadingAi ? (
        <div className="p-8 rounded-2xl bg-purple-50/50 border border-purple-100 flex flex-col items-center justify-center text-center animate-in fade-in">
          <div className="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center mb-3 animate-spin shadow-md">
            <Sparkles className="w-5 h-5" />
          </div>
          <span className="text-sm font-bold text-gray-900">
            경기 흐름과 맥락을 AI가 분석하고 있어요...
          </span>
        </div>
      ) : hasAskedAi ? (
        <div className="p-5 sm:p-6 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-700 text-white shadow-xl shadow-purple-900/15 border border-purple-400/30 animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-white/15">
            <div className="flex items-center gap-1.5 text-xs font-bold text-purple-100">
              <Sparkles className="w-4 h-4 text-yellow-300" />
              <span>야구한입 AI 경기 맥락 분석</span>
            </div>
            <span className="text-[10px] bg-white/20 px-2.5 py-0.5 rounded-full text-purple-100 font-semibold">
              핵심 모멘텀 해설
            </span>
          </div>

          <p className="text-sm sm:text-[15px] font-medium leading-relaxed text-purple-50 whitespace-pre-line">
            {scene.aiExplanation.summary}
          </p>

          {/* Related Terms Chips inside explanation */}
          <div className="mt-4 pt-3.5 border-t border-white/15">
            <span className="text-[11px] font-bold text-purple-200 block mb-2">관련 용어:</span>
            <div className="flex flex-wrap items-center gap-2">
              {scene.aiExplanation.keyTerms.map((term, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleChipClick(term)}
                  className="px-2.5 py-1 rounded-lg bg-white/20 hover:bg-white/30 text-white font-bold text-xs transition-colors cursor-pointer flex items-center gap-1 shadow-2xs"
                >
                  <span>{term}</span>
                  <ArrowUpRight className="w-3 h-3 text-purple-200" />
                </button>
              ))}
            </div>

            {/* Toast notice on term click */}
            {activeChipToast && (
              <div className="mt-2.5 text-xs text-white bg-black/40 px-3 py-1.5 rounded-lg flex items-center gap-1.5 animate-in fade-in">
                <CheckCircle2 className="w-3.5 h-3.5 text-yellow-300" />
                <span>{activeChipToast} 용어는 추후 야구사전 페이지와 연계됩니다.</span>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* 6. 이전 맥락 복원 영역 ("이 장면까지 어떻게 왔나요?") */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-50 border border-slate-200/80">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200">
          <div className="flex items-center gap-1.5 text-xs font-extrabold text-gray-800">
            <GitCommit className="w-4 h-4 text-purple-600" />
            <span>이 장면까지 어떻게 왔나요? (경기 맥락 타임라인)</span>
          </div>
          <span className="text-[10px] text-gray-400">데이터 기반 맥락 복원</span>
        </div>

        {/* 4 Steps Flow */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {scene.context.flowSteps.map((step, idx) => (
            <div 
              key={idx}
              className={`p-3 rounded-xl border text-xs font-bold flex items-center gap-2 ${
                idx === scene.context.flowSteps.length - 1
                  ? 'bg-purple-100/80 border-purple-300 text-purple-900 shadow-xs'
                  : 'bg-white border-gray-200/80 text-gray-700'
              }`}
            >
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 ${
                idx === scene.context.flowSteps.length - 1
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {idx + 1}
              </span>
              <span className="truncate">{step.replace(/^\d+\.\s*/, '')}</span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
