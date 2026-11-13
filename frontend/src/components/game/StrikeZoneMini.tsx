
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import type { PitchDetail } from '../../data/mockGameData';
import { Target, Info } from 'lucide-react';

interface StrikeZoneMiniProps {
  currentPitch: PitchDetail;
  pitchesHistory?: PitchDetail[];
  showAllPitches?: boolean;
}

type VisualPitch = PitchDetail & {
  zoneAvailable?: boolean;
};

function isZoneAvailable(pitch: VisualPitch): boolean {
  return (
    pitch.zoneAvailable !== false &&
    Number.isFinite(pitch.zoneLocation?.x) &&
    Number.isFinite(pitch.zoneLocation?.y)
  );
}

function formatSpeed(speed: number): string {
  return speed > 0 ? `${speed}km/h` : '구속 미기록';
}

export function StrikeZoneMini({
  currentPitch,
  pitchesHistory = [],
  showAllPitches = false,
}: StrikeZoneMiniProps) {
  const [hoveredPitch, setHoveredPitch] =
    useState<number | null>(null);

  const current = currentPitch as VisualPitch;
  const currentAvailable = isZoneAvailable(current);

  const visibleHistory = showAllPitches
    ? pitchesHistory.filter(
        (pitch) =>
          pitch.pitchNumber !== currentPitch.pitchNumber &&
          isZoneAvailable(pitch as VisualPitch)
      )
    : [];

  const availableCount = pitchesHistory.filter(
    (pitch) => isZoneAvailable(pitch as VisualPitch)
  ).length;

  return (
    <div className="w-full bg-slate-50/80 rounded-2xl p-4 border border-gray-100 flex flex-col items-center">

      {/* 제목 */}
      <div className="w-full flex items-center justify-between text-xs text-gray-500 mb-3 px-1">
        <div className="flex items-center gap-1.5 font-bold text-gray-700">
          <Target className="w-3.5 h-3.5 text-purple-600" />
          <span>투구 탄착점 시각화</span>
        </div>

        <span className="text-[11px] font-semibold text-purple-700 bg-purple-100/70 px-2 py-0.5 rounded-md">
          포수 시점
        </span>
      </div>

      {/* 스트라이크존 전체 프레임 */}
      <div className="relative w-44 h-52 sm:w-48 sm:h-56 bg-white rounded-xl border border-dashed border-gray-300 shadow-inner flex items-center justify-center p-3 select-none">

        {/* 바깥 경계 */}
        <div className="absolute inset-2 border border-dashed border-gray-200/80 rounded pointer-events-none" />

        {/* 3x3 스트라이크존 */}
        <div className="relative w-28 h-36 sm:w-32 sm:h-40 border-2 border-purple-500/80 bg-purple-500/5 shadow-xs rounded-md">

          <div className="absolute inset-0 grid grid-cols-3 grid-rows-3">
            {Array.from({ length: 9 }).map((_, index) => (
              <div
                key={index}
                className="border border-purple-200/60"
              />
            ))}
          </div>

          <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[9px] font-bold text-gray-400 whitespace-nowrap">
            존 상단
          </span>

          <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[9px] font-bold text-gray-400 whitespace-nowrap">
            존 하단
          </span>
        </div>

        {/* 이전 투구 위치 */}
        {visibleHistory.map((pitch, index) => (
          <div
            key={`${pitch.pitchNumber}-${index}`}
            style={{
              left: `${pitch.zoneLocation.x}%`,
              top: `${pitch.zoneLocation.y}%`,
            }}
            className="absolute -translate-x-1/2 -translate-y-1/2 z-10 w-5 h-5 rounded-full bg-gray-200 border border-gray-400 text-[10px] font-black text-gray-600 flex items-center justify-center cursor-help opacity-80 hover:opacity-100 hover:scale-125 transition-all shadow-xs"
            title={`${pitch.pitchNumber}구 ${pitch.pitchType} (${formatSpeed(pitch.speedKm)}) · ${pitch.result}`}
          >
            {pitch.pitchNumber}
          </div>
        ))}

        {/* 현재 선택된 마지막 투구 */}
        {currentAvailable && (
          <div
            key={`pitch-${currentPitch.pitchNumber}-${currentPitch.zoneLocation.x}-${currentPitch.zoneLocation.y}`}
            style={{
              left: `${currentPitch.zoneLocation.x}%`,
              top: `${currentPitch.zoneLocation.y}%`,
            }}
            onMouseEnter={() =>
              setHoveredPitch(currentPitch.pitchNumber)
            }
            onMouseLeave={() =>
              setHoveredPitch(null)
            }
            className="absolute -translate-x-1/2 -translate-y-1/2 z-20 group cursor-help animate-in zoom-in-50 fade-in duration-300"
          >
            <span className="absolute -inset-1 rounded-full bg-purple-500 opacity-40 animate-ping" />

            <div className="relative w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-purple-600 border-2 border-white shadow-md text-white flex items-center justify-center text-xs font-black">
              {currentPitch.pitchNumber}
            </div>

            <div
              className={`absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 flex-col items-center pointer-events-none whitespace-nowrap z-30 ${
                hoveredPitch === currentPitch.pitchNumber
                  ? 'flex'
                  : 'hidden group-hover:flex'
              }`}
            >
              <div className="bg-gray-900 text-white text-[10px] font-bold px-2 py-1 rounded shadow-lg">
                {currentPitch.pitchNumber}구{' '}
                {currentPitch.pitchType}{' '}
                ({formatSpeed(currentPitch.speedKm)})
              </div>

              <div className="w-1.5 h-1.5 bg-gray-900 rotate-45 -mt-0.5" />
            </div>
          </div>
        )}

        {/* 위치 데이터가 없는 경우 */}
        {!currentAvailable &&
          visibleHistory.length === 0 && (
            <div className="absolute inset-x-3 top-1/2 -translate-y-1/2 z-20 flex justify-center pointer-events-none">
              <div className="rounded-lg bg-white/95 border border-gray-200 shadow-sm px-3 py-2 text-center">
                <Info className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                <span className="text-[10px] font-semibold text-gray-500">
                  탄착점 위치 미제공
                </span>
              </div>
            </div>
          )}

        {/* 홈플레이트 */}
        <div
          className="absolute bottom-1 w-12 h-4 bg-gray-200 border border-gray-400 opacity-60"
          style={{
            clipPath:
              'polygon(0% 0%, 100% 0%, 100% 40%, 50% 100%, 0% 40%)',
          }}
          title="홈플레이트"
        />
      </div>

      {/* 투구 정보 */}
      <div className="mt-3 text-center max-w-full">
        <div className="inline-flex flex-wrap items-center justify-center gap-1 text-xs font-bold text-purple-700 bg-purple-50 px-3 py-1.5 rounded-xl border border-purple-100">
          <span>
            {currentPitch.pitchNumber}구 {currentPitch.pitchType}
          </span>

          <span className="text-purple-300">·</span>

          <span>{currentPitch.result}</span>
        </div>
      </div>

      {/* 위치 제공 여부 */}
      <div className="mt-2 text-[11px] text-gray-500 text-center">
        {currentAvailable
          ? '보라색 공은 마지막 투구의 기록된 위치예요.'
          : '마지막 투구의 위치 정보가 없어 탄착점을 표시하지 않았어요.'}
      </div>

      {showAllPitches && (
        <div className="mt-2 text-[11px] text-gray-400 text-center">
          위치 확인 가능한 투구 {availableCount}개
          / 전체 {pitchesHistory.length}개
        </div>
      )}
    </div>
  );
}
