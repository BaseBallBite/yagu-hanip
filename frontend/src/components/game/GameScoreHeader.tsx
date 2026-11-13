
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CurrentGameSummary } from '../../data/mockGameData';
import { Calendar, MapPin, History } from 'lucide-react';

interface GameScoreHeaderProps {
  summary: CurrentGameSummary;
}

const TEAM_INFO: Record<
  string,
  { name: string; bg: string; text: string }
> = {
  KIA: {
    name: 'KIA 타이거즈',
    bg: '#D71920',
    text: '#FFFFFF',
  },
  SSG: {
    name: 'SSG 랜더스',
    bg: '#F04E5E',
    text: '#FFFFFF',
  },
  KT: {
    name: 'KT 위즈',
    bg: '#333333',
    text: '#FFFFFF',
  },
  LG: {
    name: 'LG 트윈스',
    bg: '#D41470',
    text: '#FFFFFF',
  },
  두산: {
    name: '두산 베어스',
    bg: '#171735',
    text: '#FFFFFF',
  },
  삼성: {
    name: '삼성 라이온즈',
    bg: '#0066B3',
    text: '#FFFFFF',
  },
  롯데: {
    name: '롯데 자이언츠',
    bg: '#285477',
    text: '#FFFFFF',
  },
  한화: {
    name: '한화 이글스',
    bg: '#FF6B00',
    text: '#FFFFFF',
  },
  NC: {
    name: 'NC 다이노스',
    bg: '#C9A34E',
    text: '#171735',
  },
  키움: {
    name: '키움 히어로즈',
    bg: '#760D35',
    text: '#FFFFFF',
  },
};

function getTeamInfo(team: string) {
  return (
    TEAM_INFO[team] ?? {
      name: team,
      bg: '#6B7280',
      text: '#FFFFFF',
    }
  );
}

function TeamDisplay({
  team,
  side,
}: {
  team: string;
  side: 'HOME' | 'AWAY';
}) {
  const info = getTeamInfo(team);
  const isAway = side === 'AWAY';

  return (
    <div
      className={`flex items-center gap-3 ${
        isAway ? 'flex-row-reverse text-right' : ''
      }`}
    >
      <div
        className="w-11 h-11 shrink-0 rounded-2xl font-black text-xs flex items-center justify-center shadow-sm"
        style={{
          backgroundColor: info.bg,
          color: info.text,
        }}
      >
        {team}
      </div>

      <div>
        <div className="text-[11px] font-semibold text-gray-400">
          {side}
        </div>

        <div className="text-sm sm:text-lg font-black text-gray-900 whitespace-nowrap">
          {info.name}
        </div>
      </div>
    </div>
  );
}

