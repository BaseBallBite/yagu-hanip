/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  VolumeX, 
  Maximize2, 
  Sparkles,
  Tv
} from 'lucide-react';
import { HighlightItem } from '../../data/mockHighlightsData';

interface MockVideoPlayerProps {
  scene: HighlightItem;
}

export function MockVideoPlayer({ scene }: MockVideoPlayerProps) {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentSeconds, setCurrentSeconds] = useState<number>(24);

  // When scene changes, reset mock play state
  useEffect(() => {
    setIsPlaying(false);
    setCurrentSeconds(Math.min(24, Math.floor(scene.video.durationSec * 0.35)));
  }, [scene.id]);

  // Mock progress ticker when playing
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentSeconds((prev) => {
          if (prev >= scene.video.durationSec) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, scene.video.durationSec]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const progressPercent = Math.min(100, (currentSeconds / scene.video.durationSec) * 100);

  return (
    <div className="w-full rounded-2xl overflow-hidden bg-slate-950 text-white relative shadow-lg group select-none">
      
      {/* Video Viewport / Backdrop Canvas */}
      <div 
        className="relative w-full h-[260px] sm:h-[340px] md:h-[380px] bg-gradient-to-tr from-slate-950 via-purple-950/70 to-slate-900 flex items-center justify-center cursor-pointer overflow-hidden"
        onClick={() => setIsPlaying(!isPlaying)}
      >
        {/* Stadium Grass / Field Graphic Lines (Stylized Broadcast Feel) */}
        <div className="absolute inset-0 opacity-15 pointer-events-none">
          <div className="absolute inset-0 bg-[radial-gradient(#9333ea_1px,transparent_1px)] [background-size:16px_16px]" />
          <div className="absolute top-1/2 left-0 right-0 h-px bg-white/20" />
          <div className="absolute top-0 bottom-0 left-1/2 w-px bg-white/20" />
        </div>

        {/* Dynamic Broadcast Tag */}
        <div className="absolute top-3.5 left-4 flex items-center gap-2 z-10">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-[11px] font-extrabold text-white border border-white/10">
            <span className={`w-2 h-2 rounded-full ${isPlaying ? 'bg-red-500 animate-ping' : 'bg-red-500'}`} />
            <span>KBO 하이라이트</span>
          </span>
          <span className="px-2.5 py-1 rounded-full bg-purple-600/80 backdrop-blur-md text-[11px] font-bold text-white">
            {scene.inning}
          </span>
        </div>

        {/* Center Big Play/Pause Button */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setIsPlaying(!isPlaying);
          }}
          className={`w-16 h-16 sm:w-18 sm:h-18 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl z-20 cursor-pointer ${
            isPlaying
              ? 'bg-black/50 hover:bg-black/70 text-white scale-90 opacity-0 group-hover:opacity-100'
              : 'bg-purple-600 hover:bg-purple-500 text-white shadow-purple-600/50 scale-100 hover:scale-110'
          }`}
          aria-label={isPlaying ? '일시정지' : '재생'}
        >
          {isPlaying ? (
            <Pause className="w-7 h-7 sm:w-8 sm:h-8 fill-current" />
          ) : (
            <Play className="w-7 h-7 sm:w-8 sm:h-8 fill-current ml-1" />
          )}
        </button>

        {/* Broadcast Title Badge at Center Bottom */}
        <div className="absolute bottom-14 left-4 right-4 flex items-end justify-between pointer-events-none z-10">
          <div className="bg-black/65 backdrop-blur-md p-2.5 sm:p-3 rounded-xl border border-white/15 max-w-md">
            <div className="text-xs font-semibold text-purple-300 mb-0.5">
              {scene.playerName} ({scene.playerTeam})
            </div>
            <div className="text-sm sm:text-base font-black text-white tracking-tight">
              {scene.playResult}
            </div>
          </div>
          <span className="hidden sm:inline-block text-[10px] text-gray-400 bg-black/50 px-2 py-1 rounded">
            Mock Video Player
          </span>
        </div>

      </div>

      {/* Video Control Bar */}
      <div className="bg-slate-900/95 backdrop-blur-md px-4 py-3 flex flex-col gap-2 border-t border-white/10">
        
        {/* Timeline Scrubber */}
        <div 
          className="w-full bg-gray-700/80 h-1.5 hover:h-2.5 rounded-full cursor-pointer relative transition-all"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clickPercent = (e.clientX - rect.left) / rect.width;
            setCurrentSeconds(Math.floor(clickPercent * scene.video.durationSec));
          }}
        >
          <div 
            className="bg-purple-500 h-full rounded-full relative transition-all"
            style={{ width: `${progressPercent}%` }}
          >
            <span className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-md scale-0 group-hover:scale-100 transition-transform" />
          </div>
        </div>

        {/* Buttons & Time Row */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              className="hover:text-purple-400 transition cursor-pointer p-1"
            >
              {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
            </button>

            <button
              type="button"
              onClick={() => setCurrentSeconds(0)}
              className="hover:text-purple-400 transition cursor-pointer p-1"
              title="처음부터 다시보기"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            <div className="font-mono text-gray-300 text-[11px] ml-1">
              <span className="text-white font-bold">{formatTime(currentSeconds)}</span>
              <span className="text-gray-500 mx-1">/</span>
              <span>{formatTime(scene.video.durationSec)}</span>
            </div>
          </div>

          <div className="flex items-center gap-3 text-gray-300">
            <button
              type="button"
              onClick={() => setIsMuted(!isMuted)}
              className="hover:text-white transition cursor-pointer p-1"
            >
              {isMuted ? <VolumeX className="w-4 h-4 text-red-400" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <button
              type="button"
              className="hover:text-white transition cursor-pointer p-1"
              title="전체화면"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>

    </div>
  );
}
