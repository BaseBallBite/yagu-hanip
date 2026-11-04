/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { HelpCircle, Sparkles } from 'lucide-react';

export function BeginnerHelpBox() {
  return (
    <div className="w-full bg-purple-50/70 rounded-2xl p-4 sm:p-5 border border-purple-100 shadow-xs mt-6 text-left">
      <div className="flex items-center gap-2 mb-2.5 text-purple-900 font-extrabold text-xs sm:text-sm">
        <HelpCircle className="w-4 h-4 text-purple-600" />
        <span>순위표가 어려워요? (초보자 야구 가이드)</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs text-gray-700">
        <div className="bg-white/80 p-2.5 rounded-xl border border-purple-100/60 shadow-2xs">
          <span className="font-extrabold text-purple-700 mr-1.5">승</span>
          <span className="text-gray-600 font-medium">이긴 경기 수</span>
        </div>

        <div className="bg-white/80 p-2.5 rounded-xl border border-purple-100/60 shadow-2xs">
          <span className="font-extrabold text-purple-700 mr-1.5">패</span>
          <span className="text-gray-600 font-medium">진 경기 수</span>
        </div>

        <div className="bg-white/80 p-2.5 rounded-xl border border-purple-100/60 shadow-2xs">
          <span className="font-extrabold text-purple-700 mr-1.5">승률</span>
          <span className="text-gray-600 font-medium">이긴 경기 비율 (승 ÷ (승+패))</span>
        </div>

        <div className="bg-white/80 p-2.5 rounded-xl border border-purple-100/60 shadow-2xs">
          <span className="font-extrabold text-purple-700 mr-1.5">게임차</span>
          <span className="text-gray-600 font-medium">앞선 팀과의 경기 수 격차</span>
        </div>
      </div>
    </div>
  );
}
