
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  Heart,
  ArrowRight,
  RotateCcw,
  Trophy,
  Calendar,
  TrendingUp,
  Compass,
} from 'lucide-react';

import { TeamStanding } from '../../data/mockRankingData';

interface MyTeamCardProps {
  team: TeamStanding | null;
  onNavigate: (path: string) => void;
}

// 온보딩에서 확정한 10개 구단 UI 색상과 통일
const TEAM_BADGE_COLORS: Record<
  string,
  {
    background: string;
    text: string;
    lightBg: string;
  }
> = {
  kia: {
    background: '#D71920',
    text: '#FFFFFF',
    lightBg: '#FFF1F2',
  },
  samsung: {
    background: '#0066B3',
    text: '#FFFFFF',
    lightBg: '#EFF6FF',
  },
  lg: {
    background: '#D41470',
    text: '#FFFFFF',
    lightBg: '#FFF0F7',
  },
  doosan: {
    background: '#171735',
    text: '#FFFFFF',
    lightBg: '#F1F5F9',
  },
  kt: {
    background: '#333333',
    text: '#FFFFFF',
    lightBg: '#F5F5F5',
  },
  ssg: {
    background: '#F04E5E',
    text: '#FFFFFF',
    lightBg: '#FFF1F3',
  },
  lotte: {
    background: '#285477',
    text: '#FFFFFF',
    lightBg: '#EFF6FA',
  },
  hanwha: {
    background: '#FF6B00',
    text: '#FFFFFF',
    lightBg: '#FFF4E8',
  },
  nc: {
    background: '#C9A34E',
    text: '#172033',
    lightBg: '#FFFBEB',
  },
  kiwoom: {
    background: '#760D35',
    text: '#FFFFFF',
    lightBg: '#FFF1F5',
  },
};

