
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { User } from 'lucide-react';
import {
  ExplanationLevel,
  MOCK_RECENT_GAMES,
  MOCK_RECENT_TERMS,
  getFavoriteTeamInfo,
} from '../../data/mockMyData';

import { MyTeamCard } from './MyTeamCard';
import { MySettingsCard } from './MySettingsCard';
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

  // AI explanation level
  const [explanationLevel, setExplanationLevel] =
    useState<ExplanationLevel>(() => {
      const stored = localStorage.getItem('explanationLevel');

      if (
        stored === 'beginner' ||
        stored === 'standard' ||
        stored === 'detailed'
      ) {
        return stored;
      }

      return 'beginner';
    });

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

  const handleChangeLevel = (level: ExplanationLevel) => {
    setExplanationLevel(level);
    localStorage.setItem('explanationLevel', level);
  };

  const favoriteTeamInfo = getFavoriteTeamInfo(favoriteTeamName);

  return (
    <div className="w-full py-8 lg:py-12 animate-fadeIn">
      <div className="max-w-[1350px] mx-auto px-4 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="mb-8 lg:mb-10">
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

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">

          {/* Left column */}
          <div className="lg:col-span-5 space-y-6">
            <MyTeamCard
              team={favoriteTeamInfo}
              onNavigate={onNavigate}
            />

            <MySettingsCard
              explanationLevel={explanationLevel}
              onChangeLevel={handleChangeLevel}
              onNavigate={onNavigate}
            />
          </div>

          {/* Right column */}
          <div className="lg:col-span-7 space-y-6">
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
