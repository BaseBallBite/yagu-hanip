/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { 
  Settings, 
  Sparkles, 
  ChevronRight, 
  Sliders, 
  HelpCircle,
  Lightbulb,
  Check
} from 'lucide-react';
import { ExplanationLevel } from '../../data/mockMyData';

interface MySettingsCardProps {
  explanationLevel: ExplanationLevel;
  onChangeLevel: (level: ExplanationLevel) => void;
  onNavigate: (path: string) => void;
}

export function MySettingsCard({
  explanationLevel,
  onChangeLevel,
  onNavigate
}: MySettingsCardProps) {
  const levels: { id: ExplanationLevel; label: string; desc: string }[] = [
    { id: 'beginner', label: '초보자', desc: '쉬운 비유와 직관적인 기초 설명' },
    { id: 'standard', label: '보통', desc: '경기 흐름과 야구 용어 중심' },
    { id: 'detailed', label: '자세히', desc: '세부 전술과 데이터 통계 포함' }
  ];

  return (
    <div className="space-y-4">
      {/* Settings Card */}
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-sm transition-all duration-300 hover:shadow-md">
        <div className="flex items-center gap-2 mb-5">
          <span className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm shadow-xs">
            <Settings className="w-4 h-4 text-purple-600" />
          </span>
          <h2 className="text-lg font-bold text-gray-900 tracking-tight">설정</h2>
        </div>

        <div className="space-y-5">
          {/* Setting Item 1: Team Change Quick Nav */}
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div>
              <p className="text-sm font-semibold text-gray-900">응원 팀 변경</p>
              <p className="text-xs text-gray-500 mt-0.5">KBO 10개 구단 중 언제든 변경할 수 있어요</p>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('/team-select')}
              className="px-3 py-1.5 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 text-xs font-semibold text-gray-700 hover:text-purple-700 flex items-center gap-1 transition cursor-pointer"
            >
              <span>변경하기</span>
              <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
            </button>
          </div>

          {/* Setting Item 2: AI Explanation Difficulty Level */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-semibold text-gray-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span>AI 해설 난이도</span>
              </label>
              <span className="text-[11px] font-medium text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md border border-purple-100">
                기본값: 초보자
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              '한입만!' 버튼을 눌렀을 때 제공되는 AI 해설의 깊이를 조절합니다.
            </p>

            {/* Segmented Select buttons */}
            <div className="grid grid-cols-3 gap-2 p-1 bg-gray-50 rounded-2xl border border-gray-100">
              {levels.map((lvl) => {
                const isActive = explanationLevel === lvl.id;
                return (
                  <button
                    key={lvl.id}
                    type="button"
                    onClick={() => onChangeLevel(lvl.id)}
                    className={`py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex flex-col items-center justify-center gap-0.5 cursor-pointer ${
                      isActive
                        ? 'bg-white text-purple-700 shadow-xs border border-purple-200/80'
                        : 'text-gray-500 hover:text-gray-900 hover:bg-white/60'
                    }`}
                  >
                    <div className="flex items-center gap-1">
                      <span>{lvl.label}</span>
                      {isActive && <Check className="w-3 h-3 text-purple-600 stroke-[3]" />}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Helper description for active level */}
            <div className="mt-2.5 px-3 py-2 rounded-xl bg-purple-50/50 border border-purple-100/60 text-[11px] text-purple-800 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-600 shrink-0" />
              <span>
                {levels.find((l) => l.id === explanationLevel)?.desc}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Service Guide Replay */}
      <button
        type="button"
        onClick={() => onNavigate('/guide')}
        className="w-full bg-white rounded-2xl p-4 border border-gray-100 shadow-sm hover:shadow-md hover:border-purple-200 transition-all flex items-center justify-between gap-3 text-left cursor-pointer group"
      >
        <div className="flex items-center gap-3">
          <span className="w-9 h-9 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
            <HelpCircle className="w-4 h-4 text-purple-600" />
          </span>

          <div>
            <p className="text-sm font-bold text-gray-900 group-hover:text-purple-700 transition-colors">
              서비스 이용 가이드 다시 보기
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              야구한입 사용 방법을 처음부터 확인해요
            </p>
          </div>
        </div>

        <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-purple-600 shrink-0" />
      </button>

      
      {/* Personalization Info Guidance Box */}
      <div className="rounded-2xl p-4 bg-gradient-to-r from-purple-50/70 via-indigo-50/40 to-purple-50/70 border border-purple-100/80 text-xs text-purple-900 flex items-start gap-3 shadow-xs">
        <Lightbulb className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="font-semibold text-purple-950">야구한입</strong>은 선택한 응원 팀과 
          내가 자주 찾는 정보를 바탕으로 더 보기 편한 맞춤 경기 정보를 제공할 예정이에요.
        </p>
      </div>
    </div>
  );
}
