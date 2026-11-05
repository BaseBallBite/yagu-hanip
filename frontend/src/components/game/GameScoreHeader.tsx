/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { CurrentGameSummary } from '../../data/mockGameData';
import { Calendar, MapPin, Radio } from 'lucide-react';

interface GameScoreHeaderProps {
  summary: CurrentGameSummary;
}

export function GameScoreHeader({ summary }: GameScoreHeaderProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-5 sm:p-6 border border-gray-100 shadow-md shadow-purple-950/5 mb-6">
      <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
        
        {/* Left: Live Match Indicator & Venue */}
        <div className="flex items-center gap-3 w-full lg:w-auto justify-between lg:justify-start">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
            </span>
            <span className="text-xs font-black text-red-600 tracking-wider">LIVE</span>
            <span className="text-xs font-bold text-gray-400">|</span>
            <span className="text-xs font-semibold text-gray-600 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-gray-400" />
              {summary.date}
            </span>
          </div>

          <div className="text-xs font-medium text-gray-500 flex items-center gap-1 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-100">
            <MapPin className="w-3 h-3 text-purple-600" />
            <span>{summary.stadium}</span>
          </div>
        </div>

        {/* Center: Main Scoreboard Display */}
        <div className="flex items-center gap-6 sm:gap-10">
          {/* Home Team: KT */}
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-[#1F2024] text-white font-black text-sm flex items-center justify-center shadow-xs">
              {summary.homeTeam}
            </div>
            <div>
              <div className="text-[11px] font-semibold text-gray-400">HOME</div>
              <div className="text-lg font-black text-gray-900">{summary.homeTeam} 위즈</div>
            </div>
          </div>

          {/* Scores & Inning */}
          <div className="text-center px-2">
            <div className="text-3xl sm:text-4xl font-black tracking-wider text-gray-900 flex items-center gap-3">
              <span className="text-purple-600 font-mono">{summary.homeScore}</span>
              <span className="text-gray-300 font-light">:</span>
              <span className="text-gray-900 font-mono">{summary.awayScore}</span>
            </div>
            <div className="mt-1 inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs font-black">
              <span>{summary.inning}</span>
            </div>
          </div>

          {/* Away Team: KIA */}
          <div className="flex items-center gap-3 flex-row-reverse text-right">
            <div className="w-11 h-11 rounded-2xl bg-[#C3042D] text-white font-black text-sm flex items-center justify-center shadow-xs">
              {summary.awayTeam}
            </div>
            <div>
              <div className="text-[11px] font-semibold text-gray-400">AWAY</div>
              <div className="text-lg font-black text-gray-900">{summary.awayTeam} 타이거즈</div>
            </div>
          </div>
        </div>

        {/* Right: Out Count + Runner Diamond Visualization */}
        <div className="flex items-center gap-6 bg-slate-50 p-3 sm:px-4 sm:py-2.5 rounded-2xl border border-gray-100 w-full lg:w-auto justify-around lg:justify-end">
          
          {/* Out Count */}
          <div className="flex flex-col items-center">
            <span className="text-[11px] font-bold text-gray-500 mb-1">아웃 카운트</span>
            <div className="flex items-center gap-1.5" title={`${summary.outsCount}아웃`}>
              {/* Dot 1 */}
              <span className={`w-3 h-3 rounded-full ${summary.outsCount >= 1 ? 'bg-red-500 shadow-xs' : 'bg-gray-300'}`} />
              {/* Dot 2 */}
              <span className={`w-3 h-3 rounded-full ${summary.outsCount >= 2 ? 'bg-red-500 shadow-xs' : 'bg-gray-300'}`} />
              {/* Dot 3 */}
              <span className={`w-3 h-3 rounded-full ${summary.outsCount >= 3 ? 'bg-red-500 shadow-xs' : 'bg-gray-300'}`} />
            </div>
            <span className="text-[10px] font-bold text-red-600 mt-1">{summary.outsCount} 아웃</span>
          </div>

          {/* Vertical divider */}
          <div className="w-px h-8 bg-gray-200" />

          {/* Runner Diamond Visualization */}
          <div className="flex items-center gap-3">
            <div className="flex flex-col items-center">
              <span className="text-[11px] font-bold text-gray-500 mb-1">주자 상황</span>
              <div className="relative w-8 h-8 select-none">
                {/* 2nd Base (Top) */}
                <div 
                  className={`absolute top-0 left-1/2 -translate-x-1/2 w-2.5 h-2.5 rotate-45 border ${
                    summary.runners.second 
                      ? 'bg-purple-600 border-purple-700 shadow-xs' 
                      : 'bg-white border-gray-300'
                  }`} 
                  title="2루 주자 없음" 
                />
                {/* 3rd Base (Left) */}
                <div 
                  className={`absolute top-1/2 left-0 -translate-y-1/2 w-2.5 h-2.5 rotate-45 border ${
                    summary.runners.third 
                      ? 'bg-purple-600 border-purple-700 shadow-xs' 
                      : 'bg-white border-gray-300'
                  }`} 
                  title="3루 주자 없음" 
                />
                {/* 1st Base (Right) -> Active */}
                <div 
                  className={`absolute top-1/2 right-0 -translate-y-1/2 w-2.5 h-2.5 rotate-45 border ${
                    summary.runners.first 
                      ? 'bg-purple-600 border-purple-700 shadow-xs animate-pulse ring-2 ring-purple-300' 
                      : 'bg-white border-gray-300'
                  }`} 
                  title="1루 주자 있음" 
                />
                {/* Home Plate (Bottom) */}
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-400 rotate-45" title="홈플레이트" />
              </div>
            </div>

            <div className="flex flex-col text-left">
              <span className="text-xs font-black text-purple-700">1루 주자</span>
              <span className="text-[10px] text-gray-500">진루 중</span>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
