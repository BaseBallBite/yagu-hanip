/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Target, RotateCcw, Sparkles } from 'lucide-react';

interface StrikeZoneVisualProps {
  className?: string;
}

export function StrikeZoneVisual({ className = '' }: StrikeZoneVisualProps) {
  const [pitchType, setPitchType] = useState<'strike' | 'ball'>('strike');
  const [replayKey, setReplayKey] = useState<number>(0);

  const handleReplay = () => {
    setReplayKey((prev) => prev + 1);
  };

  return (
    <div className={`w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col justify-between relative overflow-hidden transition-all duration-300 ${className}`}>
      {/* Top Header / Infographic status */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-600 animate-ping"></span>
          <span className="text-xs font-bold text-purple-700 tracking-wide uppercase">
            투구 판정 시각화
          </span>
        </div>
        
        {/* Toggle between strike or ball preview */}
        <div className="flex items-center bg-gray-100 p-0.5 rounded-xl text-xs font-semibold">
          <button
            onClick={() => { setPitchType('strike'); handleReplay(); }}
            className={`px-3 py-1 rounded-lg transition-all ${
              pitchType === 'strike' 
                ? 'bg-purple-600 text-white shadow-xs' 
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            스트라이크 예시
          </button>
          <button
            onClick={() => { setPitchType('ball'); handleReplay(); }}
            className={`px-3 py-1 rounded-lg transition-all ${
              pitchType === 'ball' 
                ? 'bg-purple-600 text-white shadow-xs' 
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            볼 예시
          </button>
        </div>
      </div>

      {/* Main Infographic Stage */}
      <div className="relative my-6 h-[280px] sm:h-[300px] w-full flex items-center justify-center bg-gradient-to-b from-purple-50/40 via-white to-gray-50/80 rounded-2xl border border-dashed border-purple-200/70 overflow-hidden px-4">
        
        {/* Pitcher Mound Indicator (Left Side) */}
        <div className="absolute left-4 top-1/2 -translate-y-1/2 flex flex-col items-center">
          <div className="w-12 h-12 rounded-2xl bg-white border border-gray-200 shadow-sm flex items-center justify-center text-lg">
            ⚾
          </div>
          <span className="text-[11px] font-bold text-gray-500 mt-1.5 whitespace-nowrap">투수 방향</span>
          <span className="text-[10px] text-gray-400">18.44m</span>
        </div>

        {/* Dynamic Trajectory Flight Path */}
        <svg 
          key={replayKey}
          className="absolute inset-0 w-full h-full pointer-events-none" 
          viewBox="0 0 400 240"
          preserveAspectRatio="none"
        >
          {pitchType === 'strike' ? (
            <path
              d="M 60 120 Q 200 90, 275 110"
              fill="none"
              stroke="#9333ea"
              strokeWidth="2.5"
              strokeDasharray="5 5"
              className="opacity-60"
            />
          ) : (
            <path
              d="M 60 120 Q 180 60, 315 50"
              fill="none"
              stroke="#64748b"
              strokeWidth="2.5"
              strokeDasharray="5 5"
              className="opacity-50"
            />
          )}
        </svg>

        {/* Animated Baseball */}
        <div 
          key={`ball-${replayKey}-${pitchType}`}
          className={`absolute z-20 flex items-center justify-center ${
            pitchType === 'strike' ? 'animate-pitch' : ''
          }`}
          style={{
            right: pitchType === 'strike' ? '30%' : '18%',
            top: pitchType === 'strike' ? '46%' : '20%',
            transition: 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
          }}
        >
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-white border-2 border-red-500 shadow-lg flex items-center justify-center shadow-purple-600/20">
              <span className="text-base select-none">⚾</span>
            </div>
            {pitchType === 'strike' && (
              <span className="absolute -top-6 -right-2 px-1.5 py-0.5 rounded bg-purple-600 text-white text-[10px] font-bold shadow-xs whitespace-nowrap animate-bounce">
                IN!
              </span>
            )}
            {pitchType === 'ball' && (
              <span className="absolute -top-6 -right-2 px-1.5 py-0.5 rounded bg-gray-600 text-white text-[10px] font-bold shadow-xs whitespace-nowrap">
                OUT!
              </span>
            )}
          </div>
        </div>

        {/* Right Target Area: Strike Zone & Home Plate */}
        <div className="absolute right-6 sm:right-10 flex flex-col items-center">
          
          {/* Strike Zone Title */}
          <div className="mb-2 flex items-center gap-1 text-[11px] font-bold text-purple-700 bg-purple-100/80 px-2.5 py-0.5 rounded-full">
            <Target className="w-3 h-3 text-purple-600" />
            <span>스트라이크 존</span>
          </div>

          {/* Strike Zone 3x3 Grid Box */}
          <div className={`w-32 h-40 sm:w-36 sm:h-44 rounded-xl border-2 transition-all duration-300 relative ${
            pitchType === 'strike' 
              ? 'border-purple-600 bg-purple-500/10 shadow-lg shadow-purple-600/15' 
              : 'border-gray-300 bg-white/70'
          }`}>
            {/* 3x3 Grid Lines */}
            <div className="grid grid-cols-3 grid-rows-3 w-full h-full divide-x divide-y divide-purple-200/50">
              {[...Array(9)].map((_, i) => (
                <div 
                  key={i} 
                  className={`flex items-center justify-center text-[10px] font-medium transition-colors ${
                    pitchType === 'strike' && i === 4 
                      ? 'bg-purple-200/40 text-purple-900 font-bold' 
                      : 'text-gray-300'
                  }`}
                >
                  {i === 4 && pitchType === 'strike' ? 'STRIKE' : ''}
                </div>
              ))}
            </div>

            {/* Height Label Helper */}
            <div className="absolute -left-6 top-1 text-[9px] font-semibold text-gray-400 [writing-mode:vertical-lr] rotate-180">
              타자 가슴 높이
            </div>
            <div className="absolute -left-6 bottom-1 text-[9px] font-semibold text-gray-400 [writing-mode:vertical-lr] rotate-180">
              타자 무릎 높이
            </div>
          </div>

          {/* Home Plate (Pentagon Base) */}
          <div className="mt-3 flex flex-col items-center">
            {/* 5-sided Home Plate polygon */}
            <div 
              className="w-16 h-8 bg-white border-2 border-gray-400 shadow-xs"
              style={{
                clipPath: 'polygon(0% 0%, 100% 0%, 100% 45%, 50% 100%, 0% 45%)'
              }}
              title="홈플레이트"
            />
            <span className="text-[10px] font-bold text-gray-500 mt-1">홈플레이트</span>
          </div>

        </div>

      </div>

      {/* Bottom Infographic Explanatory Note */}
      <div className="bg-gray-50 rounded-2xl p-3.5 border border-gray-100 flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-gray-600">
          <Sparkles className="w-4 h-4 text-purple-600 shrink-0" />
          <span>
            {pitchType === 'strike' 
              ? '공이 스트라이크 존 안으로 들어가면 스트라이크!' 
              : '존 밖으로 벗어난 공을 치지 않으면 볼(Ball)!'}
          </span>
        </div>
        <button
          onClick={handleReplay}
          className="text-purple-600 hover:text-purple-800 font-bold flex items-center gap-1 text-[11px] shrink-0 p-1 rounded-lg hover:bg-purple-50 transition"
        >
          <RotateCcw className="w-3 h-3" />
          <span>모션 재생</span>
        </button>
      </div>

    </div>
  );
}
