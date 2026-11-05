/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';
import { OnboardingLayout } from './OnboardingLayout';
import { StrikeZoneVisual } from './StrikeZoneVisual';
import { InfoCard } from './InfoCard';

export interface OnboardingStep1Props {
  onNavigate: (path: string) => void;
}

export function OnboardingStep1({ onNavigate }: OnboardingStep1Props) {
  const handleSkip = () => {
    onNavigate('/team-select');
  };

  const handleNext = () => {
    onNavigate('/onboarding/2');
  };

  return (
    <OnboardingLayout
      currentStep={1}
      totalSteps={3}
      onSkip={handleSkip}
      onNext={handleNext}
      nextButtonLabel="다음"
      leftContent={<StrikeZoneVisual />}
      rightContent={
        <div className="flex flex-col items-start text-left w-full">
          {/* Small label */}
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/90 text-purple-700 text-xs font-bold mb-4">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" />
            <span>야구 기초 01</span>
          </div>

          {/* Big title */}
          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight mb-3">
            공 하나하나가 승부예요
          </h1>

          {/* Description */}
          <p className="text-base sm:text-lg text-gray-600 leading-relaxed font-normal mb-8 whitespace-pre-line">
            투수가 던진 공을 타자가 치지 않으면{"\n"}
            공의 위치에 따라 <span className="font-semibold text-gray-900">'볼'</span> 또는 <span className="font-semibold text-purple-600">'스트라이크'</span>로 판정돼요.
          </p>

          {/* 2 Explanation Cards (볼 & 스트라이크) */}
          <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            {/* [볼] Card */}
            <InfoCard
              badgeTitle="볼"
              badgeColor="slate"
              countNumber={4}
              countUnit="개"
              actionText="타자는 1루로 이동"
              description="스트라이크 존 밖으로 벗어난 공이에요. 4번 모이면 볼넷으로 진루해요."
            />

            {/* [스트라이크] Card */}
            <InfoCard
              badgeTitle="스트라이크"
              badgeColor="purple"
              countNumber={3}
              countUnit="개"
              actionText="타자는 아웃"
              description="스트라이크 존을 통과했거나 헛스윙한 공이에요. 3번 모이면 삼진 아웃!"
            />
          </div>

          {/* Helpful Subtitle Notice */}
          <div className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-purple-50/70 border border-purple-100/60 text-purple-800 text-xs sm:text-sm font-semibold">
            <CheckCircle2 className="w-4 h-4 text-purple-600 shrink-0" />
            <span>지금은 이것만 기억해도 충분해요!</span>
          </div>
        </div>
      }
    />
  );
}
