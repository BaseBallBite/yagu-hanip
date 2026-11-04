/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { AtBatPlay } from '../../data/mockGameData';
import { ChevronLeft, ChevronRight, History, Check } from 'lucide-react';

interface InningPlaysHistoryProps {
  atBats: AtBatPlay[];
  selectedAtBatId: string;
  onSelectAtBat: (atBatId: string) => void;
  onPrevAtBat: () => void;
  onNextAtBat: () => void;
  hasPrev: boolean;
  hasNext: boolean;
}

export function InningPlaysHistory({
  atBats,
  selectedAtBatId,
  onSelectAtBat,
  onPrevAtBat,
  onNextAtBat,
  hasPrev,
  hasNext,
}: InningPlaysHistoryProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-md shadow-purple-950/5 mt-6">
      
      {/* Header with Title and Navigation buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-100 mb-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
            <History className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h3 className="text-base sm:text-lg font-black text-gray-900 tracking-tight">
              9회말 · KIA 공격 타석 기록
            </h3>
            <p className="text-xs text-gray-400">
              타석을 선택하면 해당 장면의 투구 데이터와 AI 해설을 바로 확인할 수 있어요.
            </p>
          </div>
        </div>

        {/* Previous / Next At-Bat Buttons */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <button
            type="button"
            onClick={onPrevAtBat}
            disabled={!hasPrev}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
              hasPrev 
                ? 'bg-gray-100 hover:bg-purple-100 text-gray-700 hover:text-purple-700 active:scale-95' 
                : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>이전 타석</span>
          </button>

          <button
            type="button"
            onClick={onNextAtBat}
            disabled={!hasNext}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
              hasNext 
                ? 'bg-purple-600 hover:bg-purple-700 text-white shadow-xs active:scale-95' 
                : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }`}
          >
            <span>다음 타석</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Plays List / Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        {atBats.map((item, index) => {
          const isSelected = item.id === selectedAtBatId;

          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectAtBat(item.id)}
              className={`p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between relative group ${
                isSelected
                  ? 'bg-purple-50/70 border-2 border-purple-600 ring-2 ring-purple-200/50 shadow-md shadow-purple-600/10 -translate-y-0.5'
                  : 'bg-white border-gray-200/80 hover:border-purple-300 hover:shadow-xs hover:-translate-y-0.5'
              }`}
            >
              {/* Active Indicator Top Tag */}
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-bold text-gray-400">
                  {index + 1}번째 타자
                </span>
                {isSelected ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full">
                    <Check className="w-3 h-3 stroke-[3]" />
                    조회 중
                  </span>
                ) : (
                  <span className="text-[10px] text-gray-400 font-mono">
                    {item.pitchCountText}
                  </span>
                )}
              </div>

              {/* Batter Name */}
              <div className="text-base font-extrabold text-gray-900 group-hover:text-purple-700 transition-colors">
                {item.batterName}
              </div>

              {/* Play Result */}
              <div className="mt-1 flex items-center justify-between text-xs font-semibold">
                <span className={isSelected ? 'text-purple-900 font-bold' : 'text-gray-600'}>
                  {item.resultText}
                </span>
                <span className="text-gray-400 font-medium text-[11px]">
                  {item.currentPitch.speedKm}km/h
                </span>
              </div>
            </button>
          );
        })}
      </div>

    </div>
  );
}
