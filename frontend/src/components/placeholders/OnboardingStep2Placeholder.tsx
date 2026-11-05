/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { ArrowLeft, Clock, Sparkles } from 'lucide-react';
import { OnboardingLayout } from '../onboarding/OnboardingLayout';

export interface OnboardingStep2PlaceholderProps {
  onNavigate: (path: string) => void;
}

export function OnboardingStep2Placeholder({ onNavigate }: OnboardingStep2PlaceholderProps) {
  return (
    <OnboardingLayout
      currentStep={2}
      totalSteps={3}
      onSkip={() => onNavigate('/team-select')}
      onNext={() => onNavigate('/team-select')}
      nextButtonLabel="팀 선택으로 이동"
      leftContent={
        <div className="w-full bg-white rounded-3xl p-8 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col items-center justify-center text-center min-h-[320px]">
          <div className="w-16 h-16 rounded-2xl bg-purple-50 text-purple-600 flex items-center justify-center text-2xl mb-4">
            ⚾
          </div>
          <span className="text-sm font-bold text-gray-800 mb-1">온보딩 2단계 (아웃 & 이닝)</span>
          <p className="text-xs text-gray-500 max-w-xs">
            다음 단계에서는 3아웃으로 공수가 바뀌는 9이닝 룰을 쉽게 알려드릴 예정이에요.
          </p>
        </div>
      }
      rightContent={
        <div className="flex flex-col items-start text-left w-full">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-xs font-bold mb-4">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>야구 기초 02 · 오픈 예정</span>
          </div>
          <h2 className="text-3xl font-black text-gray-900 tracking-tight mb-3">
            3아웃이면 공수가 바뀌어요
          </h2>
          <p className="text-base text-gray-600 mb-6">
            이 화면은 곧 추가될 두 번째 온보딩 페이지입니다.
          </p>
          <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-xs mb-6 w-full">
            <div className="flex items-center gap-2 text-sm font-bold text-purple-700 mb-1">
              <Clock className="w-4 h-4" />
              <span>준비 중인 화면</span>
            </div>
            <p className="text-xs text-gray-500">
              첫 번째 온보딩으로 돌아가시려면 아래 버튼을 눌러주세요.
            </p>
          </div>
          <button
            onClick={() => onNavigate('/onboarding')}
            className="px-5 py-2.5 rounded-xl border border-gray-200 hover:border-purple-300 text-gray-700 hover:text-purple-700 text-sm font-semibold transition flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>온보딩 1단계로 돌아가기</span>
          </button>
        </div>
      }
    />
  );
}
