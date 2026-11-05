/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { 
  Sparkles, 
  HelpCircle, 
  Search, 
  CheckCircle2, 
  BookOpen, 
  ArrowDown, 
  MousePointerClick, 
  Bot 
} from 'lucide-react';
import { OnboardingLayout } from './OnboardingLayout';
import { GameSituationPreview } from './GameSituationPreview';

export interface OnboardingStep2Props {
  onNavigate: (path: string) => void;
}

export function OnboardingStep2({ onNavigate }: OnboardingStep2Props) {
  const handleSkip = () => {
    onNavigate('/team-select');
  };

  const handlePrev = () => {
    onNavigate('/onboarding');
  };

  const handleNext = () => {
    onNavigate('/team-select');
  };

  return (
    <OnboardingLayout
      currentStep={2}
      totalSteps={3}
      onSkip={handleSkip}
      onPrev={handlePrev}
      onNext={handleNext}
      prevButtonLabel="이전"
      nextButtonLabel="다음"
      leftContent={<GameSituationPreview />}
      rightContent={
        <div className="flex flex-col items-start text-left w-full">
          {/* Small label */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/90 text-purple-700 text-xs font-bold mb-4">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>야구한입 사용법</span>
          </div>

          {/* Big title */}
          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight mb-4 leading-snug">
            모르는 장면은{"\n"}
            <span className="text-purple-600">🤔 왜?</span> 한 번이면 돼요
          </h1>

          {/* Description */}
          <p className="text-base sm:text-lg text-gray-600 leading-relaxed font-normal mb-8 whitespace-pre-line">
            경기를 보다 이해되지 않는 상황이 나오면{"\n"}
            <span className="font-semibold text-purple-700">🤔 왜?</span> 버튼을 눌러보세요.{"\n\n"}
            AI가 현재 경기 기록과 야구 규칙을 바탕으로{"\n"}
            <span className="font-semibold text-gray-900">초보자도 이해하기 쉬운 말</span>로 설명해줘요.
          </p>

          {/* 3-Step Usage Flow */}
          <div className="w-full bg-white rounded-2xl p-5 border border-gray-100 shadow-sm mb-6 space-y-3">
            {/* Step 1 */}
            <div className="flex items-center gap-3.5 p-2 rounded-xl hover:bg-gray-50 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0 font-black text-sm">
                1
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-gray-400">Step 01</div>
                <div className="text-sm sm:text-base font-bold text-gray-900">
                  궁금한 경기 장면 발견
                </div>
              </div>
              <Search className="w-4 h-4 text-gray-400" />
            </div>

            {/* Down Arrow connector */}
            <div className="flex justify-center -my-1 text-purple-400">
              <ArrowDown className="w-4 h-4" />
            </div>

            {/* Step 2 */}
            <div className="flex items-center gap-3.5 p-2 rounded-xl bg-purple-50/60 border border-purple-100/80 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center shrink-0 font-black text-sm shadow-xs">
                2
              </div>
              <div className="flex-1">
                <div className="text-xs font-bold text-purple-700">Step 02 · 핵심</div>
                <div className="text-sm sm:text-base font-extrabold text-purple-900 flex items-center gap-1.5">
                  <span>🤔 왜? 버튼 클릭</span>
                </div>
              </div>
              <MousePointerClick className="w-4 h-4 text-purple-600 animate-bounce" />
            </div>

            {/* Down Arrow connector */}
            <div className="flex justify-center -my-1 text-purple-400">
              <ArrowDown className="w-4 h-4" />
            </div>

            {/* Step 3 */}
            <div className="flex items-center gap-3.5 p-2 rounded-xl hover:bg-gray-50 transition-colors">
              <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0 font-black text-sm">
                3
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-gray-400">Step 03</div>
                <div className="text-sm sm:text-base font-bold text-gray-900">
                  AI가 상황과 규칙을 쉽게 설명
                </div>
              </div>
              <Bot className="w-4 h-4 text-purple-600" />
            </div>
          </div>

          {/* Bottom Highlight Message Box */}
          <div className="w-full p-4 rounded-2xl bg-purple-50/90 border border-purple-200/80 text-purple-900 flex items-start gap-3 shadow-xs">
            <BookOpen className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
            <p className="text-xs sm:text-sm font-semibold leading-relaxed">
              야구 용어를 몰라도 괜찮아요.{"\n"}
              설명 속 어려운 단어는 <span className="text-purple-700 underline underline-offset-2">야구사전</span>에서 바로 확인할 수 있어요.
            </p>
          </div>

        </div>
      }
    />
  );
}
