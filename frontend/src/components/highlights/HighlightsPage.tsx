/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { 
  MOCK_HIGHLIGHT_GAMES, 
  MOCK_HIGHLIGHT_SCENES,
  HighlightGame,
  HighlightItem
} from '../../data/mockHighlightsData';
import { HighlightSceneList } from './HighlightSceneList';
import { HighlightDetailPanel } from './HighlightDetailPanel';
import { Sparkles, Video, Calendar, ChevronDown } from 'lucide-react';

export function HighlightsPage() {
  const [selectedGameId, setSelectedGameId] = useState<string>('game-0930');
  
  // Default to the 2nd scene ("5회초 박재현 만루 3루타") as requested in prompt
  const [selectedSceneId, setSelectedSceneId] = useState<string>('hl-0930-2');

  const currentGame: HighlightGame = 
    MOCK_HIGHLIGHT_GAMES.find((g) => g.id === selectedGameId) || MOCK_HIGHLIGHT_GAMES[0];

  const currentScenes: HighlightItem[] = 
    MOCK_HIGHLIGHT_SCENES[selectedGameId] || MOCK_HIGHLIGHT_SCENES['game-0930'];

  const currentScene: HighlightItem = 
    currentScenes.find((s) => s.id === selectedSceneId) || currentScenes[0];

  const handleSelectGame = (gameId: string) => {
    setSelectedGameId(gameId);
    const scenesForGame = MOCK_HIGHLIGHT_SCENES[gameId] || [];
    if (scenesForGame.length > 0) {
      // If switching to game-0930 pick the 2nd scene, else pick 1st
      if (gameId === 'game-0930') {
        setSelectedSceneId('hl-0930-2');
      } else {
        setSelectedSceneId(scenesForGame[0].id);
      }
    }
  };

  return (
    <div className="w-full flex-1 py-6 sm:py-8 animate-fade-in">
      <div className="max-w-[1350px] w-full mx-auto px-4 sm:px-6">
        
        {/* Top Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-5 border-b border-gray-200/70">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/90 text-purple-700 text-xs font-bold mb-2">
              <Sparkles className="w-3.5 h-3.5 text-purple-600" />
              <span>AI 경기 맥락 해설</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight">
              경기 하이라이트
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              놓친 장면을 다시 보고, AI에게 그 장면의 맥락도 물어보세요.
            </p>
          </div>

          {/* Right: Date / Match Indicator Dropdown UI */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <div className="bg-white rounded-2xl px-4 py-2.5 border border-gray-200 shadow-xs flex items-center gap-2.5 text-xs font-bold text-gray-700">
              <Calendar className="w-4 h-4 text-purple-600" />
              <span>현재 선택 경기:</span>
              <span className="text-purple-700 font-extrabold">{currentGame.title}</span>
            </div>
          </div>
        </div>

        {/* Main 2-Column Desktop Grid (Left ~38~40% col-span-5, Right ~60~62% col-span-7) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column: Match & Scene List */}
          <div className="lg:col-span-5 w-full">
            <HighlightSceneList
              games={MOCK_HIGHLIGHT_GAMES}
              selectedGameId={selectedGameId}
              onSelectGame={handleSelectGame}
              scenes={currentScenes}
              selectedSceneId={selectedSceneId}
              onSelectScene={(id) => setSelectedSceneId(id)}
            />
          </div>

          {/* Right Column: Video Player & AI Context Explanation */}
          <div className="lg:col-span-7 w-full">
            <HighlightDetailPanel scene={currentScene} />
          </div>

        </div>

      </div>
    </div>
  );
}
