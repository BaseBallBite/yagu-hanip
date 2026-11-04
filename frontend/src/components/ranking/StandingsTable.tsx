/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { TeamStanding } from '../../data/mockRankingData';
import { Trophy, Star, ChevronRight, Heart } from 'lucide-react';

interface StandingsTableProps {
  standings: TeamStanding[];
  selectedTeamId: string;
  favoriteTeamName: string;
  onSelectTeam: (team: TeamStanding) => void;
}

export function StandingsTable({
  standings,
  selectedTeamId,
  favoriteTeamName,
  onSelectTeam,
}: StandingsTableProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-5 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 overflow-hidden">
      
      {/* Table Header Section */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-100 mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
            <Trophy className="w-4 h-4 text-purple-600" />
          </div>
          <div>
            <h2 className="text-base sm:text-lg font-black text-gray-900 tracking-tight">
              KBO 리그 정규시즌 순위
            </h2>
            <p className="text-xs text-gray-400">
              팀을 클릭하면 우측에서 상세 전력과 최근 경기 흐름을 확인할 수 있어요.
            </p>
          </div>
        </div>

        {favoriteTeamName && favoriteTeamName !== 'NONE' && (
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-50 border border-purple-100 text-purple-700 text-xs font-bold">
            <Heart className="w-3.5 h-3.5 fill-purple-600 text-purple-600" />
            <span>MY 응원 팀: {favoriteTeamName}</span>
          </div>
        )}
      </div>

      {/* Responsive Table Wrapper */}
      <div className="overflow-x-auto -mx-2 sm:mx-0">
        <table className="w-full text-left border-collapse min-w-[620px]">
          <thead>
            <tr className="border-b border-gray-100 text-[11px] font-extrabold text-gray-400 uppercase tracking-wider">
              <th className="py-3 px-3 text-center w-12">순위</th>
              <th className="py-3 px-3">팀</th>
              <th className="py-3 px-2 text-center w-14">승</th>
              <th className="py-3 px-2 text-center w-12">무</th>
              <th className="py-3 px-2 text-center w-14">패</th>
              <th className="py-3 px-3 text-center w-16">승률</th>
              <th className="py-3 px-3 text-center w-16">게임차</th>
              <th className="py-3 px-3 text-center w-40">최근 5경기</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50 text-xs sm:text-sm">
            {standings.map((team) => {
              const isSelected = team.id === selectedTeamId;
              const isFavorite = favoriteTeamName === team.name;

              return (
                <tr
                  key={team.id}
                  onClick={() => onSelectTeam(team)}
                  className={`transition-all duration-150 cursor-pointer group ${
                    isSelected
                      ? 'bg-purple-100/70 font-bold border-l-4 border-l-purple-600 text-purple-950 shadow-xs'
                      : isFavorite
                      ? 'bg-purple-50/50 hover:bg-purple-100/40 border-l-4 border-l-purple-300'
                      : 'hover:bg-slate-50/90 text-gray-800'
                  }`}
                >
                  {/* Rank */}
                  <td className="py-3.5 px-3 text-center">
                    <span className={`inline-flex items-center justify-center w-6 h-6 rounded-lg text-xs font-black ${
                      team.rank === 1
                        ? 'bg-amber-100 text-amber-800'
                        : team.rank <= 5
                        ? 'bg-purple-50 text-purple-700 font-extrabold'
                        : 'text-gray-500 font-bold'
                    }`}>
                      {team.rank}
                    </span>
                  </td>

                  {/* Team Name & Logo/Badge */}
                  <td className="py-3.5 px-3">
                    <div className="flex items-center gap-2.5">
                      {/* Authentic Team Circular Initial Badge */}
                      <div 
                        className="w-7 h-7 rounded-xl flex items-center justify-center text-[10px] font-black text-white shrink-0 shadow-2xs"
                        style={{ backgroundColor: team.primaryColor }}
                      >
                        {team.initial}
                      </div>

                      <div className="flex items-center gap-1.5">
                        <span className="font-extrabold text-gray-900 group-hover:text-purple-700 transition-colors">
                          {team.name}
                        </span>
                        <span className="text-gray-400 font-medium text-xs hidden sm:inline">
                          {team.fullName.replace(team.name, '').trim()}
                        </span>
                        {isFavorite && (
                          <span className="px-1.5 py-0.5 rounded-md bg-purple-600 text-white text-[10px] font-black ml-1 shadow-2xs">
                            MY
                          </span>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Wins */}
                  <td className="py-3.5 px-2 text-center font-bold text-gray-900">
                    {team.wins}
                  </td>

                  {/* Draws */}
                  <td className="py-3.5 px-2 text-center text-gray-400 font-medium">
                    {team.draws}
                  </td>

                  {/* Losses */}
                  <td className="py-3.5 px-2 text-center text-gray-600 font-semibold">
                    {team.losses}
                  </td>

                  {/* Win Rate */}
                  <td className="py-3.5 px-3 text-center font-mono font-extrabold text-purple-700">
                    {team.winRate}
                  </td>

                  {/* Games Behind */}
                  <td className="py-3.5 px-3 text-center font-mono text-gray-600 font-bold">
                    {team.gamesBehind}
                  </td>

                  {/* Last 5 Games Badges (W / L / W / W / L) */}
                  <td className="py-3.5 px-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {team.last5.map((result, idx) => (
                        <span
                          key={idx}
                          className={`w-5 h-5 rounded-md text-[10px] font-black flex items-center justify-center shadow-2xs ${
                            result === 'W'
                              ? 'bg-emerald-100 text-emerald-800'
                              : result === 'L'
                              ? 'bg-slate-100 text-slate-600'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                          title={result === 'W' ? '승리' : result === 'L' ? '패배' : '무승부'}
                        >
                          {result}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

    </div>
  );
}
