/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { ArrowRight, ShieldAlert, Award } from 'lucide-react';

export interface InfoCardProps {
  badgeTitle: string;
  badgeColor?: 'purple' | 'slate';
  countNumber: number | string;
  countUnit: string;
  actionText: string;
  description?: string;
  highlightColor?: string;
}

export function InfoCard({
  badgeTitle,
  badgeColor = 'purple',
  countNumber,
  countUnit,
  actionText,
  description,
}: InfoCardProps) {
  const isPurple = badgeColor === 'purple';

  return (
    <div className={`w-full bg-white rounded-2xl p-5 sm:p-6 border transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 group ${
      isPurple 
        ? 'border-purple-100 hover:border-purple-300 shadow-xs' 
        : 'border-gray-200/80 hover:border-gray-300 shadow-xs'
    }`}>
      <div className="flex items-center justify-between mb-3">
        {/* Badge Label */}
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${
          isPurple 
            ? 'bg-purple-100 text-purple-700' 
            : 'bg-gray-100 text-gray-700'
        }`}>
          {badgeTitle}
        </span>
        <span className="text-[11px] font-medium text-gray-400">
          {isPurple ? '타자 페널티' : '타자 보너스'}
        </span>
      </div>

      <div className="flex items-baseline gap-2">
        {/* Big prominent number */}
        <span className={`text-4xl sm:text-5xl font-black tracking-tight ${
          isPurple ? 'text-purple-600' : 'text-gray-800'
        }`}>
          {countNumber}
        </span>
        <span className="text-lg sm:text-xl font-bold text-gray-800">
          {countUnit}
        </span>
      </div>

      {/* Main Action Text */}
      <div className="mt-2 text-base sm:text-lg font-bold text-gray-900 flex items-center gap-2">
        <span className="text-purple-600 font-black">→</span>
        <span>{actionText}</span>
      </div>

      {/* Sub explanation if provided */}
      {description && (
        <p className="mt-2 whitespace-pre-line break-keep text-xs sm:text-sm text-gray-500 leading-relaxed font-normal">
          {description}
        </p>
      )}
    </div>
  );
}
