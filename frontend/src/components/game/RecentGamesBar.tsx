/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { RecentGameItem } from '../../data/mockGameData';
import { History, CheckCircle2 } from 'lucide-react';

interface RecentGamesBarProps {
  games: RecentGameItem[];
  selectedGameId: string;
  onSelectGame: (gameId: string) => void;
}

export function RecentGamesBar({
  games,
  selectedGameId,
  onSelectGame,
}: RecentGamesBarProps) {
  return (
    <div className="w-full mb-6">
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-1.5 text-xs font-bold text-gray-500">
          <History className="w-3.5 h-3.5 text-purple-600" />
          <span>최근 맞대결 경기 선택</span>
        </div>
        <span className="text-[11px] text-gray-400">클릭하여 해당 경기 기록 조회</span>
      </div>

      {/* 3 Horizontal Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {games.map((g) => {
          const isSelected = g.id === selectedGameId;

          return (
            <button
              key={g.id}
              type="button"
              onClick={() => onSelectGame(g.id)}
              className={`p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-center justify-between group ${
                isSelected
                  ? 'bg-purple-50/70 border-2 border-purple-600 ring-2 ring-purple-200/50 shadow-sm'
                  : 'bg-white border-gray-200/80 hover:border-purple-300 hover:shadow-xs hover:-translate-y-0.5'
              }`}
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-black text-gray-900 group-hover:text-purple-700 transition-colors">
                    {g.homeTeam} <span className={isSelected ? 'text-purple-600' : 'text-gray-700'}>{g.homeScore} : {g.awayScore}</span> {g.awayTeam}
                  </span>
                  {isSelected && (
                    <span className="text-[10px] font-bold text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded">
                      선택됨
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-0.5 font-medium">
                  {g.date} · {g.status}
                </div>
              </div>

              {/* Selection indicator checkmark */}
              <div className={`w-5 h-5 rounded-full flex items-center justify-center transition-all ${
                isSelected 
                  ? 'bg-purple-600 text-white shadow-xs' 
                  : 'border border-gray-300 text-transparent group-hover:border-purple-300'
              }`}>
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
