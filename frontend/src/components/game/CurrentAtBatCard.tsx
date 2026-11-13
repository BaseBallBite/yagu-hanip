/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { AtBatPlay } from '../../data/mockGameData';
import { StrikeZoneMini } from './StrikeZoneMini';
import { 
  Zap, 
  HelpCircle, 
  ChevronRight, 
  Sparkles, 
  Layers, 
  ListOrdered,
  Eye
} from 'lucide-react';

interface CurrentAtBatCardProps {
  atBat: AtBatPlay;
  onAskWhy: () => void;
  isAiExplaining: boolean;
}

export function CurrentAtBatCard({
  atBat,
  onAskWhy,
  isAiExplaining,
}: CurrentAtBatCardProps) {
  const [showPitchDetail, setShowPitchDetail] = useState<boolean>(false);

  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col justify-between transition-all duration-300">
      
      {/* Card Header: Live Tag & Matchup */}
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
            </span>
            <span className="text-xs font-black text-red-600 tracking-wider">LIVE 지금 타석</span>
          </div>

          <div className="text-xs font-semibold px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-100">
            {atBat.pitchCountText} 승부
          </div>
        </div>

        {/* Batter vs Pitcher Matchup */}
        <div className="mt-4 p-4 rounded-2xl bg-gradient-to-br from-gray-50 to-purple-50/20 border border-gray-100 flex items-center justify-between">
          {/* Batter */}
          <div>
            <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
              현재 타자 ({atBat.batterTeam})
            </div>
            <div className="text-xl sm:text-2xl font-black text-gray-900 flex items-baseline gap-2">
              <span>{atBat.batterName}</span>
              <span className="text-xs font-semibold text-gray-500">{atBat.batterPosition}</span>
            </div>
          </div>

          {/* VS Tag */}
          <div className="px-3 py-1 rounded-xl bg-gray-100 text-gray-500 text-xs font-black">
            VS
          </div>

          {/* Pitcher */}
          <div className="text-right">
            <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
              상대 투수 ({atBat.pitcherTeam})
            </div>
            <div className="text-xl sm:text-2xl font-black text-gray-900 flex items-baseline gap-2 justify-end">
              <span className="text-xs font-semibold text-gray-500">마무리</span>
              <span>{atBat.pitcherName}</span>
            </div>
          </div>
        </div>

        {/* Center: Large Pitch Information & Count */}
        <div className="mt-5 p-5 rounded-2xl bg-purple-50/50 border border-purple-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="inline-flex items-center gap-1 text-xs font-bold text-purple-700 bg-purple-100 px-2.5 py-0.5 rounded-full">
                <Zap className="w-3 h-3 text-purple-600" />
                결정구 투구
              </span>
              <span className="text-xs font-semibold text-gray-500">
                볼 {atBat.balls} · 스트라이크 {atBat.strikes}
              </span>
            </div>

            {/* Pitch Type & Speed */}
            <div className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight flex items-baseline gap-2.5">
              <span>{atBat.currentPitch.pitchNumber}구 {atBat.currentPitch.pitchType}</span>
              <span className="text-base sm:text-lg font-bold text-purple-600">
                {atBat.currentPitch.speedKm}km/h
              </span>
            </div>

            {/* Outcome description */}
            <div className="text-sm font-semibold text-gray-600 mt-1">
              {atBat.currentPitch.result} · {atBat.currentPitch.speedKm}km/h
            </div>
          </div>

          {/* Result Badge */}
          <div className="px-4 py-2.5 rounded-2xl bg-white border border-purple-200 shadow-sm text-purple-700 font-black text-base sm:text-lg whitespace-nowrap self-stretch sm:self-auto text-center">
            {atBat.resultBadge}
          </div>
        </div>

        {/* Pitch Visualization Area */}
        <div className="mt-5">
          <StrikeZoneMini
            currentPitch={atBat.currentPitch}
            pitchesHistory={atBat.pitchesHistory}
            showAllPitches={showPitchDetail}
          />
        </div>

        {/* Detailed Pitches Breakdown (if '투구 자세히' toggled) */}
        {showPitchDetail && (
          <div className="mt-4 p-4 rounded-2xl bg-white border border-gray-200 shadow-xs animate-in fade-in duration-200">
            <div className="text-xs font-bold text-gray-500 mb-2.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <ListOrdered className="w-3.5 h-3.5 text-purple-600" />
                이 타석 전체 투구 기록 ({atBat.pitchesHistory.length}구)
              </span>
              <span className="text-[11px] text-gray-400">구종 / 구속 / 결과</span>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {atBat.pitchesHistory.map((p) => (
                <div 
                  key={p.pitchNumber}
                  className={`p-2.5 rounded-xl border text-xs ${
                    p.pitchNumber === atBat.currentPitch.pitchNumber 
                      ? 'bg-purple-50 border-purple-300 font-bold text-purple-900' 
                      : 'bg-gray-50/80 border-gray-200/80 text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono font-bold">
                    <span>{p.pitchNumber}구 {p.pitchType}</span>
                    <span className="text-[11px] text-gray-500">{p.speedKm}km</span>
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5">{p.result}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Card Action Buttons (Secondary: 투구 자세히, Primary: 🤔 왜?) */}
      <div className="mt-6 pt-5 border-t border-gray-100 flex flex-col sm:flex-row items-center gap-3">
        {/* Secondary: 투구 자세히 */}
        <button
          type="button"
          onClick={() => setShowPitchDetail(!showPitchDetail)}
          className={`w-full sm:w-auto px-5 py-3.5 rounded-2xl border font-bold text-sm transition-all duration-200 cursor-pointer flex items-center justify-center gap-2 ${
            showPitchDetail 
              ? 'bg-purple-50 border-purple-300 text-purple-700 shadow-xs' 
              : 'border-gray-200 hover:border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          <Eye className="w-4 h-4 text-purple-600" />
          <span>{showPitchDetail ? '투구 접기' : '투구 자세히'}</span>
        </button>

        {/* Primary CTA: 한입만 🍙 */}
        <button
          type="button"
          onClick={onAskWhy}
          className={`w-full flex-1 py-4 px-6 rounded-2xl font-black text-base sm:text-lg flex items-center justify-center gap-2.5 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-xl active:scale-[0.98] ${
            isAiExplaining
              ? 'bg-purple-700 text-white shadow-purple-700/25 ring-2 ring-purple-300'
              : 'bg-purple-600 hover:bg-purple-700 text-white shadow-purple-600/30 animate-gentle-pulse hover:scale-[1.01]'
          }`}
        >

<span>한입만!</span>
<span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-white/20 ml-1">
  이 장면 쉽게 이해하기
</span>
          <Sparkles className="w-4 h-4 ml-auto text-yellow-300 animate-pulse" />
        </button>
      </div>

    </div>
  );
}
