/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { Sparkles, User, ShieldCheck } from 'lucide-react';
import { 
  ExplanationLevel, 
  SavedQuestion, 
  INITIAL_SAVED_QUESTIONS,
  MOCK_RECENT_GAMES,
  MOCK_RECENT_TERMS,
  getFavoriteTeamInfo
} from '../../data/mockMyData';
import { MyTeamCard } from './MyTeamCard';
import { MySettingsCard } from './MySettingsCard';
import { SavedQuestionsCard } from './SavedQuestionsCard';
import { RecentActivityCard } from './RecentActivityCard';

export interface MyPageProps {
  onNavigate: (path: string) => void;
}

export function MyPage({ onNavigate }: MyPageProps) {
  // 1. Favorite Team State synchronized from localStorage
  const [favoriteTeamName, setFavoriteTeamName] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('favoriteTeam');
      // If user hasn't explicitly chosen yet, provide KIA as friendly default demonstration
      return stored !== null ? stored : 'KIA';
    }
    return 'KIA';
  });

  // 2. Explanation Difficulty Level State (Default: 'beginner')
  const [explanationLevel, setExplanationLevel] = useState<ExplanationLevel>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('explanationLevel') as ExplanationLevel;
      if (['beginner', 'standard', 'detailed'].includes(stored)) {
        return stored;
      }
    }
    return 'beginner';
  });

  // 3. Saved Questions State with Mock interactive deletion & restoration
  const [savedQuestions, setSavedQuestions] = useState<SavedQuestion[]>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('savedQuestions');
      if (stored) {
        try {
          return JSON.parse(stored);
        } catch {
          // fallback to initial
        }
      }
    }
    return INITIAL_SAVED_QUESTIONS;
  });

  // Listen for storage events or window focus in case team was changed on another page
  useEffect(() => {
    const handleStorage = () => {
      if (typeof window !== 'undefined') {
        const storedTeam = localStorage.getItem('favoriteTeam');
        setFavoriteTeamName(storedTeam);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const handleChangeLevel = (level: ExplanationLevel) => {
    setExplanationLevel(level);
    if (typeof window !== 'undefined') {
      localStorage.setItem('explanationLevel', level);
    }
  };

  const handleDeleteQuestion = (id: string) => {
    setSavedQuestions((prev) => {
      const updated = prev.filter((q) => q.id !== id);
      if (typeof window !== 'undefined') {
        localStorage.setItem('savedQuestions', JSON.stringify(updated));
      }
      return updated;
    });
  };

  const handleRestoreQuestions = () => {
    setSavedQuestions(INITIAL_SAVED_QUESTIONS);
    if (typeof window !== 'undefined') {
      localStorage.setItem('savedQuestions', JSON.stringify(INITIAL_SAVED_QUESTIONS));
    }
  };

  const favoriteTeamInfo = getFavoriteTeamInfo(favoriteTeamName);

  return (
    <div className="w-full py-8 lg:py-12 animate-fadeIn">
      <div className="max-w-[1350px] mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Page Top Header Section */}
        <div className="mb-8 lg:mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-50 text-purple-700 text-xs font-bold border border-purple-100 mb-3 shadow-2xs">
            <User className="w-3.5 h-3.5 text-purple-600" />
            <span>개인화 대시보드</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-black text-gray-900 tracking-tight mb-2.5">
            MY
          </h1>
          <p className="text-sm sm:text-base text-gray-500 leading-relaxed max-w-2xl">
            내가 응원하는 팀과 저장한 질문, 최근 본 경기와 야구 용어를 한곳에서 확인해보세요.
          </p>
        </div>

        {/* Main Content: Two-Column Responsive Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-start">
          
          {/* LEFT COLUMN: ~38% (lg:col-span-5 or col-span-4 / col-span-5) */}
          <div className="lg:col-span-5 space-y-6">
            {/* My Team Card */}
            <MyTeamCard 
              team={favoriteTeamInfo} 
              onNavigate={onNavigate} 
            />

            {/* Personal Settings & AI Level */}
            <MySettingsCard
              explanationLevel={explanationLevel}
              onChangeLevel={handleChangeLevel}
              onNavigate={onNavigate}
            />
          </div>

          {/* RIGHT COLUMN: ~62% (lg:col-span-7) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Saved Questions with Expandable Answer Preview */}
            <SavedQuestionsCard
              questions={savedQuestions}
              onDeleteQuestion={handleDeleteQuestion}
              onRestoreQuestions={handleRestoreQuestions}
              onNavigate={onNavigate}
            />

            {/* Recent Activity: Watched Matches & Searched Terms Chips */}
            <RecentActivityCard
              games={MOCK_RECENT_GAMES}
              terms={MOCK_RECENT_TERMS}
              onNavigate={onNavigate}
            />
          </div>

        </div>
      </div>
    </div>
  );
}
