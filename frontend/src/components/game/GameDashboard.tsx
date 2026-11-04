/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  MOCK_GAME_SUMMARY, 
  MOCK_RECENT_GAMES, 
  MOCK_AT_BATS, 
  AtBatPlay 
} from '../../data/mockGameData';
import { GameScoreHeader } from './GameScoreHeader';
import { RecentGamesBar } from './RecentGamesBar';
import { CurrentAtBatCard } from './CurrentAtBatCard';
import { AIExplanationPanel } from './AIExplanationPanel';
import { InningPlaysHistory } from './InningPlaysHistory';

export function GameDashboard() {
  const [selectedGameId, setSelectedGameId] = useState<string>('game-1');
  const [selectedAtBatId, setSelectedAtBatId] = useState<string>('atbat-1');
  const [isLoadingAi, setIsLoadingAi] = useState<boolean>(false);
  const [hasAskedAi, setHasAskedAi] = useState<boolean>(true); // default true for rich initial demo impression, can be re-triggered

  // Find currently active at-bat
  const currentAtBatIndex = MOCK_AT_BATS.findIndex((a) => a.id === selectedAtBatId);
  const currentAtBat: AtBatPlay = MOCK_AT_BATS[currentAtBatIndex !== -1 ? currentAtBatIndex : 0];

  const handleAskWhy = () => {
    setIsLoadingAi(true);
    setTimeout(() => {
      setIsLoadingAi(false);
      setHasAskedAi(true);
    }, 450);
  };

  const handleSelectAtBat = (atBatId: string) => {
    if (atBatId !== selectedAtBatId) {
      setSelectedAtBatId(atBatId);
      // Automatically refresh explanation for the newly selected at-bat
      setIsLoadingAi(true);
      setTimeout(() => {
        setIsLoadingAi(false);
        setHasAskedAi(true);
      }, 350);
    }
  };

  const handlePrevAtBat = () => {
    if (currentAtBatIndex > 0) {
      handleSelectAtBat(MOCK_AT_BATS[currentAtBatIndex - 1].id);
    }
  };

  const handleNextAtBat = () => {
    if (currentAtBatIndex < MOCK_AT_BATS.length - 1) {
      handleSelectAtBat(MOCK_AT_BATS[currentAtBatIndex + 1].id);
    }
  };

  return (
    <div className="w-full flex-1 py-6 sm:py-8 animate-fade-in">
      <div className="max-w-[1350px] w-full mx-auto px-4 sm:px-6">
        
        {/* 1. Top Match Summary (Score, Diamond, Out count) */}
        <GameScoreHeader summary={MOCK_GAME_SUMMARY} />

        {/* 2. Recent Games Selection Bar (3 horizontal cards) */}
        <RecentGamesBar
          games={MOCK_RECENT_GAMES}
          selectedGameId={selectedGameId}
          onSelectGame={(id) => setSelectedGameId(id)}
        />

        {/* 3. Main 2-Column Dashboard (Desktop: Left ~60%, Right ~40%) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left ~60% (col-span-7): Current At-Bat & Pitch Visual */}
          <div className="lg:col-span-7 w-full">
            <CurrentAtBatCard
              atBat={currentAtBat}
              onAskWhy={handleAskWhy}
              isAiExplaining={hasAskedAi && !isLoadingAi}
            />
          </div>

          {/* Right ~40% (col-span-5): AI Explanation Panel */}
          <div className="lg:col-span-5 w-full">
            <AIExplanationPanel
              atBat={currentAtBat}
              isLoading={isLoadingAi}
              hasAsked={hasAskedAi}
              onTriggerAsk={handleAskWhy}
            />
          </div>

        </div>

        {/* 4. Bottom Section: Previous At-Bats / Plays List & Inning Navigation */}
        <InningPlaysHistory
          atBats={MOCK_AT_BATS}
          selectedAtBatId={selectedAtBatId}
          onSelectAtBat={handleSelectAtBat}
          onPrevAtBat={handlePrevAtBat}
          onNextAtBat={handleNextAtBat}
          hasPrev={currentAtBatIndex > 0}
          hasNext={currentAtBatIndex < MOCK_AT_BATS.length - 1}
        />

      </div>
    </div>
  );
}