export function MyTeamCard({
  team,
  onNavigate,
}: MyTeamCardProps) {

  // 응원팀이 선택되지 않았을 때
  if (!team) {
    return (
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm relative overflow-hidden transition-all duration-300 hover:shadow-md">

        <div className="absolute -top-12 -right-12 w-40 h-40 bg-purple-50 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-base shadow-xs">
              ⚾
            </span>

            <h2 className="text-xl font-bold text-gray-900 tracking-tight">
              나의 팀
            </h2>
          </div>

          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-500">
            미설정
          </span>
        </div>

        <div className="py-6 flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-purple-100 to-indigo-50 flex items-center justify-center text-purple-600 mb-4 shadow-xs">
            <Compass className="w-8 h-8 text-purple-600 stroke-[1.8]" />
          </div>

          <h3 className="text-lg font-bold text-gray-900 mb-2">
            아직 응원하는 팀이 없어요
          </h3>

          <p className="text-sm text-gray-500 leading-relaxed max-w-sm mb-6">
            응원 팀을 선택하면 해당 팀의 경기와 하이라이트,
            <br className="hidden sm:inline" />
            맞춤 해설을 먼저 모아서 보여드려요.
          </p>

          <button
            type="button"
            onClick={() => onNavigate('/team-select')}
            className="w-full sm:w-auto min-w-[200px] inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-sm transition-all shadow-md shadow-purple-600/20 hover:shadow-lg hover:shadow-purple-600/30 active:scale-98 cursor-pointer"
          >
            <span>팀 고르기</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // 팀 ID를 기준으로 구단별 배지 색상 선택
  const teamColors = TEAM_BADGE_COLORS[team.id.toLowerCase()] ?? {
    background: team.primaryColor || '#64748B',
    text: '#FFFFFF',
    lightBg: team.lightBg || '#F8FAFC',
  };

  return (
    <div className="bg-white rounded-3xl p-6 md:p-8 border border-gray-100 shadow-sm relative overflow-hidden transition-all duration-300 hover:shadow-md">

      {/* Top Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-base shadow-xs">
            ⚾
          </span>

          <h2 className="text-xl font-bold text-gray-900 tracking-tight">
            나의 팀
          </h2>
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-100 text-xs font-bold">
          <Heart className="w-3.5 h-3.5 fill-purple-600 text-purple-600" />
          <span>나의 응원 팀</span>
        </div>
      </div>

      {/* Team Brand Hero Banner */}
      <div
        className="rounded-2xl p-5 mb-6 relative overflow-hidden border transition-transform"
        style={{
          backgroundColor: teamColors.lightBg,
          borderColor: `${teamColors.background}25`,
        }}
      >
        <div className="flex items-center gap-4">

          {/* 구단 PNG 대신 구단명 텍스트 배지 */}
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center shrink-0 shadow-sm font-black text-base select-none transition-transform hover:scale-105"
            style={{
              backgroundColor: teamColors.background,
              color: teamColors.text,
              border: '1px solid transparent',
            }}
            aria-label={`${team.fullName} 응원팀`}
          >
            <span>{team.initial || team.name}</span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-white/80 text-gray-700 backdrop-blur-xs border border-white/60">
                KBO LEAGUE
              </span>

              <span className="text-xs text-gray-500 font-medium">
                {team.stadium}
              </span>
            </div>

            <h3 className="text-2xl font-black text-gray-900 tracking-tight mt-1 truncate">
              {team.fullName}
            </h3>
          </div>
        </div>
      </div>

      {/* Quick Team Stats Grid */}
      <div className="grid grid-cols-3 gap-3 mb-6">

        {/* Current Rank */}
        <div className="bg-gray-50/80 rounded-2xl p-3.5 border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium mb-1">
            <Trophy className="w-3.5 h-3.5 text-amber-500" />
            <span>현재 순위</span>
          </div>

          <div className="flex items-baseline gap-1">
            <span className="text-xl font-black text-gray-900">
              {team.rank}위
            </span>

            <span className="text-[11px] text-gray-400 font-medium">
              ({team.gamesBehind === '-'
                ? '선두'
                : `${team.gamesBehind}G차`})
            </span>
          </div>
        </div>

        {/* Recent Game */}
        <div className="bg-gray-50/80 rounded-2xl p-3.5 border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium mb-1">
            <Calendar className="w-3.5 h-3.5 text-blue-500" />
            <span>최근 경기</span>
          </div>

          <div className="text-sm font-bold text-gray-900 truncate">
            {team.name === 'KT'
              ? 'KT 3 : 2 KIA'
              : 'KT 3 : 2 KIA'}
          </div>
        </div>

        {/* Recent 5 Games Flow */}
        <div className="bg-gray-50/80 rounded-2xl p-3.5 border border-gray-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium mb-1">
            <TrendingUp className="w-3.5 h-3.5 text-purple-500" />
            <span>최근 5경기</span>
          </div>

          <div className="flex items-center gap-1">
            {team.last5.map((result, idx) => (
              <span
                key={idx}
                className={`w-5 h-5 rounded-md text-[10px] font-black flex items-center justify-center shrink-0 ${
                  result === 'W'
                    ? 'bg-red-50 text-red-600 border border-red-200'
                    : result === 'L'
                    ? 'bg-blue-50 text-blue-600 border border-blue-200'
                    : 'bg-gray-100 text-gray-600 border border-gray-200'
                }`}
              >
                {result}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center gap-3">

        <button
          type="button"
          onClick={() => onNavigate('/game')}
          className="w-full flex-1 inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-sm transition-all shadow-md shadow-purple-600/20 hover:shadow-lg hover:shadow-purple-600/30 active:scale-98 cursor-pointer"
        >
          <span>팀 경기 보기</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={() => onNavigate('/team-select')}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-3.5 rounded-2xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50/40 text-gray-700 hover:text-purple-700 font-semibold text-sm transition-all cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
          <span>응원 팀 변경</span>
        </button>
      </div>
    </div>
  );
}
