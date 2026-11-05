/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Target, Info } from 'lucide-react';
import { PitchDetail } from '../../data/mockGameData';

interface StrikeZoneMiniProps {
  currentPitch: PitchDetail;
  pitchesHistory?: PitchDetail[];
  showAllPitches?: boolean;
}

export function StrikeZoneMini({ 
  currentPitch, 
  pitchesHistory = [], 
  showAllPitches = false 
}: StrikeZoneMiniProps) {
  const [hoveredPitch, setHoveredPitch] = useState<number | null>(null);

  // Home plate dimension aspect ratio and clean 3x3 strike grid
  return (
    <div className="w-full bg-slate-50/80 rounded-2xl p-4 border border-gray-100 flex flex-col items-center">
      
      {/* Zone Header Info */}
      <div className="w-full flex items-center justify-between text-xs text-gray-500 mb-3 px-1">
        <div className="flex items-center gap-1.5 font-bold text-gray-700">
          <Target className="w-3.5 h-3.5 text-purple-600" />
          <span>투구 탄착점 시각화</span>
        </div>
        <span className="text-[11px] font-semibold text-purple-700 bg-purple-100/70 px-2 py-0.5 rounded-md">
          포수 시점
        </span>
      </div>

      {/* Main Strike Zone Frame */}
      <div className="relative w-44 h-52 sm:w-48 sm:h-56 bg-white rounded-xl border border-dashed border-gray-300 shadow-inner flex items-center justify-center p-3 select-none">
        
        {/* Out-of-zone boundary background indicator */}
        <div className="absolute inset-2 border border-dashed border-gray-200/80 rounded pointer-events-none" />

        {/* The Official Strike Zone Box (centered rectangle) */}
        <div className="relative w-28 h-36 sm:w-32 sm:h-40 border-2 border-purple-500/80 bg-purple-500/5 shadow-xs rounded-md">
          {/* 3x3 Grid Lines */}
          <div className="w-full h-full grid grid-cols-3 grid-rows-3 divide-x divide-y divide-purple-200/60">
            {Array.from({ length: 9 }).map((_, i) => (
              <div key={i} className="flex items-center justify-center" />
            ))}
          </div>

          {/* Label indicators */}
          <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[9px] font-bold text-gray-400">
            가슴 높이
          </span>
          <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[9px] font-bold text-gray-400">
            무릎 높이
          </span>
        </div>

        {/* Pitch Flight Trajectory Line (Simple dashed curve to the landing spot) */}
        <svg 
          key={`traj-${currentPitch.pitchNumber}`}
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 100 100" 
          preserveAspectRatio="none"
        >
          <path
            d={`M 50 10 Q ${50 + (currentPitch.zoneLocation.x - 50) * 0.4} 45, ${currentPitch.zoneLocation.x} ${currentPitch.zoneLocation.y}`}
            fill="none"
            stroke="#9333ea"
            strokeWidth="1.8"
            strokeDasharray="3 3"
            className="opacity-70"
          />
        </svg>

        {/* History Pitches (if toggled) */}
        {showAllPitches && pitchesHistory.map((p) => {
          if (p.pitchNumber === currentPitch.pitchNumber) return null;
          return (
            <div
              key={p.pitchNumber}
              style={{
                left: `${p.zoneLocation.x}%`,
                top: `${p.zoneLocation.y}%`,
              }}
              className="absolute -translate-x-1/2 -translate-y-1/2 w-5 h-5 rounded-full bg-gray-200 border border-gray-400 text-[10px] font-black text-gray-600 flex items-center justify-center cursor-pointer opacity-75 hover:opacity-100 hover:scale-125 transition-all shadow-xs"
              title={`${p.pitchNumber}구 ${p.pitchType} (${p.speedKm}km/h) - ${p.result}`}
            >
              {p.pitchNumber}
            </div>
          );
        })}

        {/* Current Active Pitch Dot (With scale/fade-in animation) */}
        <div
          key={`pitch-dot-${currentPitch.pitchNumber}-${currentPitch.zoneLocation.x}`}
          style={{
            left: `${currentPitch.zoneLocation.x}%`,
            top: `${currentPitch.zoneLocation.y}%`,
          }}
          onMouseEnter={() => setHoveredPitch(currentPitch.pitchNumber)}
          onMouseLeave={() => setHoveredPitch(null)}
          className="absolute -translate-x-1/2 -translate-y-1/2 z-20 group cursor-pointer animate-in zoom-in-50 fade-in duration-300"
        >
          {/* Ripple Pulse */}
          <span className="absolute -inset-1 rounded-full bg-purple-500 opacity-60 animate-ping" />
          
          {/* Main Baseball Pin */}
          <div className="relative w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-purple-600 border-2 border-white shadow-md text-white flex items-center justify-center text-xs font-black">
            <span>{currentPitch.pitchNumber}</span>
          </div>

          {/* Tooltip on pitch */}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:flex flex-col items-center pointer-events-none whitespace-nowrap z-30">
            <div className="bg-gray-900 text-white text-[10px] font-bold px-2 py-1 rounded shadow-lg">
              {currentPitch.pitchNumber}구 {currentPitch.pitchType} ({currentPitch.speedKm}km/h)
            </div>
            <div className="w-1.5 h-1.5 bg-gray-900 rotate-45 -mt-0.5" />
          </div>
        </div>

        {/* Home Plate Symbol at the bottom */}
        <div 
          className="absolute bottom-1 w-12 h-4 bg-gray-200 border border-gray-400 opacity-60"
          style={{
            clipPath: 'polygon(0% 0%, 100% 0%, 100% 40%, 50% 100%, 0% 40%)'
          }}
          title="홈플레이트"
        />

      </div>

      {/* Caption Below Strike Zone */}
      <div className="mt-3 text-center">
        <span className="text-xs font-bold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100">
          {currentPitch.pitchNumber}구 {currentPitch.pitchType} · {currentPitch.description}
        </span>
      </div>

    </div>
  );
}
