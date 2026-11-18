import type { RealAtBat } from '../../data/gameApi';
import { ChevronLeft, ChevronRight, Check, History } from 'lucide-react';

interface Props {
  atBats: RealAtBat[];
  selectedAtBatId: string;
  onSelectAtBat: (id: string) => void;
  onPrevAtBat: () => void;
  onNextAtBat: () => void;
  hasPrev: boolean;
  hasNext: boolean;
  awayTeam?: string;
  homeTeam?: string;
}

export function InningPlaysHistory({ atBats, selectedAtBatId, onSelectAtBat, onPrevAtBat, onNextAtBat, hasPrev, hasNext, awayTeam, homeTeam }: Props) {
  const selected = atBats.find(item => item.id === selectedAtBatId) || atBats[0];
  const innings = Array.from(new Set(atBats.map(item => item.inning))).sort((a, b) => a - b);
  const activeInning = selected?.inning ?? innings[0];
  const activeHalf = selected?.half ?? atBats.find(item => item.inning === activeInning)?.half ?? 'top';
  const availableHalves = (['top', 'bottom'] as const).filter(half =>
    atBats.some(item => item.inning === activeInning && item.half === half)
  );
  const visible = atBats.filter(item => item.inning === activeInning && item.half === activeHalf);
  const label = (item: RealAtBat) => `${item.inning}회${item.half === 'top' ? '초' : '말'} · ${item.batterTeam} 공격`;
  const outcome = (item: RealAtBat) => {
    const t = item.resultText;
    if (/볼넷|고의4구|고의사구/.test(t)) return ['볼넷', 'bg-blue-50 text-blue-700 border-blue-100'];
    if (/몸에 맞는|사구/.test(t)) return ['사구', 'bg-blue-50 text-blue-700 border-blue-100'];
    if (/안타|1루타|2루타|3루타|홈런/.test(t)) return ['안타', 'bg-emerald-50 text-emerald-700 border-emerald-100'];
    if (/실책/.test(t)) return ['실책', 'bg-amber-50 text-amber-700 border-amber-100'];
    if (/아웃|삼진|병살|뜬공|땅볼|플라이|파울플라이/.test(t)) return ['아웃', 'bg-gray-100 text-gray-600 border-gray-200'];
    return ['기록', 'bg-purple-50 text-purple-700 border-purple-100'];
  };
  const away = awayTeam || atBats.find(item => item.half === 'top')?.batterTeam || '';
  const home = homeTeam || atBats.find(item => item.half === 'bottom')?.batterTeam || '';
  return (
    <div className="w-full min-w-0 rounded-3xl border border-gray-100 bg-white p-4 sm:p-5 shadow-md shadow-purple-950/5">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
        <h3 className="flex items-center gap-2 font-black text-gray-900"><History className="h-4 w-4 text-purple-600"/>타석 기록</h3>
        <span className="text-xs font-medium text-gray-500">이닝을 선택해 기록을 살펴보세요</span>
      </div>
      {/* 1단계: 회 선택 */}
      <div className="flex gap-2 overflow-x-auto py-3" aria-label="회 선택">
        {innings.map(inning => {
          const first = atBats.find(item => item.inning === inning)!;
          const active = inning === activeInning;
          return (
            <button
              key={inning}
              type="button"
              aria-pressed={active}
              onClick={() => onSelectAtBat(first.id)}
              className={`shrink-0 rounded-xl border px-3 py-2 text-xs font-bold transition-colors ${active ? 'border-purple-600 bg-purple-600 text-white' : 'border-gray-200 bg-white text-gray-600 hover:bg-purple-50'}`}
            >
              {inning}회
            </button>
          );
        })}
      </div>
      {/* 2단계: 해당 회의 초·말 선택 (실제 기록이 있는 쪽만 표시) */}
      <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label={`${activeInning}회 초말 선택`}>
        {availableHalves.map(half => {
          const first = atBats.find(item => item.inning === activeInning && item.half === half)!;
          const active = activeHalf === half;
          const team = half === 'top' ? away : home;
          return (
            <button
              key={half}
              type="button"
              aria-pressed={active}
              onClick={() => onSelectAtBat(first.id)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-bold transition-colors ${active ? 'border-purple-300 bg-purple-50 text-purple-800' : 'border-gray-200 text-gray-500 hover:bg-gray-50'}`}
            >
              {half === 'top' ? '초' : '말'} · {team} 공격
            </button>
          );
        })}
      </div>
      {selected && <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs font-bold text-gray-700"><span>{label(selected)}</span><span className="text-gray-500">{away} {visible[0]?.stateAfter.score.away ?? '-'} : {visible[0]?.stateAfter.score.home ?? '-'} {home}</span></div>}
      <div className="max-h-[640px] overflow-y-auto space-y-1 pr-1">
        {visible.map((item, index) => {
          const [tag, tagStyle] = outcome(item);
          const picked = item.id === selectedAtBatId;
          const previous = atBats[atBats.indexOf(item) - 1];
          // 이전 타석의 종료 점수는 현재 타석 시작 점수와 같습니다.
          // 이닝 첫 타석도 직전 이닝의 마지막 타석 점수와 비교해야 득점을 놓치지 않습니다.
          const before = previous?.stateAfter.score;
          const runs = before
            ? Math.max(0, item.half === 'top'
              ? item.stateAfter.score.away - before.away
              : item.stateAfter.score.home - before.home)
            : 0;
          const description = item.resultText.startsWith(`${item.batterName}:`) ? item.resultText.slice(item.batterName.length + 1).trim() : item.resultText;
          return <button type="button" key={item.id} onClick={() => onSelectAtBat(item.id)} aria-current={picked ? 'true' : undefined} className={`w-full rounded-xl border px-3 py-3 text-left transition-all ${picked ? 'border-purple-600 bg-purple-50 ring-1 ring-purple-200' : 'border-transparent hover:border-gray-200 hover:bg-gray-50'}`}>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
              <span className="w-3 shrink-0 font-black text-purple-600">{picked ? '▶' : ''}</span>
              <span className="min-w-[48px] font-extrabold text-gray-900">{item.batterName}</span>
              <span className={`rounded-md border px-1.5 py-0.5 text-[11px] font-black ${tagStyle}`}>{tag}</span>
              <span className="min-w-0 flex-1 text-gray-600">{description}</span>
              {runs > 0 && <span className="font-black text-emerald-700">+{runs}점</span>}
              <span className="whitespace-nowrap font-bold text-gray-500">{item.pitchCountText}</span>
              <span className="whitespace-nowrap text-[10px] text-gray-500" title="타석 종료 후 아웃카운트">{Array.from({length:3}, (_,i)=><span key={i} className={i < item.outs ? 'text-purple-600' : 'text-gray-300'}>{i < item.outs ? '●' : '○'}</span>)}</span>
              {picked && <Check className="h-3.5 w-3.5 text-purple-600"/>}
            </div>
          </button>;
        })}
        {!visible.length && <p className="py-8 text-center text-sm text-gray-400">이 이닝의 타석 기록이 없어요.</p>}
      </div>
      <div className="mt-3 flex items-center justify-between gap-2 border-t border-gray-100 pt-3">
        <span className="text-[11px] text-gray-400">● 아웃 · 타석 종료 후 기준</span>
        <div className="flex gap-2"><button type="button" onClick={onPrevAtBat} disabled={!hasPrev} className="flex items-center rounded-lg border border-gray-200 px-2 py-1.5 text-xs font-bold disabled:opacity-35"><ChevronLeft className="h-4 w-4"/>이전</button><button type="button" onClick={onNextAtBat} disabled={!hasNext} className="flex items-center rounded-lg bg-purple-600 px-2 py-1.5 text-xs font-bold text-white disabled:opacity-35">다음<ChevronRight className="h-4 w-4"/></button></div>
      </div>
    </div>
  );
}
