
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  Sparkles,
  HelpCircle,
  Zap,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export function GameSituationPreview() {
  const [isOpen, setIsOpen] = useState<boolean>(false);

  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col justify-between relative transition-all duration-300">

      {/* Card Header */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-100">
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-50 text-purple-700 text-xs font-bold border border-purple-100">
          <Sparkles className="w-3.5 h-3.5 text-purple-600" />
          <span>경기 중 이런 순간</span>
        </span>

        <span className="text-xs font-bold text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
          시연용 가상 경기 예시
        </span>
      </div>

      {/* Game Scoreboard */}
      <div className="mt-4 bg-gradient-to-br from-gray-50 to-purple-50/20 rounded-2xl p-4 border border-gray-100">
        <div className="flex items-center justify-between">

          {/* KT */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-black text-white font-black text-xs flex items-center justify-center shadow-xs">
              KT
            </div>
            <span className="font-extrabold text-gray-900 text-sm">
              KT
            </span>
          </div>

          {/* Score & Inning */}
          <div className="text-center">
            <div className="text-xl sm:text-2xl font-black text-gray-900 tracking-wider">
              <span className="text-purple-600">3</span> : <span>2</span>
            </div>
            <div className="text-[11px] font-bold text-purple-800 bg-purple-100/80 px-2 py-0.5 rounded-full mt-0.5">
              9회초 · 투구 전 0아웃
            </div>
          </div>

          {/* KIA */}
          <div className="flex items-center gap-2.5 flex-row-reverse text-right">
            <div className="w-9 h-9 rounded-xl bg-[#EA0029] text-white font-black text-xs flex items-center justify-center shadow-xs">
              KIA
            </div>
            <span className="font-extrabold text-gray-900 text-sm">
              KIA
            </span>
          </div>
        </div>
      </div>

      {/* Current At Bat */}
      <div className="mt-3 p-3.5 rounded-2xl bg-white border border-gray-100 shadow-xs">
        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1">
          현재 타석
        </div>

        <div className="flex items-center justify-between text-sm sm:text-base font-bold text-gray-900">
          <span>
            황대인{' '}
            <span className="text-xs text-gray-500 font-normal">
              (타자)
            </span>
          </span>

          <span className="text-xs font-bold text-gray-400 px-2 py-0.5 bg-gray-50 rounded">
            VS
          </span>

          <span>
            박영현{' '}
            <span className="text-xs text-gray-500 font-normal">
              (투수)
            </span>
          </span>
        </div>
      </div>

      {/* Pitch Info & Result */}
      <div className="mt-3 p-3.5 rounded-2xl bg-purple-50/40 border border-purple-100">
        <div className="text-[11px] font-bold text-purple-700 flex items-center gap-1 mb-1">
          <Zap className="w-3 h-3 text-purple-600" />
          <span>투구 정보</span>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-extrabold text-gray-900">
              6구 슬라이더
            </div>

            <div className="text-xs text-gray-600 font-medium">
              헛스윙 · 136km/h
            </div>
          </div>

          <div className="px-3 py-1.5 rounded-xl bg-white border border-purple-200 text-purple-700 font-black text-sm shadow-xs">
            → 삼진 아웃 · 1아웃
          </div>
        </div>
      </div>

      {/* 한입만! Button */}
      <div className="mt-5 pt-3 border-t border-gray-100 flex flex-col items-center">
        <div className="text-xs font-medium text-gray-500 mb-2.5 flex items-center gap-1">
          <HelpCircle className="w-3.5 h-3.5 text-purple-600" />
          <span>이 장면이 이해되지 않는다면?</span>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={`w-full py-3.5 px-6 rounded-2xl font-black text-base sm:text-lg flex items-center justify-center gap-2.5 transition-all duration-300 cursor-pointer shadow-md ${
            isOpen
              ? 'bg-purple-700 text-white shadow-purple-700/25 ring-2 ring-purple-300'
              : 'bg-purple-600 hover:bg-purple-700 text-white shadow-purple-600/30 animate-gentle-pulse hover:scale-[1.01]'
          }`}
          aria-expanded={isOpen}
        >
          <span>한입만!</span>

          <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-white/20 ml-1">
            {isOpen ? '해설 닫기' : '눌러서 해설 보기'}
          </span>

          {isOpen ? (
            <ChevronUp className="w-4 h-4 ml-auto" />
          ) : (
            <ChevronDown className="w-4 h-4 ml-auto" />
          )}
        </button>
      </div>

      {/* AI Explanation Panel */}
      {isOpen && (
        <div className="mt-4 p-5 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-700 text-white shadow-xl shadow-purple-900/20 border border-purple-400/30 animate-slide-down">

          {/* Panel Header */}
          <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-white/15">
            <div className="flex items-center gap-1.5 text-xs font-bold text-purple-100">
              <Sparkles className="w-4 h-4 text-yellow-300" />
              <span>해설 예시</span>
            </div>

            <span className="text-[10px] font-semibold text-purple-200 bg-white/15 px-2 py-0.5 rounded-full">
              즉시 답변
            </span>
          </div>

          {/* AI Explanation Body */}
          <p className="text-sm sm:text-[15px] font-medium leading-relaxed text-purple-50 whitespace-pre-line mb-4">
            "슬라이더가 아래쪽으로 떨어지면서{"\n"}
            타자의 배트가 헛돌았어요.{"\n\n"}
            스트라이크가 3개가 되어{"\n"}
            삼진 아웃이 된 상황이에요."
          </p>

          {/* Related Terminology Chips */}
          <div className="pt-3 border-t border-white/15">
            <span className="text-[11px] font-bold text-purple-200 block mb-2">
              관련 용어:
            </span>

            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-1 rounded-lg bg-white/20 text-white font-bold text-xs tracking-wide shadow-xs hover:bg-white/30 transition-colors animate-fade-in [animation-delay:100ms]">
                #슬라이더
              </span>

              <span className="px-2.5 py-1 rounded-lg bg-white/20 text-white font-bold text-xs tracking-wide shadow-xs hover:bg-white/30 transition-colors animate-fade-in [animation-delay:200ms]">
                #헛스윙
              </span>

              <span className="px-2.5 py-1 rounded-lg bg-white/20 text-white font-bold text-xs tracking-wide shadow-xs hover:bg-white/30 transition-colors animate-fade-in [animation-delay:300ms]">
                #삼진
              </span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
