/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { 
  HighlightGame, 
  HighlightItem 
} from '../../data/mockHighlightsData';
import { 
  Play, 
  Calendar, 
  Layers, 
  CheckCircle2, 
  Clock, 
  Video 
} from 'lucide-react';

interface HighlightSceneListProps {
  games: HighlightGame[];
  selectedGameId: string;
  onSelectGame: (gameId: string) => void;
  scenes: HighlightItem[];
  selectedSceneId: string;
  onSelectScene: (sceneId: string) => void;
}

export function HighlightSceneList({
  games,
  selectedGameId,
  onSelectGame,
  scenes,
  selectedSceneId,
  onSelectScene,
}: HighlightSceneListProps) {
  return (
    <div className="w-full bg-white rounded-3xl p-5 sm:p-6 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col gap-6">
      
      {/* 1. 하이라이트 경기 선택 섹션 */}
      <div>
        <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
              <Calendar className="w-4 h-4 text-purple-600" />
            </div>
            <h2 className="text-sm sm:text-base font-black text-gray-900 tracking-tight">
              하이라이트 경기
            </h2>
          </div>
          <span className="text-[11px] font-semibold text-gray-400">
            총 {games.length}경기
          </span>
        </div>

        {/* 3 Match Cards */}
        <div className="space-y-2">
          {games.map((g) => {
            const isSelected = g.id === selectedGameId;

            return (
              <button
                key={g.id}
                type="button"
                onClick={() => onSelectGame(g.id)}
                className={`w-full p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-center justify-between group ${
                  isSelected
                    ? 'bg-purple-50/80 border-2 border-purple-600 ring-2 ring-purple-300/40 shadow-xs'
                    : 'bg-gray-50/70 border-gray-200/80 hover:bg-white hover:border-purple-300 hover:shadow-xs'
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-gray-400">{g.date}</span>
                    <span className="text-sm font-black text-gray-900 group-hover:text-purple-700 transition-colors">
                      {g.homeTeam} vs {g.awayTeam}
                    </span>
                    {isSelected && (
                      <span className="text-[10px] font-bold text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded">
                        선택
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-500 font-medium mt-0.5">
                    하이라이트 장면 {g.scenesCount}개
                  </div>
                </div>

                <div className={`w-5 h-5 rounded-full flex items-center justify-center transition-all ${
                  isSelected 
                    ? 'bg-purple-600 text-white shadow-xs' 
                    : 'border border-gray-300 text-transparent group-hover:border-purple-300'
                }`}>
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. 선택된 경기의 주요 장면 목록 */}
      <div>
        <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center">
              <Video className="w-4 h-4 text-purple-600" />
            </div>
            <h3 className="text-sm sm:text-base font-black text-gray-900 tracking-tight">
              주요 하이라이트 클립
            </h3>
          </div>
          <span className="text-[11px] font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full">
            {scenes.length}개 클립
          </span>
        </div>

        {/* Scene Cards Stack */}
        <div className="space-y-2.5">
          {scenes.map((scene) => {
            const isSelected = scene.id === selectedSceneId;

            return (
              <button
                key={scene.id}
                type="button"
                onClick={() => onSelectScene(scene.id)}
                className={`w-full p-3.5 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-center gap-3.5 group relative overflow-hidden ${
                  isSelected
                    ? 'bg-purple-50/70 border-2 border-purple-600 ring-2 ring-purple-300/40 shadow-md shadow-purple-600/10 -translate-y-0.5'
                    : 'bg-white border-gray-200/80 hover:border-purple-300 hover:shadow-xs hover:-translate-y-0.5'
                }`}
              >
                {/* Scene Number Index Pill */}
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-black text-xs shrink-0 transition-colors ${
                  isSelected 
                    ? 'bg-purple-600 text-white shadow-xs' 
                    : 'bg-gray-100 text-gray-500 group-hover:bg-purple-100 group-hover:text-purple-700'
                }`}>
                  {scene.sceneNumber}
                </div>

                {/* Small Thumbnail Placeholder with Play Icon */}
                <div className="w-16 h-12 rounded-xl bg-gradient-to-tr from-slate-900 via-purple-900 to-slate-800 flex items-center justify-center shrink-0 relative overflow-hidden shadow-2xs">
                  <Play className={`w-4 h-4 fill-white text-white transition-transform ${isSelected ? 'scale-110 text-yellow-300 fill-yellow-300' : 'group-hover:scale-110'}`} />
                  <span className="absolute bottom-1 right-1 text-[9px] font-mono text-white/90 bg-black/60 px-1 rounded">
                    {scene.video.durationFormatted}
                  </span>
                </div>

                {/* Scene Content Text */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-purple-700 bg-purple-100/80 px-2 py-0.5 rounded-md">
                      {scene.inning}
                    </span>
                    <span className="text-xs font-semibold text-gray-500 truncate">
                      {scene.playerName}
                    </span>
                  </div>
                  <div className="text-sm font-extrabold text-gray-900 group-hover:text-purple-700 transition-colors mt-0.5 truncate">
                    {scene.playResult}
                  </div>
                </div>

                {/* Play Indicator on Right */}
                <div className="shrink-0 text-gray-300 group-hover:text-purple-600 transition-colors">
                  <Play className={`w-4 h-4 fill-current ${isSelected ? 'text-purple-600' : ''}`} />
                </div>
              </button>
            );
          })}
        </div>
      </div>

    </div>
  );
}
