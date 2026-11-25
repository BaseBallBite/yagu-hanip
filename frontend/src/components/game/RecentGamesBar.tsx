
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import type { RecentGameItem } from '../../data/mockGameData';
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
    <div className="w-full rounded-3xl border border-gray-100 bg-white p-4 shadow-sm">

      {/* 경기 목록 제목 */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-1.5 text-xs font-bold text-gray-500">
          <History className="w-3.5 h-3.5 text-purple-600" />
          <span>경기 선택</span>
        </div>


      </div>

      {/* 선택 가능한 실제 경기 */}
      <div className="flex flex-col gap-2 max-h-[60vh] overflow-y-auto pr-1">
        {games.map((game) => {
          const isSelected =
            game.id === selectedGameId;

          return (
            <button
              key={game.id}
              type="button"
              onClick={() => onSelectGame(game.id)}
              aria-pressed={isSelected}
              className={`w-full min-w-0 shrink-0 px-3 py-2.5 rounded-xl border text-left transition-all duration-200 cursor-pointer flex items-center justify-between gap-2 group ${
                isSelected
                  ? 'bg-purple-50/70 border-2 border-purple-600 ring-2 ring-purple-200/50 shadow-sm'
                  : 'bg-white border-gray-200/80 hover:border-purple-300 hover:shadow-sm hover:-translate-y-0.5'
              }`}
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-black text-gray-900 group-hover:text-purple-700 transition-colors">
                    {game.homeTeam}{' '}

                    <span
                      className={
                        isSelected
                          ? 'text-purple-600'
                          : 'text-gray-700'
                      }
                    >
                      {game.homeScore} : {game.awayScore}
                    </span>

                    {' '}{game.awayTeam}
                  </span>

                  {isSelected && (
                    <span className="text-[10px] font-bold text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded">
                      선택됨
                    </span>
                  )}
                </div>

                <div className="text-xs text-gray-500 mt-1 font-medium">
                  {game.date} · {game.status}
                </div>
              </div>

              <div
                className={`w-5 h-5 shrink-0 rounded-full flex items-center justify-center transition-all ${
                  isSelected
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'border border-gray-300 text-transparent group-hover:border-purple-300'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
