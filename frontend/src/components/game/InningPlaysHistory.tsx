
/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import type { RealAtBat } from '../../data/gameApi';
import {
  ChevronLeft,
  ChevronRight,
  History,
  Check,
} from 'lucide-react';

interface InningPlaysHistoryProps {
  atBats: RealAtBat[];
  selectedAtBatId: string;
  onSelectAtBat: (atBatId: string) => void;
  onPrevAtBat: () => void;
  onNextAtBat: () => void;
  hasPrev: boolean;
  hasNext: boolean;
}

function getInningLabel(atBat: RealAtBat): string {
  return `${atBat.inning}회${
    atBat.half === 'top' ? '초' : '말'
  }`;
}

function formatSpeed(speed: number): string {
  return speed > 0 ? `${speed}km/h` : '구속 미기록';
}

export function InningPlaysHistory({
  atBats,
  selectedAtBatId,
  onSelectAtBat,
  onPrevAtBat,
  onNextAtBat,
  hasPrev,
  hasNext,
}: InningPlaysHistoryProps) {
  const selectedAtBat = atBats.find(
    (item) => item.id === selectedAtBatId
  );

  const headerTitle = selectedAtBat
    ? `${getInningLabel(selectedAtBat)} · ${
        selectedAtBat.batterTeam
      } 공격 타석 기록`
    : '경기 타석 기록';

  return (
    <div className="w-full bg-white rounded-3xl p-6 sm:p-7 border border-gray-100 shadow-md shadow-purple-950/5 mt-6">

      {/* 타석 기록 제목 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-100 mb-5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold">
            <History className="w-4 h-4 text-purple-600" />
          </div>

          <div>
            <h3 className="text-base sm:text-lg font-black text-gray-900 tracking-tight">
              {headerTitle}
            </h3>

            <p className="text-xs text-gray-400 mt-1">
              타석을 선택하면 해당 시점의 투구 기록과
              주자·점수 상황을 확인할 수 있어요.
            </p>
          </div>
        </div>

        {/* 이전 / 다음 타석 */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <button
            type="button"
            onClick={onPrevAtBat}
            disabled={!hasPrev}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
              hasPrev
                ? 'bg-gray-100 hover:bg-purple-100 text-gray-700 hover:text-purple-700 active:scale-95 cursor-pointer'
                : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>이전 타석</span>
          </button>

          <button
            type="button"
            onClick={onNextAtBat}
            disabled={!hasNext}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
              hasNext
                ? 'bg-purple-600 hover:bg-purple-700 text-white shadow-sm active:scale-95 cursor-pointer'
                : 'bg-gray-50 text-gray-300 cursor-not-allowed'
            }`}
          >
            <span>다음 타석</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 타석 기록 카드 */}
      {atBats.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
          {atBats.map((item) => {
            const isSelected =
              item.id === selectedAtBatId;

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelectAtBat(item.id)}
                className={`p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex flex-col justify-between relative group ${
                  isSelected
                    ? 'bg-purple-50/70 border-2 border-purple-600 ring-2 ring-purple-200/50 shadow-md shadow-purple-600/10 -translate-y-0.5'
                    : 'bg-white border-gray-200/80 hover:border-purple-300 hover:shadow-sm hover:-translate-y-0.5'
                }`}
              >
                {/* 이닝 및 선택 상태 */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[11px] font-bold text-gray-400">
                    {getInningLabel(item)} · {item.batterTeam}
                  </span>

                  {isSelected ? (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full whitespace-nowrap">
                      <Check className="w-3 h-3 stroke-[3]" />
                      조회 중
                    </span>
                  ) : (
                    <span className="text-[10px] text-gray-400 font-mono whitespace-nowrap">
                      {item.pitchCountText}
                    </span>
                  )}
                </div>

                {/* 실제 타자 */}
                <div className="text-base font-extrabold text-gray-900 group-hover:text-purple-700 transition-colors">
                  {item.batterName}
                </div>

                {/* 타석 결과 */}
                <div className="mt-1 flex items-start justify-between gap-2 text-xs font-semibold">
                  <span
                    className={`break-words ${
                      isSelected
                        ? 'text-purple-900 font-bold'
                        : 'text-gray-600'
                    }`}
                  >
                    {item.resultText}
                  </span>

                  <span className="text-gray-400 font-medium text-[11px] whitespace-nowrap">
                    {item.pitchesCount > 0
                      ? formatSpeed(
                          item.currentPitch.speedKm
                        )
                      : '기록 없음'}
                  </span>
                </div>

                {/* 투구 수 */}
                <div className="mt-3 pt-2.5 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-[11px] text-gray-400">
                    {item.pitchCountText}
                  </span>

                  <span className="text-[10px] font-semibold text-gray-400">
                    {item.outs}아웃
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="py-10 text-center text-sm text-gray-400">
          표시할 타석 기록이 없어요.
        </div>
      )}
    </div>
  );
}
