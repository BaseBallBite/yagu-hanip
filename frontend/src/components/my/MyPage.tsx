
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { User, Settings, HelpCircle } from 'lucide-react';
import {
  MOCK_RECENT_GAMES,
  MOCK_RECENT_TERMS,
  getFavoriteTeamInfo,
} from '../../data/mockMyData';

import { MyTeamCard } from './MyTeamCard';
import { RecentActivityCard } from './RecentActivityCard';

export interface MyPageProps {
  onNavigate: (path: string) => void;
}

const RECENT_TERMS_KEY = 'yagu_recent_terms';

function loadRecentTerms(): typeof MOCK_RECENT_TERMS {
  try {
    const stored = localStorage.getItem(RECENT_TERMS_KEY);
    if (!stored) return [];

    const parsed: unknown = JSON.parse(stored);
    return Array.isArray(parsed)
      ? (parsed as typeof MOCK_RECENT_TERMS)
      : [];
  } catch {
    return [];
  }
}

export function MyPage({ onNavigate }: MyPageProps) {
  // Favorite team
  const [favoriteTeamName, setFavoriteTeamName] = useState<string | null>(
    () => localStorage.getItem('favoriteTeam')
  );

  // Recent dictionary activity: no initial mock records
  const [recentTerms, setRecentTerms] =
    useState<typeof MOCK_RECENT_TERMS>(loadRecentTerms);

  useEffect(() => {
    const syncFromStorage = () => {
      setFavoriteTeamName(localStorage.getItem('favoriteTeam'));
      setRecentTerms(loadRecentTerms());
    };

    // Sync when returning to this page or when another tab updates storage
    syncFromStorage();

    window.addEventListener('storage', syncFromStorage);
    window.addEventListener('focus', syncFromStorage);
    window.addEventListener('yagu-recent-terms-updated', syncFromStorage);

    return () => {
      window.removeEventListener('storage', syncFromStorage);
      window.removeEventListener('focus', syncFromStorage);
      window.removeEventListener(
        'yagu-recent-terms-updated',
        syncFromStorage
      );
    };
  }, []);

  const favoriteTeamInfo = getFavoriteTeamInfo(favoriteTeamName);

  return (
    <div className="w-full py-8 lg:py-12 animate-fadeIn">
      <div className="max-w-[1350px] mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="mb-8 lg:mb-10 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 text-purple-700 text-xs font-bold border border-purple-100 mb-3 shadow-2xs">
            <User className="w-3.5 h-3.5 text-purple-600" />
            <span>개인화 대시보드</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight mb-2.5">
            MY
          </h1>

          <p className="text-sm sm:text-base text-gray-500 leading-relaxed max-w-2xl">
            내가 응원하는 팀과 최근 본 경기, 찾아본 야구 용어를
            한곳에서 확인해보세요.
          </p>
          </div>
          <div className="flex flex-wrap gap-2 sm:pt-2">
            <button type="button" onClick={() => onNavigate('/team-select')} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-700 hover:border-purple-300 hover:text-purple-700"><Settings className="w-4 h-4"/> 응원 팀 변경</button>
            <button type="button" onClick={() => onNavigate('/guide')} className="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs font-bold text-gray-700 hover:border-purple-300 hover:text-purple-700"><HelpCircle className="w-4 h-4"/> 이용 가이드</button>
          </div>
        </div>

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">

          {/* Left column */}
          <div className="min-w-0 h-full">
            <MyTeamCard team={favoriteTeamInfo} onNavigate={onNavigate} />
          </div>

          {/* Right column */}
          <div className="lg:col-span-2 min-w-0 h-full">
            <RecentActivityCard
              games={MOCK_RECENT_GAMES}
              terms={recentTerms}
              onNavigate={onNavigate}
            />
          </div>

        </div>
      </div>
    </div>
  );
}
