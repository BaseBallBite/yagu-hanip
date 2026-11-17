/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { MOCK_STANDINGS, TeamStanding } from '../../data/mockRankingData';
import { StandingsTable } from './StandingsTable';
import { TeamDetailCard } from './TeamDetailCard';
import { BeginnerHelpBox } from './BeginnerHelpBox';
import { Calendar, Sparkles, ChevronDown, Heart } from 'lucide-react';

interface RankingPageProps {
  onNavigate: (path: string) => void;
}

export function RankingPage({ onNavigate }: RankingPageProps) {
  const [favoriteTeamName, setFavoriteTeamName] = useState<string>('');
  const [selectedTeam, setSelectedTeam] = useState<TeamStanding>(() => {
    return MOCK_STANDINGS[0]; // fallback default
  });

  // On mount, check localStorage for favoriteTeam
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedFavorite = localStorage.getItem('favoriteTeam');
      if (savedFavorite && savedFavorite !== 'NONE') {
        setFavoriteTeamName(savedFavorite);
        const matched = MOCK_STANDINGS.find(
          (t) => t.name === savedFavorite || t.fullName.includes(savedFavorite)
        );
        if (matched) {
          setSelectedTeam(matched);
        }
      } else {
        // If no favorite team, default to Rank 3 KIA or Rank 1 KT
        setSelectedTeam(MOCK_STANDINGS[2]); // KIA
      }
    }
  }, []);

  const handleSelectTeam = (team: TeamStanding) => {
    setSelectedTeam(team);
  };

  return (
    <div className="w-full flex-1 py-6 sm:py-8 animate-fade-in">
      <div className="max-w-[1350px] w-full mx-auto px-4 sm:px-6">
        
        {/* Top Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-5 border-b border-gray-200/70">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/90 text-purple-700 text-xs font-bold mb-2">
              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              <span>실시간 리그 순위 분석</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
              2026 KBO 정규시즌 순위와 최근 경기 흐름
            </h1>
          </div>

          {/* Right: Season Selector UI (Mock UI) */}
          <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
            {favoriteTeamName && favoriteTeamName !== 'NONE' && (
              <div className="inline-flex items-center gap-1.5 px-3 py-2 rounded-full bg-purple-50 border border-purple-100 text-purple-700 text-xs font-bold">
                <Heart className="w-3.5 h-3.5 fill-purple-600 text-purple-600" />
                <span>MY 응원 팀: {favoriteTeamName}</span>
              </div>
            )}
            <div className="bg-white rounded-2xl px-4 py-2.5 border border-gray-200 shadow-xs flex items-center gap-2 text-xs font-bold text-gray-700 cursor-pointer hover:border-purple-300 transition-colors">
              <Calendar className="w-4 h-4 text-purple-600" />
              <span>2026 정규시즌</span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400 ml-1" />
            </div>
          </div>
        </div>

        {/* 2-Column Desktop Grid (Left ~68% col-span-8, Right ~32% col-span-4) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column: Entire Standings Table + Beginner Help Box */}
          <div className="lg:col-span-8 w-full">
            <StandingsTable
              standings={MOCK_STANDINGS}
              selectedTeamId={selectedTeam.id}
              favoriteTeamName={favoriteTeamName}
              onSelectTeam={handleSelectTeam}
            />

            {/* Beginner Help Box */}
            <BeginnerHelpBox />
          </div>

          {/* Right Column: Selected Team Details */}
          <div className="lg:col-span-4 w-full">
            <TeamDetailCard
              team={selectedTeam}
              isFavorite={favoriteTeamName === selectedTeam.name}
              onNavigateToGame={() => onNavigate('/game')}
            />
          </div>

        </div>

      </div>
    </div>
  );
}
