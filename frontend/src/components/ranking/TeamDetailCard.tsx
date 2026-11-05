/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { TeamStanding } from '../../data/mockRankingData';
import { 
  Trophy, 
  TrendingUp, 
  Calendar, 
  MapPin, 
  ArrowRight, 
  Sparkles, 
  Heart,
  Flame,
  Tv
} from 'lucide-react';

interface TeamDetailCardProps {
  team: TeamStanding;
  isFavorite: boolean;
  onNavigateToGame: () => void;
}

export function TeamDetailCard({
  team,
  isFavorite,
  onNavigateToGame,
}: TeamDetailCardProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col justify-between transition-all duration-300">
      
      {/* Top Header & Team Identity */}
      <div>
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <span className="text-xs font-bold text-gray-400">
            구단 상세 분석
          </span>
          {isFavorite && (
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-purple-700 bg-purple-50 px-2.5 py-0.5 rounded-full border border-purple-100">
              <Heart className="w-3 h-3 fill-purple-600 text-purple-600" />
              <span>나의 응원 팀</span>
            </span>
          )}
        </div>

        {/* Team Banner */}
        <div className="mt-4 p-5 rounded-2xl flex items-center gap-4 border" style={{
          backgroundColor: team.lightBg,
          borderColor: `${team.primaryColor}30`,
        }}>
          {/* Logo / Initial Badge */}
          <div 
            className="w-14 h-14 rounded-2xl flex items-center justify-center font-black text-white text-base shadow-md shrink-0"
            style={{ backgroundColor: team.primaryColor }}
          >
            <span>{team.initial}</span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-gray-500">{team.stadium}</span>
            </div>
            <h3 className="text-xl sm:text-2xl font-black text-gray-900 tracking-tight">
              {team.fullName}
            </h3>
            <div className="mt-1 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-purple-600 text-white text-xs font-black shadow-xs">
              <span>현재 순위: {team.rank}위</span>
            </div>
          </div>
        </div>

        {/* Key Statistics Grid */}
        <div className="mt-5 grid grid-cols-2 gap-3 text-center">
          {/* Record */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-bold text-gray-400 block mb-1">시즌 성적</span>
            <span className="text-base font-extrabold text-gray-900">
              {team.wins}승 {team.draws}무 {team.losses}패
            </span>
          </div>

          {/* Win Rate */}
          <div className="p-3.5 rounded-2xl bg-purple-50/60 border border-purple-100">
            <span className="text-[11px] font-bold text-purple-600 block mb-1">승률</span>
            <span className="text-base font-extrabold text-purple-900 font-mono">
              {team.winRate}
            </span>
          </div>

          {/* Games Behind */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-bold text-gray-400 block mb-1">게임차</span>
            <span className="text-base font-extrabold text-gray-900 font-mono">
              {team.gamesBehind === '-' ? '0.0 (1위)' : `${team.gamesBehind} 게임`}
            </span>
          </div>

          {/* Last 5 Games Record */}
          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
            <span className="text-[11px] font-bold text-gray-400 block mb-1">최근 흐름</span>
            <span className="text-xs sm:text-sm font-extrabold text-gray-800">
              {team.last5Record}
            </span>
          </div>
        </div>

        {/* Recent 5 Games W/L Badges row */}
        <div className="mt-4 p-3.5 rounded-2xl bg-gray-50/80 border border-gray-100 flex items-center justify-between">
          <span className="text-xs font-bold text-gray-500">최근 5경기:</span>
          <div className="flex items-center gap-1.5 font-mono">
            {team.last5.map((result, idx) => (
              <span
                key={idx}
                className={`w-6 h-6 rounded-lg text-xs font-black flex items-center justify-center shadow-2xs ${
                  result === 'W'
                    ? 'bg-emerald-100 text-emerald-800'
                    : result === 'L'
                    ? 'bg-slate-200 text-slate-700'
                    : 'bg-amber-100 text-amber-800'
                }`}
                title={result === 'W' ? '승리' : '패배'}
              >
                {result}
              </span>
            ))}
          </div>
        </div>

        {/* Analysis Commentary Box */}
        <div className="mt-4 p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50/40 border border-purple-100 text-left">
          <div className="flex items-center gap-1.5 text-xs font-extrabold text-purple-900 mb-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>AI 순위 분석 브리핑</span>
          </div>
          <p className="text-xs sm:text-sm font-medium leading-relaxed text-purple-950">
            "{team.analysisComment}"
          </p>
        </div>
      </div>

      {/* Action Button: '이 팀 경기 보기' */}
      <div className="mt-6 pt-4 border-t border-gray-100">
        <button
          type="button"
          onClick={onNavigateToGame}
          className="w-full py-4 px-6 rounded-2xl bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white font-bold text-sm sm:text-base transition-all duration-200 cursor-pointer shadow-lg shadow-purple-600/20 hover:shadow-xl hover:shadow-purple-600/30 flex items-center justify-center gap-2 group hover:scale-[1.01]"
        >
          <Tv className="w-4 h-4 text-purple-200" />
          <span>이 팀 경기 보기</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>

    </div>
  );
}
