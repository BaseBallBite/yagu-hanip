
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import type { AtBatPlay } from '../../data/mockGameData';
import { StrikeZoneMini } from './StrikeZoneMini';
import {
  Zap,
  Sparkles,
  ListOrdered,
  Eye,
  History,
} from 'lucide-react';

interface CurrentAtBatCardProps {
  atBat: AtBatPlay;
  onAskWhy: () => void;
  isAiExplaining: boolean;
}

function formatSpeed(speed: number) {
  return speed > 0 ? `${speed}km/h` : '구속 미기록';
}

export function CurrentAtBatCard({
  atBat,
  onAskWhy,
  isAiExplaining,
}: CurrentAtBatCardProps) {
  const [showPitchDetail, setShowPitchDetail] = useState(false);

  const hasPitch = atBat.pitchesHistory.length > 0;

  const lastPitch = atBat.currentPitch;

  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-xl shadow-purple-950/5 flex flex-col justify-between transition-all duration-300">
      <div>
        {/* 타석 헤더 */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-black text-purple-700 tracking-wider">
              선택한 타석 기록
            </span>
          </div>

          <div className="text-xs font-semibold px-2.5 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-100">
            {atBat.pitchCountText} 승부
          </div>
        </div>

        {/* 타자 VS 투수 */}
        <div className="mt-4 p-4 rounded-2xl bg-gradient-to-br from-gray-50 to-purple-50/20 border border-gray-100 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
              타자 ({atBat.batterTeam})
            </div>

            <div className="text-xl sm:text-2xl font-black text-gray-900 flex flex-wrap items-baseline gap-2">
              <span>{atBat.batterName}</span>

              {atBat.batterPosition && (
                <span className="text-xs font-semibold text-gray-500">
                  {atBat.batterPosition}
                </span>
              )}
            </div>
          </div>

          <div className="shrink-0 px-3 py-1 rounded-xl bg-gray-100 text-gray-500 text-xs font-black">
            VS
          </div>

          <div className="text-right min-w-0">
            <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-0.5">
              투수 ({atBat.pitcherTeam})
            </div>

            <div className="text-xl sm:text-2xl font-black text-gray-900">
              {atBat.pitcherName}
            </div>
          </div>
        </div>

        {/* 마지막 투구와 타석 결과 */}
        <div className="mt-5 p-5 rounded-2xl bg-purple-50/50 border border-purple-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <span className="inline-flex items-center gap-1 text-xs font-bold text-purple-700 bg-purple-100 px-2.5 py-0.5 rounded-full">
                <Zap className="w-3 h-3 text-purple-600" />
                {hasPitch ? '마지막 투구' : '타석 기록'}
              </span>

              {hasPitch && (
                <span className="text-xs font-semibold text-gray-500">
                  볼 {atBat.balls} · 스트라이크 {atBat.strikes}
                </span>
              )}
            </div>

            {hasPitch ? (
              <>
                <div className="text-2xl sm:text-3xl font-black text-gray-900 tracking-tight flex flex-wrap items-baseline gap-2.5">
                  <span>
                    {lastPitch.pitchNumber}구 {lastPitch.pitchType}
                  </span>

                  <span className="text-base sm:text-lg font-bold text-purple-600">
                    {formatSpeed(lastPitch.speedKm)}
                  </span>
                </div>

                <div className="text-sm font-semibold text-gray-600 mt-1">
                  {lastPitch.result}
                </div>
              </>
            ) : (
              <div className="text-xl font-black text-gray-700">
                투구 상세 기록 없음
              </div>
            )}
          </div>

          <div className="max-w-full px-4 py-2.5 rounded-2xl bg-white border border-purple-200 shadow-sm text-purple-700 font-black text-sm sm:text-base self-stretch sm:self-auto text-center break-words">
            {atBat.resultText}
          </div>
        </div>

        {/* 투구 탄착점 */}
        {hasPitch ? (
          <div className="mt-5">
            <StrikeZoneMini
              currentPitch={lastPitch}
              pitchesHistory={atBat.pitchesHistory}
              showAllPitches={showPitchDetail}
            />
          </div>
        ) : (
          <div className="mt-5 p-6 text-center rounded-2xl bg-slate-50 border border-gray-100">
            <p className="text-sm font-medium text-gray-500">
              이 타석의 투구 위치 데이터가 제공되지 않았어요.
            </p>
          </div>
        )}

        {/* 타석별 투구 상세 */}
        {showPitchDetail && hasPitch && (
          <div className="mt-4 p-4 rounded-2xl bg-white border border-gray-200 shadow-xs animate-in fade-in duration-200">
            <div className="text-xs font-bold text-gray-500 mb-2.5 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <ListOrdered className="w-3.5 h-3.5 text-purple-600" />
                이 타석 전체 투구 기록 ({atBat.pitchesHistory.length}구)
              </span>

              <span className="text-[11px] text-gray-400">
                구종 / 구속 / 결과
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {atBat.pitchesHistory.map((pitch, index) => (
                <div
                  key={`${pitch.pitchNumber}-${index}`}
                  className={`p-2.5 rounded-xl border text-xs ${
                    pitch.pitchNumber === lastPitch.pitchNumber
                      ? 'bg-purple-50 border-purple-300 font-bold text-purple-900'
                      : 'bg-gray-50/80 border-gray-200/80 text-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono font-bold gap-1">
                    <span>
                      {pitch.pitchNumber}구 {pitch.pitchType}
                    </span>

                    <span className="text-[11px] text-gray-500 whitespace-nowrap">
                      {pitch.speedKm > 0
                        ? `${pitch.speedKm}km`
                        : '-'}
                    </span>
                  </div>

                  <div className="text-[11px] text-gray-500 mt-0.5">
                    {pitch.result}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 하단 버튼 */}
      <div className="mt-6 pt-5 border-t border-gray-100 flex flex-col sm:flex-row items-center gap-3">
        <button
          type="button"
          onClick={() => setShowPitchDetail(!showPitchDetail)}
          disabled={!hasPitch}
          className={`w-full sm:w-auto px-5 py-3.5 rounded-2xl border font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 ${
            !hasPitch
              ? 'bg-gray-50 border-gray-100 text-gray-400 cursor-not-allowed'
              : showPitchDetail
                ? 'bg-purple-50 border-purple-300 text-purple-700 shadow-xs cursor-pointer'
                : 'border-gray-200 hover:border-gray-300 text-gray-700 hover:bg-gray-50 cursor-pointer'
          }`}
        >
          <Eye className="w-4 h-4" />
          <span>
            {showPitchDetail ? '투구 접기' : '투구 자세히'}
          </span>
        </button>

        <button
          type="button"
          onClick={onAskWhy}
          className={`w-full flex-1 py-4 px-6 rounded-2xl font-black text-base sm:text-lg flex items-center justify-center gap-2.5 transition-all duration-300 cursor-pointer shadow-lg hover:shadow-xl active:scale-[0.98] ${
            isAiExplaining
              ? 'bg-purple-700 text-white shadow-purple-700/25 ring-2 ring-purple-300'
              : 'bg-purple-600 hover:bg-purple-700 text-white shadow-purple-600/30 animate-gentle-pulse hover:scale-[1.01]'
          }`}
        >
          <span>한입만!</span>

          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md bg-white/20 ml-1">
            이 장면 쉽게 이해하기
          </span>

          <Sparkles className="w-4 h-4 ml-auto text-yellow-300 animate-pulse" />
        </button>
      </div>
    </div>
  );
}
