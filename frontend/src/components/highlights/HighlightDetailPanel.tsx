/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useEffect, useState } from 'react';
import type { HighlightItem } from '../../data/mockHighlightsData';
import { MockVideoPlayer } from './MockVideoPlayer';
import { AlertCircle, GitCommit, TrendingUp } from 'lucide-react';

interface HighlightDetailPanelProps {
  scene: HighlightItem;
}

export function HighlightDetailPanel({ scene }: HighlightDetailPanelProps) {
  const [showResult, setShowResult] = useState(false);
  useEffect(() => setShowResult(false), [scene.id]);
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
              {scene.playerName} ({scene.playerTeam}{scene.playerRole ? ` ${scene.playerRole}` : ''})
            </span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
            현재 장면
          </h2>
        </div>

        <div className="text-xs font-medium text-gray-500 bg-gray-50 px-3 py-1.5 rounded-xl border border-gray-100 self-start sm:self-auto">
          결과는 아래에서 선택해 확인할 수 있어요
        </div>
      </div>

      {/* 2. Video Player Area */}
      <MockVideoPlayer scene={scene} />

      {scene.status !== '확인 불가' && (<>
      {/* 3. Scene Context: 장면 직전 상황 & 결과 요약 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 직전 상황 */}
        <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs font-bold text-gray-500 mb-2">
            <span className="flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-gray-400" />
              이 장면 직전 상황
            </span>
            <div className="flex flex-wrap items-center gap-2">
              {scene.status && scene.status !== '확인 불가' && <span className={`rounded-full px-2 py-0.5 text-[11px] font-black ${scene.status === '추정' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-700'}`}>{scene.status === '추정' ? '추정' : '확인됨'}</span>}
              <span className="text-[11px] font-mono font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">{scene.context.priorSituation.score}</span>
            </div>
          </div>

          {scene.status === '추정' && <p className="mb-3 text-[11px] leading-relaxed text-amber-800">전광판이 확인되지 않아 앞 장면을 기준으로 추정한 정보입니다. 실제와 다를 수 있어요.</p>}
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

        {/* 타석 결과는 영상보다 먼저 공개하지 않습니다. */}
        <div className="p-4 rounded-2xl bg-purple-50/60 border border-purple-200/80 flex flex-col justify-between">
          <button type="button" onClick={() => setShowResult(value => !value)} className="mb-2 rounded-lg border border-purple-200 bg-white px-3 py-1.5 text-xs font-extrabold text-purple-700">{showResult ? '결과 접기' : '결과 보기'}</button>
          {showResult && (<>
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
          </>)}
        </div>
      </div>

      {/* 실제 데이터 기반 타임라인은 장면 API와 연동 후 표시합니다. */}
      {/* 6. 이전 맥락 복원 영역 ("이 장면까지 어떻게 왔나요?") */}
      <div className="p-4 sm:p-5 rounded-2xl bg-slate-50 border border-slate-200/80">
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200">
          <div className="flex items-center gap-1.5 text-xs font-extrabold text-gray-800">
            <GitCommit className="w-4 h-4 text-purple-600" />
            <span>이 장면까지 어떻게 왔나요? (경기 상황 타임라인)</span>
          </div>
          <span className="text-[10px] text-gray-400">현재는 시안용 데이터 · 실제 장면 API 연동 예정</span>
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

      </>)}
    </div>
  );
}
