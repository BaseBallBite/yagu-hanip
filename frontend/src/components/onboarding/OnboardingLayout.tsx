/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { ArrowRight, ChevronRight } from 'lucide-react';
import { ProgressDots } from './ProgressDots';

export interface OnboardingLayoutProps {
  currentStep?: number;
  totalSteps?: number;
  onSkip: () => void;
  onNext: () => void;
  onPrev?: () => void;
  prevButtonLabel?: string;
  nextButtonLabel?: string;
  leftContent: React.ReactNode;
  rightContent: React.ReactNode;
  stepIndicatorVisible?: boolean;
  leftColClass?: string;
  rightColClass?: string;
}

export function OnboardingLayout({
  currentStep = 1,
  totalSteps = 3,
  onSkip,
  onNext,
  onPrev,
  prevButtonLabel = '이전',
  nextButtonLabel = '다음',
  leftContent,
  rightContent,
  stepIndicatorVisible = true,
  leftColClass = 'lg:col-span-5',
  rightColClass = 'lg:col-span-7',
}: OnboardingLayoutProps) {
  return (
    <div className="w-full flex-1 flex flex-col justify-between py-6 sm:py-10 animate-fade-in">
      <div className="max-w-[1150px] w-full mx-auto px-6">
        
        {/* Top Bar inside Onboarding: Skip link in top-right */}
        <div className="flex items-center justify-between pb-6 mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-purple-700 bg-purple-50 px-3 py-1 rounded-full border border-purple-100">
              입문 온보딩 {currentStep}/{totalSteps}
            </span>
          </div>

          <button
            onClick={onSkip}
            className="text-sm font-semibold text-gray-500 hover:text-purple-600 transition-colors flex items-center gap-1 px-3 py-1.5 rounded-lg hover:bg-purple-50 cursor-pointer"
          >
            <span>건너뛰기</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* 2-Column Desktop Grid: Left ~35-45%, Right ~55-65%, 1-column on mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          
          {/* Left Visual Area */}
          <div className={`${leftColClass} w-full flex justify-center`}>
            {leftContent}
          </div>

          {/* Right Explanation & Cards Area */}
          <div className={`${rightColClass} w-full flex flex-col justify-center`}>
            {rightContent}
          </div>

        </div>

        {/* Bottom Navigation & Progress Indicator Bar */}
        <div className="mt-12 sm:mt-16 pt-6 border-t border-gray-200/60 flex flex-col sm:flex-row items-center justify-between gap-5">
          {/* Left area: Previous button if provided, otherwise Progress Indicator */}
          <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-start">
            {onPrev ? (
              <button
                onClick={onPrev}
                className="px-5 py-3 rounded-2xl border border-gray-200 hover:border-purple-300 text-gray-700 hover:text-purple-700 font-semibold text-sm transition-all duration-200 hover:bg-white flex items-center gap-2 cursor-pointer shadow-xs active:scale-95"
              >
                <span>{prevButtonLabel}</span>
              </button>
            ) : null}

            {/* Progress Indicator */}
            <div className="flex items-center gap-3">
              {stepIndicatorVisible && (
                <ProgressDots currentStep={currentStep} totalSteps={totalSteps} />
              )}
              <span className="text-xs text-gray-400 font-medium hidden sm:inline">
                {totalSteps}단계 중 {currentStep}단계
              </span>
            </div>
          </div>

          {/* Right area: Next Button */}
          <div className="flex items-center gap-4 w-full sm:w-auto">
            <button
              onClick={onNext}
              className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-purple-600 hover:bg-purple-700 active:bg-purple-800 text-white font-bold text-base shadow-lg shadow-purple-600/20 hover:shadow-xl hover:shadow-purple-600/30 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center gap-2 group cursor-pointer"
            >
              <span>{nextButtonLabel}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