export function GameScoreHeader({
  summary,
}: GameScoreHeaderProps) {
  const { runners } = summary;

  const runnerCount = [
    runners.first,
    runners.second,
    runners.third,
  ].filter(Boolean).length;

  const runnerText =
    runnerCount === 0
      ? '주자 없음'
      : [
          runners.first ? '1루' : null,
          runners.second ? '2루' : null,
          runners.third ? '3루' : null,
        ]
          .filter(Boolean)
          .join(' · ');

  return (
    <div className="w-full bg-white rounded-3xl p-5 sm:p-6 border border-gray-100 shadow-md shadow-purple-950/5 mb-6">
      <div className="flex flex-col lg:flex-row items-center justify-between gap-6">

        {/* 경기 기록 및 날짜 */}
        <div className="flex items-center gap-3 w-full lg:w-auto justify-between lg:justify-start">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-purple-600" />

            <span className="text-xs font-black text-purple-700 tracking-wider">
              경기 기록
            </span>

            <span className="text-xs font-bold text-gray-300">
              |
            </span>

            <span className="text-xs font-semibold text-gray-600 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-gray-400" />
              {summary.date}
            </span>
          </div>

          {summary.stadium && (
            <div className="text-xs font-medium text-gray-500 flex items-center gap-1 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-100">
              <MapPin className="w-3 h-3 text-purple-600" />
              <span>{summary.stadium}</span>
            </div>
          )}
        </div>

        {/* 실제 홈팀·원정팀 점수 */}
        <div className="flex items-center justify-center gap-4 sm:gap-8 flex-wrap">
          <TeamDisplay
            team={summary.homeTeam}
            side="HOME"
          />

          <div className="text-center px-2">
            <div className="text-3xl sm:text-4xl font-black tracking-wider text-gray-900 flex items-center gap-3">
              <span className="text-purple-600 font-mono">
                {summary.homeScore}
              </span>

              <span className="text-gray-300 font-light">
                :
              </span>

              <span className="text-gray-900 font-mono">
                {summary.awayScore}
              </span>
            </div>

            <div className="mt-1 inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-purple-100 text-purple-800 text-xs font-black">
              <span>{summary.inning}</span>
            </div>
          </div>

          <TeamDisplay
            team={summary.awayTeam}
            side="AWAY"
          />
        </div>

        {/* 아웃 카운트 및 주자 */}
        <div className="flex items-center gap-6 bg-slate-50 p-3 sm:px-4 sm:py-2.5 rounded-2xl border border-gray-100 w-full lg:w-auto justify-around lg:justify-end">

          <div className="flex flex-col items-center">
            <span className="text-[11px] font-bold text-gray-500 mb-1">
              아웃 카운트
            </span>

            <div
              className="flex items-center gap-1.5"
              title={`${summary.outsCount}아웃`}
            >
              {[1, 2, 3].map((count) => (
                <span
                  key={count}
                  className={`w-3 h-3 rounded-full ${
                    summary.outsCount >= count
                      ? 'bg-red-500 shadow-sm'
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>

            <span className="text-[10px] font-bold text-red-600 mt-1">
              {summary.outsCount} 아웃
            </span>
          </div>

          <div className="w-px h-8 bg-gray-200" />

          <div className="flex items-center gap-3">
            <div className="flex flex-col items-center">
              <span className="text-[11px] font-bold text-gray-500 mb-1">
                주자 상황
              </span>

              <div className="relative w-8 h-8 select-none">

                {/* 2루 */}
                <div
                  className={`absolute top-0 left-1/2 -translate-x-1/2 w-2.5 h-2.5 rotate-45 border ${
                    runners.second
                      ? 'bg-purple-600 border-purple-700 shadow-sm'
                      : 'bg-white border-gray-300'
                  }`}
                  title={
                    runners.second
                      ? '2루 주자 있음'
                      : '2루 주자 없음'
                  }
                />

                {/* 3루 */}
                <div
                  className={`absolute top-1/2 left-0 -translate-y-1/2 w-2.5 h-2.5 rotate-45 border ${
                    runners.third
                      ? 'bg-purple-600 border-purple-700 shadow-sm'
                      : 'bg-white border-gray-300'
                  }`}
                  title={
                    runners.third
                      ? '3루 주자 있음'
                      : '3루 주자 없음'
                  }
                />

                {/* 1루 */}
                <div
                  className={`absolute top-1/2 right-0 -translate-y-1/2 w-2.5 h-2.5 rotate-45 border ${
                    runners.first
                      ? 'bg-purple-600 border-purple-700 shadow-sm'
                      : 'bg-white border-gray-300'
                  }`}
                  title={
                    runners.first
                      ? '1루 주자 있음'
                      : '1루 주자 없음'
                  }
                />

                {/* 홈플레이트 */}
                <div
                  className="absolute bottom-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-400 rotate-45"
                  title="홈플레이트"
                />
              </div>
            </div>

            <div className="flex flex-col text-left">
              <span className="text-xs font-black text-purple-700">
                {runnerCount === 0
                  ? '주자 없음'
                  : `${runnerCount}명 출루`}
              </span>

              <span className="text-[10px] text-gray-500">
                {runnerText}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
