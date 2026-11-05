/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';

export interface ProgressDotsProps {
  totalSteps?: number;
  currentStep: number; // 1-indexed
  className?: string;
}

export function ProgressDots({
  totalSteps = 3,
  currentStep = 1,
  className = '',
}: ProgressDotsProps) {
  return (
    <div className={`flex items-center gap-2 ${className}`} aria-label={`단계 ${currentStep} / ${totalSteps}`}>
      {Array.from({ length: totalSteps }).map((_, index) => {
        const stepNumber = index + 1;
        const isActive = stepNumber === currentStep;
        const isCompleted = stepNumber < currentStep;

        return (
          <span
            key={index}
            className={`transition-all duration-300 rounded-full ${
              isActive
                ? 'w-6 h-2.5 bg-purple-600'
                : isCompleted
                ? 'w-2.5 h-2.5 bg-purple-400'
                : 'w-2.5 h-2.5 bg-gray-300'
            }`}
            title={`단계 ${stepNumber}`}
          />
        );
      })}
    </div>
  );
}
