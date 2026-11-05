/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { 
  History, 
  Tv, 
  Search, 
  ArrowRight, 
  ChevronRight, 
  Sparkles,
  BookOpen
} from 'lucide-react';
import { RecentGameActivity, RecentSearchTerm } from '../../data/mockMyData';

interface RecentActivityCardProps {
  games: RecentGameActivity[];
  terms: RecentSearchTerm[];
  onNavigate: (path: string) => void;
}

export function RecentActivityCard({
  games,
  terms,
  onNavigate
}: RecentActivityCardProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      {/* 1. Recent Watched Games Card */}
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm shadow-xs">
                <Tv className="w-4 h-4 text-purple-600" />
              </span>
              <h3 className="text-base font-bold text-gray-900 tracking-tight">
                최근 본 경기
              </h3>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('/game')}
              className="text-xs text-purple-600 hover:text-purple-700 font-semibold flex items-center gap-0.5 cursor-pointer"
            >
              <span>전체보기</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5">
            {games.map((g) => (
              <div
                key={g.id}
                onClick={() => onNavigate('/game')}
                className="group p-3 rounded-2xl bg-gray-50/70 hover:bg-purple-50/30 border border-gray-100 hover:border-purple-200 transition-all cursor-pointer flex items-center justify-between gap-3"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[11px] font-bold text-purple-700 bg-purple-100/60 px-1.5 py-0.2 rounded">
                      {g.date}
                    </span>
                    <span className="text-xs font-black text-gray-900 group-hover:text-purple-700 transition-colors">
                      {g.matchup}
                    </span>
                    <span className="text-[11px] font-bold text-gray-500">
                      ({g.score})
                    </span>
                  </div>
                  <p className="text-[11px] text-gray-500 truncate group-hover:text-gray-700">
                    {g.highlightSummary}
                  </p>
                </div>
                <div className="w-7 h-7 rounded-xl bg-white border border-gray-100 flex items-center justify-center text-gray-400 group-hover:text-purple-600 group-hover:border-purple-200 transition-colors shrink-0">
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-gray-100/80 flex items-center justify-between text-[11px] text-gray-400">
          <span>최근 3경기 시청 기록</span>
          <span className="text-purple-600 font-medium">클릭 시 해당 경기 열람</span>
        </div>
      </div>

      {/* 2. Recent Searched Terms Card */}
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm shadow-xs">
                <Search className="w-4 h-4 text-purple-600" />
              </span>
              <h3 className="text-base font-bold text-gray-900 tracking-tight">
                최근 검색한 야구 용어
              </h3>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('/dictionary')}
              className="text-xs text-purple-600 hover:text-purple-700 font-semibold flex items-center gap-0.5 cursor-pointer"
            >
              <span>사전 가기</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <p className="text-xs text-gray-500 mb-3.5">
            자주 찾아본 야구 용어를 누르면 AI 해설과 규칙을 바로 확인해요.
          </p>

          {/* Chips Grid */}
          <div className="flex flex-wrap gap-2">
            {terms.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => onNavigate('/dictionary')}
                className="group inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-gray-50 hover:bg-purple-50 text-gray-700 hover:text-purple-700 border border-gray-200 hover:border-purple-200 text-xs font-semibold transition-all shadow-2xs hover:shadow-xs active:scale-95 cursor-pointer"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400 group-hover:bg-purple-600 transition-colors" />
                <span>{t.name}</span>
                <span className="text-[10px] text-gray-400 group-hover:text-purple-500 font-normal">
                  {t.category}
                </span>
              </button>
            ))}
          </div>

          <div className="mt-4 p-3 rounded-2xl bg-purple-50/40 border border-purple-100/60 flex items-start gap-2.5 text-xs text-purple-900">
            <Sparkles className="w-3.5 h-3.5 text-purple-600 shrink-0 mt-0.5" />
            <span className="leading-relaxed text-[11px]">
              Tip: 야구사전에서 용어 우측 상단의 책갈피 아이콘을 누르면 질문과 함께 저장돼요.
            </span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-gray-100/80 flex items-center justify-between text-[11px] text-gray-400">
          <span>최근 4개 용어 검색</span>
          <span className="text-purple-600 font-medium">클릭 시 사전으로 이동</span>
        </div>
      </div>
    </div>
  );
}
