
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import {
  Tv,
  Search,
  ArrowRight,
  ChevronRight,
  BookOpen,
} from 'lucide-react';

import {
  RecentGameActivity,
  RecentSearchTerm,
} from '../../data/mockMyData';

interface RecentActivityCardProps {
  games: RecentGameActivity[];
  terms: RecentSearchTerm[];
  onNavigate: (path: string) => void;
}

export function RecentActivityCard({
  games,
  terms,
  onNavigate,
}: RecentActivityCardProps) {

  const handleTermClick = (term: RecentSearchTerm) => {
    // 사전 페이지에서 이 용어를 표시하도록 전달
    sessionStorage.setItem('yagu_dictionary_target', term.id);
    onNavigate('/dictionary');
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

      {/* 최근 본 경기 */}
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shadow-xs">
                <Tv className="w-4 h-4" />
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
              전체보기
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5">
            {games.length > 0 ? (
              games.map((g) => (
                <button
                  key={g.id}
                  type="button"
                  onClick={() => onNavigate('/game')}
                  className="w-full text-left group p-3 rounded-2xl bg-gray-50/70 hover:bg-purple-50/30 border border-gray-100 hover:border-purple-200 transition-all cursor-pointer flex items-center justify-between gap-3"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[11px] font-bold text-purple-700 bg-purple-100/60 px-1.5 py-0.5 rounded">
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

                  <span className="w-7 h-7 rounded-xl bg-white border border-gray-100 flex items-center justify-center text-gray-400 group-hover:text-purple-600 group-hover:border-purple-200 transition-colors shrink-0">
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </button>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-gray-400">
                아직 확인한 경기가 없어요.
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-gray-100/80 flex items-center justify-between text-[11px] text-gray-400">
          <span>최근 경기 기록</span>
          <span className="text-purple-600 font-medium">
            경기 화면으로 이동
          </span>
        </div>
      </div>

      {/* 최근 검색한 야구 용어 */}
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shadow-xs">
                <Search className="w-4 h-4" />
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
              사전 가기
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <p className="text-xs text-gray-500 mb-3.5">
            최근 찾아본 야구 용어를 다시 확인할 수 있어요.
          </p>

          {terms.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {terms.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => handleTermClick(t)}
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
          ) : (
            <div className="py-8 flex flex-col items-center justify-center gap-2 text-center">
              <BookOpen className="w-6 h-6 text-gray-300" />
              <p className="text-xs font-medium text-gray-500">
                아직 찾아본 야구 용어가 없어요.
              </p>
              <button
                type="button"
                onClick={() => onNavigate('/dictionary')}
                className="text-xs font-semibold text-purple-600 hover:text-purple-700 cursor-pointer"
              >
                야구사전 둘러보기
              </button>
            </div>
          )}
        </div>

        <div className="mt-4 pt-3 border-t border-gray-100/80 flex items-center justify-between text-[11px] text-gray-400">
          <span>최근 {terms.length}개 용어</span>
          <span className="text-purple-600 font-medium">
            클릭 시 사전으로 이동
          </span>
        </div>
      </div>
    </div>
  );
}
